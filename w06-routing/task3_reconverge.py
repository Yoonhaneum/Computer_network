#!/usr/bin/env python3
"""Week 6 · Task 3 — Reconverge without recomputing the world.

Textbook §5.2.1, §5.3.

A link flaps. Every router in the area has to decide what changed. `FullRecompute`
does the honest thing: throw the table away and run Dijkstra again, from scratch,
for every event. It is correct and it is what the first implementations did.

It is also why a single flapping link in a large area used to melt the CPU of
every router that could see it.

Beat it:

    python3 bench.py
    python3 bench.py --yours

Correctness first. `bench.py` compares your table against a full recompute after
**every single event**. A router that is fast and wrong black-holes traffic.
"""
import heapq

SPF_RUNS = 0


def dijkstra_table(graph, source, return_details=False):
    global SPF_RUNS
    SPF_RUNS += 1

    best = {source: (0, None)}
    parents = {source: None}
    pq = [(0, source, None)]
    done = set()

    while pq:
        cost, node, first_hop = heapq.heappop(pq)

        if node in done:
            continue

        done.add(node)
        best[node] = (cost, first_hop)

        for nbr, w in sorted(graph[node].items()):
            if nbr in done:
                continue

            hop = nbr if node == source else first_hop
            new_cost = cost + w

            if new_cost < best.get(
                nbr, (float("inf"), None)
            )[0]:
                best[nbr] = (new_cost, hop)
                parents[nbr] = node
                heapq.heappush(
                    pq, (new_cost, nbr, hop)
                )

    table = {
        d: h
        for d, (_, h) in best.items()
        if d != source and h is not None
    }

    if return_details:
        distances = {
            d: value[0] for d, value in best.items()
        }
        return table, distances, parents

    return table



class FullRecompute:
    """On every event, forget everything and run SPF again."""

    def __init__(self, graph, source):
        self.graph = {n: dict(e) for n, e in graph.items()}
        self.source = source
        self.table = dijkstra_table(self.graph, source)

    def link_change(self, a, b, cost):
        """cost=None means the link went down."""
        if cost is None:
            self.graph[a].pop(b, None)
            self.graph[b].pop(a, None)
        else:
            self.graph[a][b] = cost
            self.graph[b][a] = cost
        self.table = dijkstra_table(self.graph, self.source)


class YourRouter:
    def __init__(self, graph, source):
        self.graph = {n: dict(e) for n, e in graph.items()}
        self.source = source
        self.table = {}
        self.distances = {}
        self.parents = {}
        self._recompute()

    def _recompute(self):
        (
            self.table,
            self.distances,
            self.parents,
        ) = dijkstra_table(
            self.graph,
            self.source,
            return_details=True,
        )

    def link_change(self, a, b, cost):
        old_cost = self.graph[a].get(b)

        # No change: no recomputation needed.
        if old_cost == cost:
            return

        # Case 1: a link is removed or becomes more expensive.
        if old_cost is not None and (
            cost is None or cost > old_cost
        ):
            # Was this link used by the current shortest-path tree?
            tree_edge = (
                self.parents.get(a) == b
                or self.parents.get(b) == a
            )

            if cost is None:
                self.graph[a].pop(b, None)
                self.graph[b].pop(a, None)
            else:
                self.graph[a][b] = cost
                self.graph[b][a] = cost

            if tree_edge:
                self._recompute()

            return

        # Case 2: a link is added or becomes cheaper.
        da = self.distances.get(a, float("inf"))
        db = self.distances.get(b, float("inf"))

        improves = (
            da != float("inf") and da + cost <= db
        ) or (
            db != float("inf") and db + cost <= da
        )

        self.graph[a][b] = cost
        self.graph[b][a] = cost

        if improves:
            self._recompute()
