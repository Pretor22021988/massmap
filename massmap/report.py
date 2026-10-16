from __future__ import annotations

from datetime import date

from .models import Case, Cycle, Entity, Ground
from .periods import PERIODS


def _money(x: float) -> str:
    return f"{x:,.0f} ₽".replace(",", " ")


def _plural(n: int, one: str, few: str, many: str) -> str:
    """Согласование существительного с числительным по правилам русского языка."""
    n = abs(n) % 100
    if 11 <= n <= 14:
        return many
    n %= 10
    if n == 1:
        return one
    if 2 <= n <= 4:
        return few
    return many


def render(
    case: Case,
    cycles: list[Cycle],
    entities: dict[str, Entity],
    grounds: list[Ground],
    flags: list[str],
    *,
    has_statements: bool,
) -> str:
    live = [c for c in cycles if not c.excluded]
    dropped = [c for c in cycles if c.excluded]
    total = sum(c.turnover for c in live)

    L: list[str] = []
    a = L.append

    a(f"# Заключение о перспективах пополнения конкурсной массы")
    a("")
    a(f"**Должник:** {case.debtor_name}, ИНН {case.debtor_inn}  ")
    a(f"**Дата принятия заявления о банкротстве:** {case.accepted:%d.%m.%Y}  ")
    if case.creditor_claim:
        a(f"**Требование заказчика в реестре:** {_money(case.creditor_claim)}  ")
    a(f"**Дата заключения:** {date.today():%d.%m.%Y}")
    a("")

    a("## 1. Ответ")
    a("")
    if live:
        word = _plural(len(live), "транзитная цепочка", "транзитные цепочки", "транзитных цепочек")
        verb = _plural(len(live), "Выявлена", "Выявлены", "Выявлено")
        gword = _plural(len(grounds), "основание", "основания", "оснований")
        a(f"{verb} **{len(live)}** {word} совокупным оборотом **{_money(total)}**. "
          f"Оснований для оспаривания — **{len(grounds)}** {gword}.")
        a("")
        a("Рекомендация: **вступать активно** — заявлять о признании сделок "
          "недействительными и ходатайствовать об истребовании документов.")
    else:
        a("Транзитных цепочек, не имеющих хозяйственного объяснения, не выявлено.")
        a("")
        a("Рекомендация: **наблюдать**. По имеющимся данным самостоятельных "
          "оснований для оспаривания не усматривается.")
    a("")

    a("## 2. Участники расчётов")
    a("")
    a("| ИНН | Наименование | Аффилированность | Риск по ФНС |")
    a("|---|---|---|---|")
    for e in sorted(entities.values(), key=lambda x: x.name):
        aff = e.affiliation_source or ("да" if e.affiliated else "не установлена")
        a(f"| {e.inn} | {e.name} | {aff} | {e.risk} |")
    a("")

    a("## 3. Транзитные цепочки")
    a("")
    if live:
        for i, c in enumerate(live, 1):
            names = ", ".join(entities[m].name if m in entities else m for m in c.members)
            a(f"**Цепочка {i}.** {names}")
            a("")
            a(f"- оборот внутри компоненты: {_money(c.turnover)}")
            a(f"- платежей: {c.payments}")
            a(f"- период: {c.first:%d.%m.%Y} — {c.last:%d.%m.%Y}")
            a("")
    else:
        a("Не выявлено.")
        a("")

    a("### 3.1. Исключённые компоненты")
    a("")
    if dropped:
        a("Следующие компоненты исключены как имеющие хозяйственное объяснение:")
        a("")
        for c in dropped:
            names = ", ".join(entities[m].name if m in entities else m for m in c.members)
            a(f"- {names} — {c.exclusion_reason} (оборот {_money(c.turnover)})")
        a("")
    else:
        a("Исключённых компонент нет.")
        a("")

    a("## 4. Основания")
    a("")
    if grounds:
        for i, gr in enumerate(grounds, 1):
            names = ", ".join(entities[m].name if m in entities else m for m in gr.cycle_members)
            a(f"### 4.{i}. {gr.norm}")
            a("")
            a(f"*{gr.title}.* Участники: {names}")
            a("")
            a("**Подтверждается имеющимися данными:**")
            for f in gr.facts_supporting:
                a(f"- {f}")
            a("")
            a("**Подлежит доказыванию:**")
            for f in gr.facts_to_prove:
                a(f"- {f}")
            a("")
    else:
        a("Оснований не установлено.")
        a("")

    a("### 4.9. Признаки для проверки субсидиарной ответственности")
    a("")
    if flags:
        for f in flags:
            a(f"- {f}")
    else:
        a("Не выявлены.")
    a("")

    a("## 5. Судебная практика")
    a("")
    prac = [p for gr in grounds for p in gr.practice]
    if prac:
        for p in dict.fromkeys(prac):
            a(f"- {p}")
        a("")
        a("> Реквизиты каждого акта подлежат сверке по первоисточнику "
          "до включения в процессуальный документ.")
    else:
        a("Подбор практики не выполнялся: модуль поиска не подключён.")
    a("")

    a("## 6. Что делать дальше")
    a("")
    a("Периоды подозрительности отсчитываются от даты принятия заявления "
      f"({case.accepted:%d.%m.%Y}):")
    a("")
    a("| Норма | Период | Начало периода |")
    a("|---|---|---|")
    for p in PERIODS:
        end = p.end(case.accepted)
        a(f"| {p.norm} | {p.title} | {p.start(case.accepted):%d.%m.%Y}"
          + (f" — {end:%d.%m.%Y}" if end else "") + " |")
    a("")
    if not has_statements:
        a("**Ограничение объёма.** Расчёт выполнен без банковских выписок "
          "должника. Открытые данные показывают связи, но не движение средств "
          "по счетам вне периметра предоставленной выгрузки. Первоочередное "
          "действие — ходатайство об истребовании выписок.")
        a("")
    a("**Оговорка.** Компонента сильной связности означает возможность возврата "
      "средств к отправителю, а не доказанность транзита. Настоящее заключение "
      "сужает поле проверки и не заменяет доказательств по делу. Заключение не "
      "является экспертизой в процессуальном смысле.")
    a("")
    return "\n".join(L)
