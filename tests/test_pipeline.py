from datetime import date
from pathlib import Path

from massmap.cli import load_entities, load_payments
from massmap.models import Case
from massmap.pipeline import run

EX = Path(__file__).resolve().parent.parent / "examples"


def _report(**kw):
    case = Case(debtor_inn="7701000001", debtor_name="ООО «Должник»",
                accepted=date(2025, 1, 20), creditor_claim=18_000_000)
    return run(case, load_payments(EX / "payments_sample.csv"),
               load_entities(EX / "entities_sample.csv"), **kw)


def test_report_has_all_sections():
    r = _report()
    for h in ("## 1. Ответ", "## 2. Участники", "## 3. Транзитные цепочки",
              "### 3.1. Исключённые компоненты", "## 4. Основания",
              "## 5. Судебная практика", "## 6. Что делать дальше"):
        assert h in r, h


def test_transit_cycle_found_and_qualified():
    r = _report()
    assert "вступать активно" in r
    assert "п. 2 ст. 61.2 Закона о банкротстве" in r


def test_benign_cycle_excluded():
    """Аренда с возвратом переплаты — компонента, но не транзит."""
    r = _report()
    section = r.split("### 3.1.")[1].split("## 4.")[0]
    assert "ООО «Арендодатель»" in section


def test_caveats_present_without_statements():
    r = _report(has_statements=False)
    assert "Ограничение объёма" in r
    assert "не заменяет доказательств" in r


def test_min_turnover_filters():
    r = _report(min_turnover=10_000_000_000)
    assert "Рекомендация: **наблюдать**" in r


def test_explained_edge_does_not_absorb_transit_chain():
    """Регрессия: встречный платёж по аренде склеивал арендодателя с
    транзитной цепочкой в одну компоненту, и наивный отсев вычёркивал всю
    цепочку. Объяснённые рёбра должны удаляться ДО поиска связности."""
    r = _report()
    live = r.split("## 3. Транзитные цепочки")[1].split("### 3.1.")[0]
    assert "ООО «Вектор»" in live and "ООО «Трансгруз»" in live
    assert "ООО «Арендодатель»" not in live
