# Manual Discord Autocomplete Benchmark

Use this suite to measure the delay a player actually sees in Discord. It
complements the local profiler; it does not replace it.

## What Is Being Measured

Measure from the final query keystroke until the autocomplete choices stop
changing and are readable. This includes Discord client debounce, network
latency, command routing, and the bot callback.

For the most repeatable measurement, record the Discord window at 60 frames per
second and count frames between those two events:

1. The final character appears in the command option.
2. The suggestion list reaches its final visible state.

Convert frames to milliseconds with:

```text
milliseconds = frames / 60 * 1000
```

A stopwatch is acceptable when screen recording is unavailable, but note that
method in the results because reaction time adds noise.

## Prerequisites

- Start the bot and wait for both catalog-loaded messages in its log.
- Use the same Discord desktop client, network, server, and channel for one run.
- Close Discord's command composer before every case.
- Do not paste text. Type the query normally and stop after the final character.
- Record the client version, connection type, date, and approximate ping.
- Run the local baseline once:

```powershell
.\env\Scripts\python.exe -m rubberneck.tools.profile_autocomplete --iterations 10000
```

## Test Procedure

Run the entire table once immediately after restarting the bot. Label that
pass `cold client`. Without restarting the bot or Discord, repeat every case
three times and label those passes `warm 1`, `warm 2`, and `warm 3`.

For each case:

1. Open the slash command and focus the named option.
2. Type the exact query shown.
3. Measure until the final suggestion list is visible.
4. Record the elapsed time, number of visible choices, and whether a relevant
   expected choice appeared.
5. Press `Esc` and wait at least two seconds before the next case.

| ID | Command option | Shape | Query | Expected example |
| --- | --- | --- | --- | --- |
| R1 | `/rules lookup term` | Empty | `(empty)` | Up to 25 references |
| R2 | `/rules lookup term` | Exact | `cover` | Cover |
| R3 | `/rules lookup term` | Prefix | `rest` | Resting or Restrained |
| R4 | `/rules lookup term` | Substring | `attack` | Making an Attack |
| R5 | `/rules lookup term` | No result | `definitely-not-real` | No choices |
| M1 | `/monster name` | Empty | `(empty)` | Up to 25 monsters |
| M2 | `/monster name` | Exact | `owlbear` | Owlbear |
| M3 | `/monster name` | Prefix | `drag` | Dragon entries |
| M4 | `/monster name` | Substring | `gob` | Goblin or Hobgoblin |
| M5 | `/monster name` | No result | `definitely-not-real` | No choices |

For an empty-query case, start timing when the focused empty option first
requests suggestions rather than after a keystroke.

## Results Worksheet

Copy this table for each environment. Enter elapsed milliseconds or `N/A` when
the list never settles.

| ID | Cold client | Warm 1 | Warm 2 | Warm 3 | Choices correct? | Notes |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| R1 |  |  |  |  |  |  |
| R2 |  |  |  |  |  |  |
| R3 |  |  |  |  |  |  |
| R4 |  |  |  |  |  |  |
| R5 |  |  |  |  |  |  |
| M1 |  |  |  |  |  |  |
| M2 |  |  |  |  |  |  |
| M3 |  |  |  |  |  |  |
| M4 |  |  |  |  |  |  |
| M5 |  |  |  |  |  |  |

Environment:

```text
Date/time:
Discord client/version:
Operating system:
Connection (wired/Wi-Fi):
Approximate Discord ping:
Measurement method (60 fps recording/stopwatch):
Bot commit:
```

## Evaluation

The run passes correctness when every expected-result case contains a relevant
choice and both no-result cases show no choices.

Report latency separately from correctness:

- Calculate the median of `warm 1` through `warm 3` for each case.
- Report the slowest warm median for references and for monsters.
- Flag any warm sample above 2,000 ms, any missing expected choice, or any list
  that never settles.
- Compare visible medians with the local profiler's p95. When local p95 remains
  below 5 ms but visible latency is materially higher, record that catalog
  lookup is not the dominant cost. Do not assign the remainder to client
  debounce, network transit, Discord processing, or rendering without separate
  instrumentation.

Do not average the cold-client pass into the warm result. Preserve it as a
separate observation so startup or first-interaction behavior remains visible.
