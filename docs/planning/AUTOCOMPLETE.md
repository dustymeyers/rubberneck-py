# Autocomplete Performance

Discord autocomplete has two independently observable latency components:

1. The local callback, which normalizes the query and reads a precomputed index.
2. Discord client debounce and network round trips, which the bot cannot control.

The catalog logs its index construction time, indexed query count, and estimated
owned memory at startup. The warm local callback target is a 95th percentile
below 5 milliseconds. The test suite measures that target over 1,000 lookups.

The index is built once when references load. It incrementally records exact,
prefix, and substring candidates instead of rescanning the entire catalog for
every indexed query. Each keystroke performs one dictionary lookup and copies at
most Discord's 25 allowed choices; it makes no API or Redis calls.

When autocomplete still feels delayed but the local test and startup metrics
are healthy, the remaining delay is normally Discord's client-side debounce or
the network path. That portion cannot be measured from inside the callback.

## Reproducible Profile

Run the live-catalog profiler from the repository root:

```shell
python -m rubberneck.tools.profile_autocomplete --iterations 10000
```

The tool fetches each catalog once, builds its local index, then measures warm
dictionary lookups. It does not include API loading time in query latency.

### 2026-07-25 Baseline

Environment: Windows, Python 3.12.4, 10,000 warm lookups per query shape.

| Catalog | Entries | Queries | Build | Estimated memory |
| --- | ---: | ---: | ---: | ---: |
| Rules and conditions | 48 | 8,566 | 31.064 ms | 3,419.9 KiB |
| Monsters | 334 | 27,492 | 88.707 ms | 14,240.8 KiB |

| Catalog | Query shape | Example | Choices | p50 | p95 | Maximum |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| References | Empty | `(empty)` | 25 | 0.0003 ms | 0.0006 ms | 0.0185 ms |
| References | Exact | `cover` | 1 | 0.0003 ms | 0.0004 ms | 0.0520 ms |
| References | Prefix | `rest` | 2 | 0.0003 ms | 0.0004 ms | 0.0961 ms |
| References | Substring | `attack` | 1 | 0.0003 ms | 0.0004 ms | 0.0064 ms |
| References | No result | `definitely-not-real` | 0 | 0.0003 ms | 0.0005 ms | 0.0603 ms |
| Monsters | Empty | `(empty)` | 25 | 0.0003 ms | 0.0004 ms | 0.0151 ms |
| Monsters | Exact | `owlbear` | 1 | 0.0003 ms | 0.0004 ms | 0.1614 ms |
| Monsters | Prefix | `drag` | 25 | 0.0004 ms | 0.0004 ms | 0.0096 ms |
| Monsters | Substring | `gob` | 2 | 0.0003 ms | 0.0005 ms | 0.0260 ms |
| Monsters | No result | `definitely-not-real` | 0 | 0.0003 ms | 0.0004 ms | 0.0050 ms |

The warm p95 is far below the 5 ms target for every representative query. The
current index is retained because its roughly 17.3 MiB combined footprint and
sub-120 ms construction time are acceptable at today's catalog size. Revisit
the representation before registering enough new catalogs to make memory scale
materially beyond this baseline.
