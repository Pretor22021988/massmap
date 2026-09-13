"""Отсев связности, которой есть хозяйственное объяснение.

Наивное правило «в компоненте встретилось безобидное назначение платежа —
исключаем компоненту» неверно, и это видно на первом же реальном примере.
Один встречный платёж по аренде между должником и арендодателем склеивает
арендодателя с транзитной цепочкой в одну компоненту сильной связности,
после чего наивное правило вычёркивает всю цепочку вместе с ним.

Правильный порядок обратный: сначала из графа удаляются рёбра, которым есть
хозяйственное объяснение, и только потом ищется связность. Объяснённый
платёж не должен создавать связность, на которой строится вывод о транзите.

Раздел об отсеве в заключении важнее раздела о находках: он показывает, что
работа велась на исключение версий, а не на набор страшных цифр.
"""
from __future__ import annotations

import re

import networkx as nx

from .models import Cycle, Payment

# Назначения платежа, при которых встречное движение средств нормально.
BENIGN: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"возврат\s+(излишне|ошибочно)", re.I), "возврат ошибочного платежа"),
    (re.compile(r"аренд", re.I), "расчёты по аренде"),
    (re.compile(r"(зарплат|заработн)", re.I), "расчёты по оплате труда"),
    (re.compile(r"(налог|страховы[ех]\s+взнос|пошлин)", re.I), "обязательные платежи"),
    (re.compile(r"(коммунальн|электроэнерг|водоснабж|теплоснабж)", re.I), "коммунальные платежи"),
)


def explain_edge(purposes: list[str]) -> str | None:
    """Объяснение для ребра, если все платежи по нему объяснимы."""
    if not purposes:
        return None
    reasons: set[str] = set()
    for text in purposes:
        for pattern, reason in BENIGN:
            if pattern.search(text):
                reasons.add(reason)
                break
        else:
            return None  # хотя бы один платёж без объяснения — ребро остаётся
    return ", ".join(sorted(reasons))


def strip_explained(g: nx.DiGraph, payments: list[Payment]) -> tuple[nx.DiGraph, dict]:
    """Убрать из графа рёбра с хозяйственным объяснением."""
    by_pair: dict[tuple[str, str], list[str]] = {}
    for p in payments:
        by_pair.setdefault((p.payer, p.payee), []).append(p.purpose)

    clean = g.copy()
    removed: dict[tuple[str, str], str] = {}
    for (a, b), purposes in by_pair.items():
        reason = explain_edge(purposes)
        if reason and clean.has_edge(a, b):
            clean.remove_edge(a, b)
            removed[(a, b)] = reason
    return clean, removed


def split(
    full_cycles: list[Cycle],
    clean_cycles: list[Cycle],
    removed: dict,
    *,
    min_turnover: float = 0.0,
) -> list[Cycle]:
    """Разделить компоненты на живые и объяснённые.

    Живой считается компонента, уцелевшая после удаления объяснённых рёбер.
    Компонента, распавшаяся при их удалении, держалась на этих платежах —
    и в заключение идёт как исключённая, с указанием причины.
    """
    survived = {frozenset(c.members): c for c in clean_cycles}
    out: list[Cycle] = []

    for c in full_cycles:
        key = frozenset(c.members)
        if key in survived:
            live = survived[key]
            if live.turnover < min_turnover:
                live.excluded = True
                live.exclusion_reason = (
                    f"оборот ниже порога {min_turnover:,.0f} ₽".replace(",", " ")
                )
            out.append(live)
            continue

        inner = [ic for ic in clean_cycles if set(ic.members) < key]
        reasons = sorted({r for (a, b), r in removed.items()
                          if a in key and b in key})
        note = ", ".join(reasons) if reasons else "связность не подтверждается"
        if inner:
            note += (f"; после отсева распалась на меньшие компоненты "
                     f"({len(inner)} шт.), они рассматриваются отдельно")
        c.excluded = True
        c.exclusion_reason = note
        out.append(c)

    for ic in clean_cycles:
        if not any(frozenset(o.members) == frozenset(ic.members) for o in out):
            if ic.turnover < min_turnover:
                ic.excluded = True
                ic.exclusion_reason = (
                    f"оборот ниже порога {min_turnover:,.0f} ₽".replace(",", " ")
                )
            out.append(ic)

    return sorted(out, key=lambda c: (c.excluded, -c.turnover))
