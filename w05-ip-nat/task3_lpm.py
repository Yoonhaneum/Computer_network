#!/usr/bin/env python3
"""Week 5 · Task 3 — Make longest-prefix match fast.

Textbook §4.3.3.

`LinearTable` is correct and it is what you probably wrote in Task 1: keep the
prefixes in a list, check every one, remember the longest that matched. On six
entries that is fine. A real router holds close to a million, and it has to
answer while the packet is still in the buffer.

Beat it:

    python3 bench.py
    python3 bench.py --yours

Correctness first: `bench.py` checks every one of your answers against the
linear table. A fast router that forwards to the wrong next hop is not a
router, it is an outage.
"""


class LinearTable:
    """Correct, and slow in the obvious way."""

    def __init__(self):
        self.entries = []

    def add(self, network, prefix_len, next_hop):
        self.entries.append((prefix_len, network, next_hop))

    def lookup(self, address):
        best = None

        for plen, net, hop in self.entries:
            mask = (0xFFFFFFFF << (32 - plen)) & 0xFFFFFFFF

            if address & mask == net and (
                best is None or plen > best[0]
            ):
                best = (plen, hop)

        return best[1] if best else None
class YourTable:
    """Fast longest-prefix match using prefix-length buckets."""

    def __init__(self):
        # 33 dictionaries for prefix lengths /0 through /32.
        # Each dictionary maps a network address to its next hop.
        self.tables = [{} for _ in range(33)]

    def add(self, network, prefix_len, next_hop):
        # Store the route in the bucket for its prefix length.
        # setdefault preserves the first route if a duplicate exists,
        # matching LinearTable's behavior.
        self.tables[prefix_len].setdefault(network, next_hop)

    def lookup(self, address):
        # Check the longest prefixes first.
        for prefix_len in range(32, -1, -1):
            mask = (0xFFFFFFFF << (32 - prefix_len)) & 0xFFFFFFFF
            network = address & mask

            # A dictionary lookup is fast on average.
            if network in self.tables[prefix_len]:
                return self.tables[prefix_len][network]

        # No matching route.
        return None
