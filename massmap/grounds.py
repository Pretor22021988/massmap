from __future__ import annotations

from datetime import date

from .models import Case, Cycle, Entity, Ground
from .periods import applicable
from .practice import NullSearch, PracticeSearch

# Что входит в предмет доказывания по каждому основанию.
TO_PROVE = {
    "п. 2 ст. 61.3 Закона о банкротстве": [
        "оказание предпочтения перед другими кредиторами",
        "совершение сделки в пределах месяца до принятия заявления",
    ],
    "п. 3 ст. 61.3 Закона о банкротстве": [
        "оказание предпочтения перед другими кредиторами",
        "осведомлённость контрагента о неплатёжеспособности или недостаточности имущества",
    ],
    "п. 1 ст. 61.2 Закона о банкротстве": [
        "неравноценность встречного исполнения",
        "сопоставление условий с аналогичными сделками в сравнимых обстоятельствах",
    ],
    "п. 2 ст. 61.2 Закона о банкротстве": [
        "цель причинения вреда имущественным правам кредиторов",
        "причинение вреда в результате совершения сделки",
        "осведомлённость другой стороны о цели должника",
    ],
}


def qualify(
    case: Case,
    cycles: list[Cycle],
    entities: dict[str, Entity],
    search: PracticeSearch | None = None,
) -> list[Ground]:
    search = search or NullSearch()
    grounds: list[Ground] = []

    for c in cycles:
        if c.excluded:
            continue
        periods = applicable(c.last, case.accepted)
        if not periods:
            continue

        supporting: list[str] = [
            f"компонента сильной связности из {len(c.members)} участников, "
            f"оборот {c.turnover:,.0f} ₽, {c.payments} платежей".replace(",", " ")
        ]
        affiliated = [m for m in c.members if entities.get(m) and entities[m].affiliated]
        if affiliated:
            supporting.append(
                "в составе компоненты аффилированные с должником лица: "
                + ", ".join(entities[m].name for m in affiliated)
            )
        risky = [m for m in c.members if entities.get(m) and entities[m].risk == "высокий"]
        if risky:
            supporting.append(
                "высокий риск по данным ФНС: " + ", ".join(entities[m].name for m in risky)
            )

        for p in periods:
            grounds.append(Ground(
                norm=p.norm,
                title=p.title,
                cycle_members=c.members,
                facts_supporting=supporting,
                facts_to_prove=TO_PROVE.get(p.norm, []),
                practice=search.find(f"{p.norm} транзитные перечисления внутри группы"),
            ))
    return grounds


def subsidiary_flags(cycles: list[Cycle], entities: dict[str, Entity]) -> list[str]:
    """Признаки, при которых стоит проверять основания по ст. 61.11.

    Это именно признаки для проверки, а не вывод о наличии оснований.
    """
    flags: list[str] = []
    live = [c for c in cycles if not c.excluded]
    if live:
        flags.append(
            "выявлены транзитные цепочки — проверить, охватываются ли они "
            "существенно убыточными сделками по смыслу ст. 61.11 Закона о банкротстве"
        )
    controlled = [e for e in entities.values() if e.affiliated]
    if controlled:
        flags.append(
            "установлены аффилированные участники расчётов — определить круг "
            "контролирующих должника лиц"
        )
    return flags
