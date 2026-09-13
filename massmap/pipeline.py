from __future__ import annotations

from .filters import split, strip_explained
from .graph import build, cycles as find_cycles
from .grounds import qualify, subsidiary_flags
from .models import Case, Entity, Payment
from .practice import NullSearch, PracticeSearch
from .report import render
from .risk import NullScorer, Scorer, enrich


def run(
    case: Case,
    payments: list[Payment],
    entities: dict[str, Entity],
    *,
    scorer: Scorer | None = None,
    search: PracticeSearch | None = None,
    min_turnover: float = 0.0,
    has_statements: bool = False,
) -> str:
    entities = enrich(entities, scorer or NullScorer())

    g = build(payments)
    clean, removed = strip_explained(g, payments)
    cyc = split(find_cycles(g), find_cycles(clean), removed, min_turnover=min_turnover)

    grounds = qualify(case, cyc, entities, search or NullSearch())
    flags = subsidiary_flags(cyc, entities)
    return render(case, cyc, entities, grounds, flags, has_statements=has_statements)
