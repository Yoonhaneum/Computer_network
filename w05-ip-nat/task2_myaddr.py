#!/usr/bin/env python3
"""Week 5 · Task 2 — Where exactly are you on the internet?

Collect local network information on two networks and save the raw results.
The report is generated as a template so the student can fill in the
network/subnet/NAT/DHCP observations from the captured data.
"""

import argparse
import json
import os
import platform
import subprocess


HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")


def sh(*cmd):
    """Run a command and return its stdout; keep failures visible."""
    try:
        result = subprocess.run(
    cmd,
    capture_output=True,
    text=True,
    encoding="cp949",
    errors="replace",
    timeout=15,
)
        if result.stdout:
            return result.stdout
        if result.stderr:
            return f"<command failed: {result.stderr.strip()}>"
        return ""
    except Exception as e:
        return f"<failed: {e}>"


def local_facts():
    """Collect raw OS/network information.

    The script deliberately keeps this output raw. Network/subnet analysis
    is intended to be done by reading the collected information.
    """
    osname = platform.system()

    if osname == "Darwin":
        return {
            "os": osname,
            "ifconfig": sh("ifconfig"),
            "route": sh("route", "-n", "get", "default"),
            "dns": sh("scutil", "--dns"),
        }

    if osname == "Linux":
        return {
            "os": osname,
            "ip_addr": sh("ip", "addr"),
            "ip_route": sh("ip", "route"),
            "dns": sh("cat", "/etc/resolv.conf"),
        }

    # Windows
    return {
        "os": osname,
        "ipconfig": sh("ipconfig", "/all"),
        "route": sh("route", "print"),
    }


def public_address():
    """Ask an external service what public IPv4 address it sees."""
    out = sh(
        "curl",
        "-s",
        "--max-time",
        "10",
        "https://api.ipify.org",
    )
    value = out.strip()
    return value if value and not value.startswith("<") else None


def collect(label):
    """Collect one network observation and append it to addresses.json."""
    if not label or not label.strip():
        raise ValueError("label must not be empty")

    os.makedirs(OUT, exist_ok=True)

    record = {
        "label": label.strip(),
        "local": local_facts(),
        "public": public_address(),
    }

    path = os.path.join(OUT, "addresses.json")

    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                all_records = json.load(f)
        except (json.JSONDecodeError, OSError):
            all_records = []
    else:
        all_records = []

    if not isinstance(all_records, list):
        all_records = []

    all_records.append(record)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(all_records, f, indent=2, ensure_ascii=False)

    print(f"  public address seen from outside: {record['public']}")
    print(f"  -> out/addresses.json  ({len(all_records)} record(s))")
    print("\n  Now read the raw output yourself and answer the questions in task2.md.")
    print("  The script deliberately does not parse the network configuration for you.")


def report():
    """Generate a report template from the collected observations.

    The actual subnet, gateway, NAT, and DHCP conclusions are intentionally
    left for the student to determine from the raw network information.
    """
    path = os.path.join(OUT, "addresses.json")

    if not os.path.exists(path):
        raise FileNotFoundError(
            "out/addresses.json not found. Run --collect on your networks first."
        )

    with open(path, "r", encoding="utf-8") as f:
        records = json.load(f)

    if not records:
        raise ValueError("out/addresses.json contains no observations.")

    os.makedirs(OUT, exist_ok=True)
    report_path = os.path.join(OUT, "report.md")

    lines = [
        "# Week 5 · Task 2 — Address Study",
        "",
        "## 1. Collected networks",
        "",
    ]

    for i, record in enumerate(records, start=1):
        lines.extend([
            f"### Network {i}: {record.get('label', '(no label)')}",
            "",
            f"- Public address seen from outside: `{record.get('public')}`",
            "- Local IP address: **fill in from the raw output below**",
            "- Subnet mask/prefix: **fill in**",
            "- Network range: **fill in**",
            "- Default gateway: **fill in**",
            "- Is the gateway inside the local subnet?: **fill in**",
            "- Private/public local address: **fill in**",
            "- NAT evidence/layers: **fill in**",
            "",
        ])

    lines.extend([
        "## 2. Comparison between the two networks",
        "",
        "| Item | Network 1 | Network 2 |",
        "|---|---|---|",
        "| Private IP | fill in | fill in |",
        "| Subnet mask/prefix | fill in | fill in |",
        "| Default gateway | fill in | fill in |",
        "| Public IP | fill in | fill in |",
        "| Private/public address changed? | fill in | fill in |",
        "",
        "## 3. DHCP observation",
        "",
        "- Wireshark filter: `port 67 or port 68`",
        "- Discover source: **fill in**",
        "- Discover destination: **fill in**",
        "- DHCP sequence (DORA): Discover → Offer → Request → ACK",
        "- Lease time: **fill in from DHCP ACK/Offer**",
        "- Why Discover is broadcast: **fill in**",
        "- Why ACK may not be broadcast: **fill in**",
        "",
        "## 4. NAT observation",
        "",
        "- Evidence of NAT: **fill in**",
        "- Number/layers of NAT inferred from the two networks: **fill in**",
        "",
        "## 5. Raw collected information",
        "",
    ])

    for i, record in enumerate(records, start=1):
        lines.extend([
            f"### Raw output — Network {i}: {record.get('label', '(no label)')}",
            "",
            "```json",
            json.dumps(record.get("local", {}), indent=2, ensure_ascii=False),
            "```",
            "",
        ])

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"  -> {report_path}")
    print("  Fill in the marked analysis fields using the raw network output and Wireshark DHCP capture.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--collect",
        metavar="LABEL",
        help='collect information for a network, e.g. "campus wifi"',
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="generate out/report.md from collected observations",
    )
    args = parser.parse_args()

    if args.collect:
        collect(args.collect)
    elif args.report:
        report()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
