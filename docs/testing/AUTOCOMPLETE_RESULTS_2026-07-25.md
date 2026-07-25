# Discord Autocomplete Results — 2026-07-25

Source recordings: `Video Project.mp4` and `monsters.mp4`

## Recording Details

- Resolution: 1280 × 720
- Frame rate: 30 FPS
- Duration: 176.13 seconds
- Timing resolution: 33.33 milliseconds per frame
- Client: Discord desktop on Windows
- Method: frame-by-frame review

The monster recording is also 1280 × 720 at 30 FPS and runs for 72.4 seconds.

Each accepted measurement starts on the first frame containing the completed
query, or the first loading frame for an empty query, and ends on the first
frame containing the settled suggestion list.

## Valid Measurements

| Trial | Query | Start | Settled | Frames | Visible latency | Correct? |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| Empty 1 | `(empty)` | 3.400 s | 3.867 s | 14 | 467 ms | Yes |
| Empty 2 | `(empty)` | 8.367 s | 9.200 s | 25 | 833 ms | Yes |
| Empty 3 | `(empty)` | 26.200 s | 27.100 s | 27 | 900 ms | Yes |
| Empty 4 | `(empty)` | 34.033 s | 34.833 s | 24 | 800 ms | Yes |
| Exact | `cover` | 68.867 s | 69.633 s | 23 | 767 ms | Yes — Cover |
| Prefix | `co` | 79.133 s | 80.567 s | 43 | 1,433 ms | Yes — Cover and related entries |
| Prefix | `cov` | 89.033 s | 89.533 s | 15 | 500 ms | Yes — Cover and related entries |
| Substring | `mak` | 126.567 s | 127.867 s | 39 | 1,300 ms | Yes — matching rule entries |

The median of the four repeatable empty-query samples is **817 ms**. All valid
samples are below the suite's 2,000 ms investigation threshold. The slowest
valid sample is **1,433 ms**.

## Monster Measurements

| Trial | Query | Approx. start | Approx. settled | Visible latency | Correct? |
| --- | --- | ---: | ---: | ---: | --- |
| Empty 1 | `(empty)` | 0.9 s | 1.2 s | 300 ms | Yes |
| Empty 2 | `(empty)` | 13.5 s | 13.7 s | 200 ms | Yes |
| Empty 3 | `(empty)` | 56.6 s | 56.9 s | 300 ms | Yes |
| Exact | `owlbear` | 25.1 s | 26.3 s | 1,200 ms | Yes — Owlbear |
| Prefix | `drag` | 33.0 s | 34.1 s | 1,100 ms | Yes — dragon entries |
| Substring | `gob` | 50.3 s | 50.8 s | 500 ms | Yes — Goblin and Hobgoblin |
| No result | `definitely no` | 61.2 s | 62.3 s | 1,100 ms | Yes — no options |

The monster samples range from approximately **200–1,200 ms**. All five query
shapes return the expected result state and remain below the 2,000 ms
investigation threshold.

## Recording Limitations

The two recordings cover both catalogs and collectively include every
representative query shape, but they are not a strict execution of every query
and repetition in the fixed suite:

- The rules recording substitutes `co`, `cov`, and `mak` for some fixed queries.
- The monster no-result query is `definitely no`, rather than
  `definitely-not-real`; both exercise the same no-result path.
- Several attempts include command syntax such as `term` in the option value,
  are cancelled, or continue into command submission and navigation. Those
  frames are excluded.
- Only the empty-query cases have enough clean repetitions for a warm median.
- The recording does not begin immediately after a demonstrated bot restart,
  so the first sample is not labeled as a verified cold-client result.

## Conclusion

Observed rules and monster autocomplete is correct and remains below two
seconds. The local callback baseline is below 5 ms p95, while the recordings
show approximately 200–1,433 ms of client-visible delay. This rules out catalog
lookup work as the dominant cost, but it does not isolate client debounce,
network transit, Discord processing, or list rendering from one another.

This closes the Block 4 measurement requirement. A future regression run should
follow the fixed suite exactly and include a demonstrated bot restart when
cold-versus-warm comparisons are needed.
