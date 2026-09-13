"""Адаптер к fns-debt-risk.

Скоринг живёт в отдельном репозитории. Здесь описан только контракт и
заглушка, чтобы пайплайн запускался без него. Подключение — реализовать
Scorer и передать в pipeline.run(scorer=...).
"""
from __future__ import annotations

from typing import Protocol

from .models import Entity, RiskLevel


class Scorer(Protocol):
    def score(self, inn: str) -> tuple[RiskLevel, list[str]]:
        ...


class NullScorer:
    """Ничего не знает и честно об этом сообщает."""

    def score(self, inn: str) -> tuple[RiskLevel, list[str]]:
        return "неизвестен", []


def enrich(entities: dict[str, Entity], scorer: Scorer) -> dict[str, Entity]:
    for e in entities.values():
        e.risk, e.risk_factors = scorer.score(e.inn)
    return entities
