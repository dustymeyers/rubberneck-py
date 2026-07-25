# Autocomplete Performance

Discord autocomplete has two independently observable latency components:

1. The local callback, which normalizes the query and reads a precomputed index.
2. Discord client debounce and network round trips, which the bot cannot control.

The catalog logs its index construction time and indexed query count at startup.
The warm local callback target is a 95th percentile below 5 milliseconds. The
test suite measures that target over 1,000 lookups.

The index is built once when references load. It incrementally records exact,
prefix, and substring candidates instead of rescanning the entire catalog for
every indexed query. Each keystroke performs one dictionary lookup and copies at
most Discord's 25 allowed choices; it makes no API or Redis calls.

When autocomplete still feels delayed but the local test and startup metrics
are healthy, the remaining delay is normally Discord's client-side debounce or
the network path. That portion cannot be measured from inside the callback.
