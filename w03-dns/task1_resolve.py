import argparse
import subprocess
import sys

import dns.message
import dns.query
import dns.rdatatype
import dns.flags

# Root servers. Everything starts here; there is no earlier step.
ROOT_SERVERS = [
    "198.41.0.4",       # a.root-servers.net
    "199.9.14.201",     # b.root-servers.net
    "192.33.4.12",      # c.root-servers.net
]

# (name, kind).  "stable" names must match dig exactly.  "cdn" names are served
# from many replicas and may legitimately give you a different address than dig
# got a second earlier - for those we only require that you reached an answer.
VERIFY_NAMES = [
    ("www.korea.ac.kr", "stable"),
    ("dns.google", "stable"),
    ("en.wikipedia.org", "stable"),
    ("www.stanford.edu", "stable"),
    ("www.microsoft.com", "cdn"),
]


class Resolver:
    """Your iterative resolver."""

    def resolve(self, name):

        # DNS 이름 끝에 .을 붙인다.
        # 예: www.korea.ac.kr -> www.korea.ac.kr.
        current_name = name.rstrip(".") + "."

        # 지금까지 질문한 DNS 서버들을 저장
        path = []

        # 처음에는 Root DNS 서버에서 시작
        servers = ROOT_SERVERS

        # 무한 루프 방지
        for depth in range(10):

            response = None

            # 현재 단계의 DNS 서버들을 하나씩 시도
            for server in servers:

                try:
                    # A 레코드를 요청하는 DNS query 생성
                    query = dns.message.make_query(
                        current_name,
                        dns.rdatatype.A
                    )

                    # 재귀 요청을 하지 않도록 설정
                    query.flags &= ~dns.flags.RD

                    # DNS 서버에게 직접 질문
                    response = dns.query.udp(
                        query,
                        server,
                        timeout=2
                    )

                    # 실제로 질문한 서버를 기록
                    path.append(server)

                    # 성공했으므로 서버 반복 종료
                    break

                except Exception:
                    # 이 서버가 응답하지 않으면 다음 서버 사용
                    continue

            # 모든 서버가 응답하지 않았다면 실패
            if response is None:
                raise RuntimeError(
                    f"No DNS server responded for {current_name}"
                )

            # ---------------------------------------------
            # 1. Answer section 확인
            # ---------------------------------------------

            cname_target = None

            for rrset in response.answer:

                # A 레코드를 찾았다면 최종 결과
                if rrset.rdtype == dns.rdatatype.A:

                    for rr in rrset:
                        return str(rr.address), path

                # CNAME을 찾았다면 나중에 다시 조회
                elif rrset.rdtype == dns.rdatatype.CNAME:

                    cname_target = str(rrset[0].target)

            # CNAME이 있었다면
            if cname_target is not None:

                current_name = cname_target

                # CNAME의 이름부터 다시 Root에서 시작
                servers = ROOT_SERVERS

                continue

            # ---------------------------------------------
            # 2. Authority section에서 NS 찾기
            # ---------------------------------------------

            ns_names = []

            for rrset in response.authority:

                if rrset.rdtype == dns.rdatatype.NS:

                    for rr in rrset:
                        ns_names.append(str(rr.target))

            # NS도 없다면 더 이상 진행할 수 없음
            if not ns_names:
                raise RuntimeError(
                    f"No A or NS record for {current_name}"
                )

            # ---------------------------------------------
            # 3. Additional section에서 glue A 찾기
            # ---------------------------------------------

            glue = {}

            for rrset in response.additional:

                if rrset.rdtype == dns.rdatatype.A:

                    for rr in rrset:
                        glue[str(rrset.name).rstrip(".")] = str(rr.address)

            # ---------------------------------------------
            # 4. 다음 DNS 서버의 IP 결정
            # ---------------------------------------------

            next_servers = []

            for ns_name in ns_names:

                key = ns_name.rstrip(".")

                # glue가 있으면 바로 사용
                if key in glue:
                    next_servers.append(glue[key])

            # ---------------------------------------------
            # 5. glue가 없다면 NS 이름을 직접 resolve
            # ---------------------------------------------

            if not next_servers:

                # 예:
                # ns1.example.com -> IP 주소
                ns_address, ns_path = self.resolve(ns_names[0])

                # NS 주소를 찾는 과정도 path에 기록
                path.extend(ns_path)

                next_servers.append(ns_address)

            # 다음 단계의 DNS 서버로 이동
            servers = next_servers

        # 너무 많이 반복되면 loop로 판단
        raise RuntimeError(
            f"Resolution exceeded maximum depth for {name}"
        )


# ------------------------------------------------------------------- harness
def dig_answer(name):
    """What the system resolver says, for comparison."""
    out = subprocess.run(["wsl", "dig", "+short", name, "A"],
                     capture_output=True, text=True).stdout
    return [l for l in out.split() if l and l[0].isdigit()]


def verify():
    r, failures = Resolver(), 0
    for name, kind in VERIFY_NAMES:
        try:
            addr, path = r.resolve(name)
        except NotImplementedError:
            print("Nothing implemented yet - write Resolver.resolve first.")
            return 1
        except Exception as e:
            print(f"  FAIL  {name:<22} your resolver raised {e!r}")
            failures += 1
            continue
        expected = dig_answer(name)
        if addr in expected:
            note = ""
        elif kind == "cdn":
            note = "  <- differs, but this name is CDN-hosted. Explain it."
        else:
            note = "  <- should have matched"
            failures += 1
        print(f"  {'FAIL' if note.endswith('matched') else 'ok  '}  {name:<22} "
              f"you={addr:<16} dig={','.join(expected) or '-'}   "
              f"hops={len(path)}{note}")
    print(f"\n  {len(VERIFY_NAMES) - failures}/{len(VERIFY_NAMES)} ok")
    return 1 if failures else 0


def main():
    p = argparse.ArgumentParser()
    p.add_argument("name", nargs="?", default="www.korea.ac.kr")
    p.add_argument("--verify", action="store_true")
    a = p.parse_args()

    if a.verify:
        sys.exit(verify())

    addr, path = Resolver().resolve(a.name)
    for i, server in enumerate(path, 1):
        print(f"  {i}. asked {server}")
    print(f"\n  {a.name} -> {addr}")


if __name__ == "__main__":
    main()
