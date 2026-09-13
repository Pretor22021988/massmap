"""Адаптер к hybrid-search-ru.

Поиск практики живёт в отдельном репозитории. Здесь контракт и заглушка.

Важно: подобранная практика идёт в заключение только после сверки реквизитов
по первоисточнику. Найденное поиском — кандидат, а не ссылка.
"""
from __future__ import annotations

from typing import Protocol


class PracticeSearch(Protocol):
    def find(self, query: str, k: int = 5) -> list[str]:
        ...


class NullSearch:
    def find(self, query: str, k: int = 5) -> list[str]:
        return []
