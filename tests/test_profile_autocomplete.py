import pytest

from rubberneck.services.api_client import ResourceReference
from rubberneck.services.reference_catalog import RULE, ReferenceCatalog
from rubberneck.tools.profile_autocomplete import percentile, profile_queries


class FakeClient:
    async def list_resources(self, endpoint):
        return [ResourceReference("cover", "Cover", "/rule-sections/cover")]


def test_percentile_requires_samples():
    with pytest.raises(ValueError):
        percentile([], 0.95)


def test_percentile_uses_nearest_rank_and_validates_percentage():
    assert percentile([4.0, 1.0, 3.0, 2.0], 0.50) == 2.0
    assert percentile([4.0, 1.0, 3.0, 2.0], 0.95) == 4.0
    with pytest.raises(ValueError):
        percentile([1.0], 0)
    with pytest.raises(ValueError):
        percentile([1.0], 1.01)


@pytest.mark.asyncio
async def test_profile_queries_reports_each_query_kind():
    catalog = ReferenceCatalog(FakeClient(), (RULE,))
    await catalog.load()

    profiles = profile_queries(
        catalog,
        (("exact", "cover"), ("no result", "missing")),
        iterations=10,
    )

    assert [profile.kind for profile in profiles] == ["exact", "no result"]
    assert [profile.choice_count for profile in profiles] == [1, 0]
    assert all(profile.p95_milliseconds >= 0 for profile in profiles)


@pytest.mark.asyncio
async def test_profile_queries_rejects_invalid_iteration_count():
    catalog = ReferenceCatalog(FakeClient(), (RULE,))
    await catalog.load()

    with pytest.raises(ValueError):
        profile_queries(catalog, (("exact", "cover"),), iterations=0)
