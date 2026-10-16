#!/usr/bin/env python3
"""Week 7 · Task 3 — A switch that runs out of room.

Textbook §6.4.3.

A switch does not have room for every station on the network. Its forwarding
table sits in a fixed amount of fast memory, and when that fills, something has
to go. Whatever goes gets **flooded** the next time anyone sends to it - out of
every port, to every station that did not ask for it.

`NaiveSwitch` handles a full table the simplest way: throw out whichever entry
has been there longest. That is a perfectly reasonable first idea and it is
close to the worst thing you can do with this traffic.

    python3 bench.py
    python3 bench.py --yours

Correctness first: every frame whose destination is reachable must still reach
it. A switch that floods less because it delivers less is not a switch.
"""
from collections import OrderedDict


class NaiveSwitch:
    """Correct. Evicts the oldest entry, which is not the least useful one."""

    BROADCAST = "ff:ff:ff:ff:ff:ff"

    def __init__(self, ports, capacity):
        self.ports = ports
        self.capacity = capacity
        self.table = OrderedDict()                 # mac -> port, insertion order

    def handle(self, frame, in_port):
        src, dst, now = frame
        if src not in self.table and len(self.table) >= self.capacity:
            self.table.popitem(last=False)         # throw out the oldest arrival
        self.table[src] = in_port

        if dst == self.BROADCAST or dst not in self.table:
            return [p for p in range(self.ports) if p != in_port]
        out = self.table[dst]
        return [] if out == in_port else [out]


class YourSwitch:
    """A learning switch that evicts the least-used table entry."""

    BROADCAST = "ff:ff:ff:ff:ff:ff"

    def __init__(self, ports, capacity):
        self.ports = ports
        self.capacity = capacity

        # MAC address -> output port
        self.table = {}

        # MAC address -> number of times it was seen while learned
        self.usage = {}

        # MAC address -> most recent time it was seen
        self.last_seen = {}

    def handle(self, frame, in_port):
        src, dst, now = frame

        # Learn the source MAC address.
        if src in self.table:
            self.usage[src] += 1
            self.last_seen[src] = now
            self.table[src] = in_port
        elif self.capacity > 0:
            # If the table is full, evict the least-used entry.
            if len(self.table) >= self.capacity:
                victim = min(
                    self.table,
                    key=lambda mac: (
                        self.usage[mac],
                        self.last_seen[mac]
                    )
                )

                del self.table[victim]
                del self.usage[victim]
                del self.last_seen[victim]

            self.table[src] = in_port
            self.usage[src] = 1
            self.last_seen[src] = now

        # Broadcast and unknown destinations must be flooded.
        if dst == self.BROADCAST or dst not in self.table:
            return [
                port for port in range(self.ports)
                if port != in_port
            ]

        # A known destination receives the frame on its learned port.
        out_port = self.table[dst]

        # Never send the frame back through its incoming port.
        if out_port == in_port:
            return []

        return [out_port]
