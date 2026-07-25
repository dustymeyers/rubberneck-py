"""Profile warm autocomplete lookups against the live SRD catalogs."""

from __future__ import annotations

import argparse
import asyncio
import math
from dataclasses import dataclass
from time import perf_counter

from rubberneck.services.api_client import DnDAPI
from rubberneck.services.reference_catalog import (
    ReferenceCatalog,
    ReferenceType,
)

MONSTER = ReferenceType(key="monster", label="Monster", endpoint="monsters")
DEFAULT_ITERATIONS = 10_000


@dataclass(frozen=True)
class QueryProfile:
    kind: str
    query: str
    choice_count: int
    p50_milliseconds: float
    p95_milliseconds: float
    maximum_milliseconds: float


def percentile(samples: list[float], percentage: float) -> float:
    """Return a nearest-rank percentile from a non-empty sample."""
    if not samples:
        raise ValueError("At least one timing sample is required.")
    if not 0 < percentage <= 1:
        raise ValueError("Percentage must be greater than zero and at most one.")
    ordered = sorted(samples)
    index = math.ceil(len(ordered) * percentage) - 1
    return ordered[index]


def profile_queries(
    catalog: ReferenceCatalog,
    queries: tuple[tuple[str, str], ...],
    iterations: int,
) -> list[QueryProfile]:
    """Measure already-built catalog lookups without network or index work."""
    if iterations < 1:
        raise ValueError("Iterations must be at least one.")

    profiles: list[QueryProfile] = []
    for kind, query in queries:
        samples: list[float] = []
        choices = catalog.choices(query)
        for _ in range(iterations):
            started = perf_counter()
            catalog.choices(query)
            samples.append((perf_counter() - started) * 1_000)
        profiles.append(
            QueryProfile(
                kind=kind,
                query=query,
                choice_count=len(choices),
                p50_milliseconds=percentile(samples, 0.50),
                p95_milliseconds=percentile(samples, 0.95),
                maximum_milliseconds=max(samples),
            )
        )
    return profiles


def print_report(
    name: str,
    catalog: ReferenceCatalog,
    profiles: list[QueryProfile],
) -> None:
    metrics = catalog.autocomplete_metrics
    print(f"\n{name}")
    print(
        f"entries={len(catalog.entries)} queries={metrics.query_count} "
        f"choices={metrics.choice_count} build_ms={metrics.build_milliseconds:.3f} "
        f"index_kib={metrics.index_bytes / 1024:.1f}"
    )
    print("| kind | query | choices | p50 ms | p95 ms | max ms |")
    print("| --- | --- | ---: | ---: | ---: | ---: |")
    for profile in profiles:
        query = profile.query or "(empty)"
        print(
            f"| {profile.kind} | {query} | {profile.choice_count} "
            f"| {profile.p50_milliseconds:.4f} "
            f"| {profile.p95_milliseconds:.4f} "
            f"| {profile.maximum_milliseconds:.4f} |"
        )


async def run(iterations: int) -> None:
    client = DnDAPI()
    references = ReferenceCatalog(client)
    monsters = ReferenceCatalog(client, (MONSTER,))
    await references.load()
    await monsters.load()

    print_report(
        "Rules and conditions",
        references,
        profile_queries(
            references,
            (
                ("empty", ""),
                ("exact", "cover"),
                ("prefix", "rest"),
                ("substring", "attack"),
                ("no result", "definitely-not-real"),
            ),
            iterations,
        ),
    )
    print_report(
        "Monsters",
        monsters,
        profile_queries(
            monsters,
            (
                ("empty", ""),
                ("exact", "owlbear"),
                ("prefix", "drag"),
                ("substring", "gob"),
                ("no result", "definitely-not-real"),
            ),
            iterations,
        ),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--iterations",
        type=int,
        default=DEFAULT_ITERATIONS,
        help="Warm lookups to measure for each representative query.",
    )
    arguments = parser.parse_args()
    asyncio.run(run(arguments.iterations))


if __name__ == "__main__":
    main()
