from datetime import date

from massmap.periods import applicable, deepest_window_start, minus_months


def test_minus_months_keeps_calendar():
    assert minus_months(date(2026, 3, 31), 1) == date(2026, 2, 28)
    assert minus_months(date(2026, 1, 15), 12) == date(2025, 1, 15)
    assert minus_months(date(2026, 1, 15), 36) == date(2023, 1, 15)


def test_windows():
    accepted = date(2026, 1, 15)
    assert [p.code for p in applicable(date(2026, 1, 10), accepted)] == \
        ["61.3-1m", "61.3-6m", "61.2-1y", "61.2-3y"]
    assert [p.code for p in applicable(date(2025, 9, 1), accepted)] == \
        ["61.3-6m", "61.2-1y", "61.2-3y"]
    assert [p.code for p in applicable(date(2025, 3, 1), accepted)] == \
        ["61.2-1y", "61.2-3y"]
    assert [p.code for p in applicable(date(2024, 3, 1), accepted)] == ["61.2-3y"]
    assert applicable(date(2020, 1, 1), accepted) == []


def test_after_acceptance_is_covered():
    accepted = date(2026, 1, 15)
    assert len(applicable(date(2026, 5, 1), accepted)) == 4


def test_deepest_window():
    assert deepest_window_start(date(2026, 1, 15)) == date(2023, 1, 15)
