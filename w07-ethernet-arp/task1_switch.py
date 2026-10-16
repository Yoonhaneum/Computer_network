#!/usr/bin/env python3
"""Week 7 · Task 1 — Build a learning switch.

Textbook §6.4.3 (link-layer switches, self-learning) and §6.4.1 (MAC addresses).
"""
import argparse


class Switch:
    """A self-learning Ethernet switch."""

    BROADCAST = "ff:ff:ff:ff:ff:ff"
    AGE_SECONDS = 300

    def __init__(self, ports):
        if ports < 0:
            raise ValueError("ports must be non-negative")
        self.ports = ports
        # MAC -> (port, last_seen_time)
        self._entries = {}

    def _expire(self, now):
        """Remove entries that have been silent for AGE_SECONDS or longer."""
        expired = [
            mac for mac, (_, last_seen) in self._entries.items()
            if now - last_seen >= self.AGE_SECONDS
        ]
        for mac in expired:
            del self._entries[mac]

    def handle(self, frame, in_port):
        """Learn the source MAC, then return sorted output ports."""
        src, dst, now = frame
        if not 0 <= in_port < self.ports:
            raise ValueError("in_port is outside the switch's port range")

        self._expire(now)
        self._last_time = now

        # Learn/relearn the source on the port where this frame arrived.
        self._entries[src] = (in_port, now)

        # Never send a frame back through the port it arrived on.
        other_ports = [p for p in range(self.ports) if p != in_port]

        # Broadcast and unknown unicast destinations are flooded.
        if dst == self.BROADCAST or dst not in self._entries:
            return other_ports

        # A known destination is sent only to its learned port.
        out_port, _ = self._entries[dst]
        return [] if out_port == in_port else [out_port]

    def table(self):
        """Return {mac: port}, excluding entries that have aged out."""
        # The harness uses monotonically increasing frame times. Keep the
        # last observed time so table() can also remove expired entries.
        now = getattr(self, "_last_time", None)
        if now is not None:
            self._expire(now)
        return {mac: port for mac, (port, _) in self._entries.items()}


# ------------------------------------------------------------------- harness
A, B, C = "00:00:00:00:00:0a", "00:00:00:00:00:0b", "00:00:00:00:00:0c"
BC = Switch.BROADCAST


def verify():
    fails = 0

    def check(label, got, want):
        nonlocal fails
        ok = got == want
        print(f"  {'ok  ' if ok else 'FAIL'}  {label:<46} {got}"
              + ("" if ok else f"   want {want}"))
        fails += not ok

    try:
        s = Switch(4)
    except NotImplementedError:
        print("  Switch is still a stub")
        return 1

    check("unknown destination floods",
          s.handle((A, B, 0.0), 0), [1, 2, 3])
    check("known destination is not flooded",
          s.handle((B, A, 1.0), 2), [0])
    check("learned both",
          s.table(), {A: 0, B: 2})
    check("broadcast floods",
          s.handle((A, BC, 2.0), 0), [1, 2, 3])
    check("never back out the arrival port",
          s.handle((C, A, 3.0), 0), [])
    check("station moved, table follows",
          (s.handle((B, A, 4.0), 3), s.table()[B]), ([0], 3))
    s.handle((C, BC, 400.0), 1)
    check("aged-out entry is gone", A in s.table(), False)

    print(f"\n  {'all ok' if not fails else str(fails) + ' failed'}")
    return 1 if fails else 0


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--verify", action="store_true")
    a = p.parse_args()
    raise SystemExit(verify() if a.verify else p.print_help())