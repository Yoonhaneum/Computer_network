#!/usr/bin/env python3
"""Week 6 · Task 1 — Link state: build the forwarding table yourself.

Textbook §5.2 (link state and distance vector) and §5.3 (OSPF).

Every OSPF router ends up holding the same map of the network, and then each one
computes, alone, where to send a packet for every destination. The computation is
Dijkstra; the output is a forwarding table with **one next hop per destination**,
not a path.

That last part is what makes routing work without anybody carrying a route around
in the packet. Build it.

    python3 task1_linkstate.py --verify
"""
import argparse

# Undirected weighted graph: node -> {neighbour: cost}
TOPOLOGY = {
    "u": {"v": 2, "w": 5, "x": 1},
    "v": {"u": 2, "w": 3, "x": 2},
    "w": {"u": 5, "v": 3, "x": 3, "y": 1, "z": 5},
    "x": {"u": 1, "v": 2, "w": 3, "y": 1},
    "y": {"w": 1, "x": 1, "z": 2},
    "z": {"w": 5, "y": 2},
}


def dijkstra(graph, source):
     import heapq

     dist = {source: 0} #거리를 저장할 맵
     pq = [(0, source)] #우선순위 queue에 거리를 저장해두고 나중에 오름차순으로 dict에 저장함

     while pq: #pq에 처리할 노드가 없을때까지, 처음엔 (0,source)처리
        current_cost, current = heapq.heappop(pq) #pq에서 비용 가장 낮은 노드 꺼냄 current_cost = 비용, current = 노드 저장

        if current_cost != dist[current]: #지금의 정보가 더 좋은지 확인
            continue

        for neighbor, edge_cost in graph[current].items(): #현재 처리하는 노드의 이웃 전부 확인 neighbor = 노드, edge_cost = 비용 저장
            new_cost = current_cost + edge_cost #현재까지 오는 비용에 다음 경로 비용 더하기

            if neighbor not in dist or new_cost < dist[neighbor]: #새로운 경로거나 비용이 현재보다 적은 new_cost라면 dist에 저장
                dist[neighbor] = new_cost
                heapq.heappush(pq, (new_cost, neighbor))

     dist.pop(source, None) #시작점은 제외하기
     return dist #시작점에서의 거리를 나타낸 딕셔너리 반환
     raise NotImplementedError("implement Dijkstra")


def forwarding_table(graph, source): 
    """What the router at `source` actually installs.

    Return {destination: first_hop}, where first_hop is a direct neighbour
    of `source`.
    """
    import heapq

    dist = {source: 0} #맵 형식
    pq = [(0, source)]
    first_hop = {} #목적지로 가기 위해 처음으로 갈 라우터, 
                   #u > x > w 라면 first_hop{"w"} = u
    

    while pq:
        current_cost, current = heapq.heappop(pq) #비용, 노드를 current_cost, current에 저장

        if current_cost != dist[current]: #비용이 현재 dist와 다르면 
            continue

        for neighbor, edge_cost in graph[current].items():
            new_cost = current_cost + edge_cost

            if neighbor not in dist or new_cost < dist[neighbor]:
                dist[neighbor] = new_cost

                if current == source: #시작점에서 직접 연결된 경우
                    first_hop[neighbor] = neighbor
                else: #그렇지 않은 경우 처음 만나는 노드
                    first_hop[neighbor] = first_hop[current]

                heapq.heappush(pq, (new_cost, neighbor))

    return first_hop


def link_down(graph, a, b):
    """A copy of `graph` with the link a-b removed, in both directions."""
    g = {n: dict(e) for n, e in graph.items()}
    g[a].pop(b, None)
    g[b].pop(a, None)
    return g


# ------------------------------------------------------------------- harness
# Costs from the textbook's worked example, §5.2.1
EXPECTED_COST_U = {"v": 2, "w": 3, "x": 1, "y": 2, "z": 4}
EXPECTED_TABLE_U = {"v": "v", "w": "x", "x": "x", "y": "x", "z": "x"}


def verify():
    fails = 0
    try:
        cost = dijkstra(TOPOLOGY, "u")
    except NotImplementedError:
        print("  dijkstra is still a stub"); return 1
    ok = cost == EXPECTED_COST_U
    print(f"  {'ok  ' if ok else 'FAIL'}  costs from u: {cost}")
    if not ok:
        print(f"        expected {EXPECTED_COST_U}")
    fails += not ok

    try:
        table = forwarding_table(TOPOLOGY, "u")  #u에서 시작, 
    except NotImplementedError:
        print("  forwarding_table is still a stub"); return 1
    ok = table == EXPECTED_TABLE_U
    print(f"  {'ok  ' if ok else 'FAIL'}  table at u:  {table}")
    if not ok:
        print(f"        expected {EXPECTED_TABLE_U}")
    fails += not ok

    # every node should be able to reach every other
    for n in TOPOLOGY:
        t = forwarding_table(TOPOLOGY, n)
        missing = set(TOPOLOGY) - {n} - set(t)
        bad = [d for d, h in t.items() if h not in TOPOLOGY[n]]
        ok = not missing and not bad
        print(f"  {'ok  ' if ok else 'FAIL'}  table at {n} covers all, hops are neighbours"
              + (f"  missing={missing} bad={bad}" if not ok else ""))
        fails += not ok

    # cutting a link must change somebody's mind
    cut = link_down(TOPOLOGY, "u", "x")
    after = forwarding_table(cut, "u")
    ok = after != table
    print(f"  {'ok  ' if ok else 'FAIL'}  u reroutes when u-x goes down: {after}")
    fails += not ok

    print(f"\n  {'all ok' if not fails else str(fails) + ' failed'}")
    return 1 if fails else 0


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--verify", action="store_true")
    a = p.parse_args()
    raise SystemExit(verify() if a.verify else p.print_help())
