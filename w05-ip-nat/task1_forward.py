#!/usr/bin/env python3
"""Week 5 · Task 1 — Subnets and longest-prefix match.

Textbook §4.3.2 (IPv4 addressing, CIDR) and §4.3.3 (forwarding).

Two things a router does with every packet: work out which prefixes the
destination falls inside, and pick the longest one. The second is the whole
of "longest prefix match", and it is the reason the internet's routing table
can hold a million entries and still be answerable.

You build both, from integers up. No `ipaddress` module - that library is
exactly the thing you are supposed to understand this week.

    python3 task1_forward.py --verify
"""
import argparse


def _parse_ipv4(address):
    """Convert dotted-decimal IPv4 address to a 32-bit integer."""
    parts = address.split(".")
    if len(parts) != 4:
        raise ValueError(f"invalid IPv4 address: {address!r}")

    value = 0
    for part in parts:
        if not part.isdigit():
            raise ValueError(f"invalid IPv4 address: {address!r}")
        octet = int(part)
        if not 0 <= octet <= 255:
            raise ValueError(f"invalid IPv4 address: {address!r}")
        value = (value << 8) | octet
    return value


def _int_to_ipv4(value):
    """Convert a 32-bit integer to dotted-decimal IPv4."""
    if not 0 <= value <= 0xFFFFFFFF:
        raise ValueError("IPv4 integer out of range")

    return ".".join(
        str((value >> shift) & 0xFF)
        for shift in (24, 16, 8, 0)
    )


def parse_cidr(cidr):
    """'163.152.6.0/24' -> (network as int, prefix length).

    Rejects prefix lengths outside 0-32 and addresses whose host bits
    are set. No ipaddress module is used.
    """
    if not isinstance(cidr, str) or "/" not in cidr:
        raise ValueError(f"invalid CIDR: {cidr!r}")

    address, prefix_text = cidr.split("/", 1)

    if not prefix_text.isdigit():
        raise ValueError(f"invalid prefix length: {prefix_text!r}")

    prefix_len = int(prefix_text)
    if not 0 <= prefix_len <= 32:
        raise ValueError(f"prefix length must be 0-32: {prefix_len}")

    address_int = _parse_ipv4(address)

    if prefix_len == 0:
        mask = 0
    else:
        mask = (0xFFFFFFFF << (32 - prefix_len)) & 0xFFFFFFFF

    network = address_int & mask

    if address_int != network:
        raise ValueError(
            f"address has host bits set: {address}/{prefix_len}"
        )

    return network, prefix_len


def network_range(cidr):
    """Return (first usable, last usable, broadcast) as IPv4 strings.

    For /31 and /32 there is no ordinary usable-host range, so this
    implementation returns (None, None, broadcast).
    """
    network, prefix_len = parse_cidr(cidr)

    host_bits = 32 - prefix_len
    size = 1 << host_bits
    broadcast = network + size - 1

    if prefix_len >= 31:
        return (None, None, _int_to_ipv4(broadcast))

    return (
        _int_to_ipv4(network + 1),
        _int_to_ipv4(broadcast - 1),
        _int_to_ipv4(broadcast),
    )


class ForwardingTable:
    """Longest-prefix-match forwarding.

    add(cidr, next_hop)  ·  lookup(address) -> next_hop or None

    The default route 0.0.0.0/0 matches everything and is the shortest prefix,
    so it must lose to any other match. If two entries have the same prefix
    length, the table is malformed - say what you do.
    """

    def __init__(self):
        # Entries are stored as (network_int, prefix_len, next_hop).
        self._routes = []

    def add(self, cidr, next_hop):
        network, prefix_len = parse_cidr(cidr)

        # Same network + prefix means equal specificity, so reject it
        # instead of silently choosing one of two different next hops.
        for old_network, old_prefix, _ in self._routes:
            if old_network == network and old_prefix == prefix_len:
                raise ValueError(f"duplicate route: {cidr}")

        self._routes.append((network, prefix_len, next_hop))

    def lookup(self, address):
        address_int = _parse_ipv4(address)

        best_hop = None
        best_prefix = -1

        for network, prefix_len, next_hop in self._routes:
            if prefix_len == 0:
                mask = 0
            else:
                mask = (0xFFFFFFFF << (32 - prefix_len)) & 0xFFFFFFFF

            if (address_int & mask) == network and prefix_len > best_prefix:
                best_prefix = prefix_len
                best_hop = next_hop

        return best_hop


# ------------------------------------------------------------------- harness
RANGE_CASES = [
    ("192.168.0.0/24",  "192.168.0.1",   "192.168.0.254",  "192.168.0.255"),
    ("10.0.0.0/8",      "10.0.0.1",      "10.255.255.254", "10.255.255.255"),
    ("172.16.32.0/20",  "172.16.32.1",   "172.16.47.254",  "172.16.47.255"),
    ("203.0.113.64/26", "203.0.113.65",  "203.0.113.126",  "203.0.113.127"),
]

TABLE = [
    ("0.0.0.0/0",       "default-gw"),
    ("10.0.0.0/8",      "campus"),
    ("10.20.0.0/16",    "eng-building"),
    ("10.20.30.0/24",   "lab-floor"),
    ("10.20.30.64/26",  "lab-rack-2"),
    ("192.168.1.0/24",  "home"),
]

LOOKUP_CASES = [
    ("10.20.30.70",   "lab-rack-2"),     # inside all four 10.x entries
    ("10.20.30.10",   "lab-floor"),
    ("10.20.99.1",    "eng-building"),
    ("10.99.0.1",     "campus"),
    ("8.8.8.8",       "default-gw"),
    ("192.168.1.77",  "home"),
]


def verify():
    fails = 0
    for cidr, first, last, bcast in RANGE_CASES:
        try:
            got = network_range(cidr)
        except NotImplementedError:
            print("  network_range is still a stub"); return 1
        except Exception as e:
            print(f"  FAIL  {cidr:<18} raised {e!r}"); fails += 1; continue
        ok = tuple(got) == (first, last, bcast)
        print(f"  {'ok  ' if ok else 'FAIL'}  {cidr:<18} {got}")
        fails += not ok

    t = ForwardingTable()
    try:
        for cidr, hop in TABLE:
            t.add(cidr, hop)
    except NotImplementedError:
        print("  ForwardingTable is still a stub"); return 1

    for addr, expect in LOOKUP_CASES:
        got = t.lookup(addr)
        ok = got == expect
        print(f"  {'ok  ' if ok else 'FAIL'}  {addr:<16} -> {got}  (want {expect})")
        fails += not ok

    print(f"\n  {len(RANGE_CASES) + len(LOOKUP_CASES) - fails}"
          f"/{len(RANGE_CASES) + len(LOOKUP_CASES)} ok")
    return 1 if fails else 0


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--verify", action="store_true")
    a = p.parse_args()
    raise SystemExit(verify() if a.verify else p.print_help())
