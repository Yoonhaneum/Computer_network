#!/usr/bin/env python3
"""Week 3 · Task 2 — Does DNS actually steer you? Measure it.

Textbook §2.4.3 (records) and §2.5 (CDNs).

The lecture claims two things:

    (a) most large sites are served by a CDN, reached through a CNAME chain
    (b) DNS steers each user to a *nearby* replica

Both are testable from your laptop, and one of them is harder to prove than
the slide makes it look. Your job is to produce the evidence and a number.

    python3 task2_steering.py --collect        # gather the raw data
    python3 task2_steering.py --report         # your analysis

What you have to build
----------------------
1.  For each hostname in SITES, follow the CNAME chain to its end and record
    every hop. `--collect` should leave the raw data in out/chains.json.

2.  Decide, for each site, whether it is served by a **third party**.
    This is the hard part and there is no single right answer:

      - `www.microsoft.com` ends at `akamaiedge.net`     - clearly third party
      - `www.netflix.com`   stops inside `netflix.com`   - own CDN, not third party
      - some sites have no CNAME at all and still sit behind a CDN (anycast)
      - `foo.cloudfront.net` and `foo.s3.amazonaws.com` are both Amazon,
        but they are not the same service

    Write down the rule you used and **defend it in observation.md**. A rule
    that just compares the last two labels will be wrong on at least one of
    the sites below; find which, and say so.

3.  Ask **two different resolvers** for the same name and compare the
    addresses you get back. If DNS really steers by location, a CDN-hosted
    name should answer differently to resolvers sitting in different places.

        RESOLVERS below has your system resolver and two public ones.

    Report: of N CDN-hosted sites, how many returned a different address set
    from a different resolver? Claim (b) predicts most of them. Check it.

Pass condition
--------------
There is no fixed answer. You pass by producing, in out/report.md:

  - the table: site | chain length | final zone | third party? | your rule's verdict
  - the steering number: "X of N sites answered differently to a different resolver"
  - at least one site where your classification rule was wrong, and why
"""
import argparse, json, os, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")

SITES = [
    "www.microsoft.com",     # Akamai, multi-hop
    "www.netflix.com",       # own CDN
    "www.adobe.com",
    "www.cnn.com",
    "www.apple.com",
    "www.korea.ac.kr",       # no CDN at all
    "www.stanford.edu",
    "www.bbc.co.uk",
    "www.spotify.com",
    "www.github.com",
    "www.wikipedia.org",
    "www.nytimes.com",
]

RESOLVERS = {
    "system": None,          # whatever is in your resolv.conf
    "google": "8.8.8.8",
    "quad9":  "9.9.9.9",
}


def dig(name, rtype="A", server=None):
    args = ["wsl", "dig", "+short", name, rtype]

    if server:
        args.insert(3, f"@{server}")

    out = subprocess.run(
        args,
        capture_output=True,
        text=True
    ).stdout

    return [
        l.strip()
        for l in out.splitlines()
        if l.strip()
    ]


def collect():
    """Gather raw chains and per-resolver answers into out/chains.json."""
    data = {}

    for site in SITES:
        print(f"collecting {site}...")

        current = site
        chain = []
        seen = set()

        # CNAME chain 따라가기
        for _ in range(10):
            if current in seen:
                break

            seen.add(current)

            cnames = dig(current, "CNAME")

            if not cnames:
                break

            target = cnames[0].rstrip(".")

            chain.append({
                "from": current,
                "to": target
            })

            current = target

        # 각 resolver에서 A record 조회
        answers = {}

        for resolver_name, resolver_ip in RESOLVERS.items():
            records = dig(site, "A", resolver_ip)

            addresses = []

            for record in records:
                if record and record[0].isdigit():
                    addresses.append(record)

            answers[resolver_name] = addresses

        data[site] = {
            "chain": chain,
            "final": current,
            "answers": answers
        }

    path = os.path.join(OUT, "chains.json")

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print(f"\nSaved: {path}")

def registrable_domain(name):
    name = name.rstrip(".").lower()
    parts = name.split(".")

    if len(parts) >= 3 and parts[-2:] in [
        ["co", "uk"],
        ["ac", "kr"],
    ]:
        return ".".join(parts[-3:])

    if len(parts) >= 2:
        return ".".join(parts[-2:])

    return name


def is_third_party(site, final):
    site_base = registrable_domain(site)
    final_base = registrable_domain(final)

    return site_base != final_base

def different_answers(answers):
    normalized = {
        resolver: tuple(sorted(addresses))
        for resolver, addresses in answers.items()
    }

    return len(set(normalized.values())) > 1


def report():
    """Read out/chains.json and produce out/report.md."""
    path = os.path.join(OUT, "chains.json")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    rows = []
    steering_count = 0

    for site, info in data.items():
        chain = info["chain"]
        final = info["final"]
        answers = info["answers"]

        # CNAME의 최종 이름을 기준으로 third-party 여부 판정
        third_party = is_third_party(site, final)

        # 서로 다른 resolver가 다른 A record를 반환했는지 확인
        different = different_answers(answers)

        if different:
            steering_count += 1

        rows.append({
            "site": site,
            "chain_length": len(chain),
            "final": final,
            "third_party": third_party,
            "different": different
        })

    report_path = os.path.join(OUT, "report.md")

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Task 2 Report\n\n")

        # --------------------------------------------------
        # Classification rule
        # --------------------------------------------------
        f.write("## Classification rule\n\n")
        f.write(
            "A site is classified as third-party when the final name "
            "in its CNAME chain belongs to a different registrable domain "
            "from the original site. A CNAME that remains inside the "
            "site's own domain is not classified as third-party.\n\n"
        )

        # --------------------------------------------------
        # CNAME chain table
        # --------------------------------------------------
        f.write("## CNAME chains and classification\n\n")

        f.write(
            "| site | chain length | final zone | "
            "third party? | your rule's verdict |\n"
        )
        f.write(
            "|---|---:|---|---|---|\n"
        )

        for row in rows:
            if row["third_party"]:
                verdict = "third-party"
            else:
                verdict = "not third-party"

            f.write(
                f"| {row['site']} | "
                f"{row['chain_length']} | "
                f"{row['final']} | "
                f"{'yes' if row['third_party'] else 'no'} | "
                f"{verdict} |\n"
            )

        f.write("\n")

        # --------------------------------------------------
        # Steering result
        # --------------------------------------------------
        f.write("## Steering result\n\n")

        f.write(
            f"**{steering_count} of {len(data)} sites answered "
            f"differently to a different resolver.**\n\n"
        )

        f.write(
            "The result compares the A records returned by the system, "
            "Google, and Quad9 resolvers. A difference in returned "
            "addresses shows that resolver choice affected the DNS "
            "answer, but it does not by itself prove that the resolver "
            "selected a physically nearby replica.\n\n"
        )

        # --------------------------------------------------
        # Classification rule limitation
        # --------------------------------------------------
        f.write("## Limitation of the classification rule\n\n")

        f.write(
            "The classification rule uses the final CNAME's registrable "
            "domain to decide whether a site is on a third-party CDN. "
            "This is only a heuristic: a different registrable domain "
            "does not by itself prove who operates the CDN or whether "
            "the CDN is actually a third-party service.\n\n"
        )

        f.write(
            "For example, www.stanford.edu ends at "
            "`stanford.netlifyglobalcdn.com`. The rule classifies this "
            "as third-party because the final registrable domain differs "
            "from `stanford.edu`. However, the CNAME chain alone does not "
            "provide enough information to establish the ownership or "
            "exact operational relationship of that CDN. This shows why "
            "the rule should be treated as a heuristic rather than a "
            "definitive CDN ownership test.\n\n"
        )

        # --------------------------------------------------
        # Raw resolver observations
        # --------------------------------------------------
        f.write("## Resolver observations\n\n")

        for row in rows:
            site = row["site"]
            answers = data[site]["answers"]

            f.write(f"### {site}\n\n")

            for resolver, addresses in answers.items():
                if addresses:
                    f.write(
                        f"- {resolver}: "
                        f"{', '.join(addresses)}\n"
                    )
                else:
                    f.write(
                        f"- {resolver}: no A record\n"
                    )

            f.write("\n")

    print(f"Saved: {report_path}")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--collect", action="store_true")
    p.add_argument("--report", action="store_true")
    a = p.parse_args()
    os.makedirs(OUT, exist_ok=True)
    if a.collect:
        collect()
    elif a.report:
        report()
    else:
        p.print_help()
