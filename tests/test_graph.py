from datetime import date

from massmap.graph import build, cycles
from massmap.models import Payment


def p(a, b, amount=1.0, when=date(2024, 1, 1), purpose=""):
    return Payment(payer=a, payee=b, amount=amount, when=when, purpose=purpose)


def test_finds_cycle_and_ignores_chain():
    payments = [p("A", "B", 10), p("B", "C", 9), p("C", "A", 8), p("A", "D", 5)]
    c = cycles(build(payments))
    assert len(c) == 1
    assert c[0].members == ["A", "B", "C"]
    assert c[0].turnover == 27
    assert c[0].payments == 3


def test_no_cycle():
    assert cycles(build([p("A", "B"), p("B", "C")])) == []


def test_edges_are_aggregated():
    g = build([p("A", "B", 10, date(2024, 1, 1)), p("A", "B", 5, date(2024, 5, 1))])
    e = g["A"]["B"]
    assert e["amount"] == 15 and e["count"] == 2
    assert e["first"] == date(2024, 1, 1) and e["last"] == date(2024, 5, 1)


def test_two_independent_cycles_sorted_by_turnover():
    payments = [p("A", "B", 1), p("B", "A", 1), p("X", "Y", 100), p("Y", "X", 100)]
    c = cycles(build(payments))
    assert [x.members for x in c] == [["X", "Y"], ["A", "B"]]
