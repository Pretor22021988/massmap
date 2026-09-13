from __future__ import annotations

import argparse
import csv
import sys
from datetime import date, datetime
from pathlib import Path

from .models import Case, Entity, Payment
from .pipeline import run


def _date(s: str) -> date:
    return datetime.strptime(s.strip(), "%Y-%m-%d").date()


def load_payments(path: Path) -> list[Payment]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return [
            Payment(
                payer=r["payer"].strip(),
                payee=r["payee"].strip(),
                amount=float(r["amount"]),
                when=_date(r["when"]),
                purpose=r.get("purpose", ""),
                doc=r.get("doc", ""),
            )
            for r in csv.DictReader(f)
        ]


def load_entities(path: Path) -> dict[str, Entity]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        out = {}
        for r in csv.DictReader(f):
            inn = r["inn"].strip()
            out[inn] = Entity(
                inn=inn,
                name=r["name"].strip(),
                affiliated=r.get("affiliated", "").strip().lower() in ("1", "да", "true"),
                affiliation_source=(r.get("affiliation_source") or "").strip() or None,
            )
        return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="massmap", description="Заключение о перспективах пополнения конкурсной массы")
    ap.add_argument("--payments", required=True, type=Path)
    ap.add_argument("--entities", required=True, type=Path)
    ap.add_argument("--debtor-inn", required=True)
    ap.add_argument("--debtor-name", required=True)
    ap.add_argument("--accepted", required=True, type=_date, help="дата принятия заявления, ГГГГ-ММ-ДД")
    ap.add_argument("--claim", type=float, default=None)
    ap.add_argument("--min-turnover", type=float, default=0.0)
    ap.add_argument("--has-statements", action="store_true")
    ap.add_argument("--out", type=Path, default=Path("zaklyuchenie.md"))
    a = ap.parse_args(argv)

    payments = load_payments(a.payments)
    entities = load_entities(a.entities)
    case = Case(debtor_inn=a.debtor_inn, debtor_name=a.debtor_name,
                accepted=a.accepted, creditor_claim=a.claim)
    text = run(case, payments, entities,
               min_turnover=a.min_turnover, has_statements=a.has_statements)
    a.out.write_text(text, encoding="utf-8")
    print(f"готово: {a.out} ({len(text)} символов)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
