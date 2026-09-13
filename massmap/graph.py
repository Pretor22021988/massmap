from __future__ import annotations

from collections import defaultdict

import networkx as nx

from .models import Cycle, Payment


def build(payments: list[Payment]) -> nx.DiGraph:
    g = nx.DiGraph()
    agg: dict[tuple[str, str], dict] = defaultdict(
        lambda: {"amount": 0.0, "count": 0, "first": None, "last": None}
    )
    for p in payments:
        e = agg[(p.payer, p.payee)]
        e["amount"] += p.amount
        e["count"] += 1
        e["first"] = p.when if e["first"] is None else min(e["first"], p.when)
        e["last"] = p.when if e["last"] is None else max(e["last"], p.when)
    for (payer, payee), e in agg.items():
        g.add_edge(payer, payee, **e)
    return g


def cycles(g: nx.DiGraph) -> list[Cycle]:
    """Компоненты сильной связности размером больше одного узла.

    networkx использует нерекурсивный вариант алгоритма Тарьяна, поэтому
    глубина графа не ограничена стеком интерпретатора.
    """
    out: list[Cycle] = []
    for comp in nx.strongly_connected_components(g):
        if len(comp) < 2:
            continue
        sub = g.subgraph(comp)
        turnover = sum(d["amount"] for _, _, d in sub.edges(data=True))
        count = sum(d["count"] for _, _, d in sub.edges(data=True))
        firsts = [d["first"] for _, _, d in sub.edges(data=True)]
        lasts = [d["last"] for _, _, d in sub.edges(data=True)]
        out.append(Cycle(
            members=sorted(comp),
            turnover=turnover,
            payments=count,
            first=min(firsts),
            last=max(lasts),
        ))
    return sorted(out, key=lambda c: c.turnover, reverse=True)
