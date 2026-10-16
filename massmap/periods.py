"""Периоды подозрительности.

Границы сверены по тексту Федерального закона от 26.10.2002 № 127-ФЗ
в редакции, действующей на 01.09.2026:

* п. 1 ст. 61.2 — один год до принятия заявления (неравноценное встречное
  исполнение). Постановлением КС РФ от 03.02.2022 № 5-П пункт признан не
  соответствующим Конституции в части — при квалификации это учитывается;
* п. 2 ст. 61.2 — три года до принятия заявления (цель причинения вреда);
* п. 2 ст. 61.3 — один месяц до принятия заявления (предпочтение);
* п. 3 ст. 61.3 — не ранее шести и не позднее одного месяца до принятия
  заявления (предпочтение при осведомлённости; п. 12 Постановления Пленума
  ВАС РФ от 23.12.2010 № 63). Последний месяц и время после принятия
  заявления охватывает только п. 2 ст. 61.3 (п. 11 того же Постановления).

ВНИМАНИЕ. Федеральным законом от 26.07.2026 № 253-ФЗ в статьи 61.2 и 61.3
внесены изменения, вступающие в силу 27.07.2027. Модуль описывает редакцию,
действующую до этой даты; перед применением после 27.07.2027 границы и
условия подлежат пересмотру.
"""
from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date


def minus_months(d: date, months: int) -> date:
    """Вычесть календарные месяцы, а не 30 дней."""
    total = d.year * 12 + (d.month - 1) - months
    year, month = divmod(total, 12)
    month += 1
    day = min(d.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


@dataclass(frozen=True)
class Period:
    code: str
    norm: str
    title: str
    months_before: int
    # не позднее чем за столько месяцев до принятия заявления; None — верхней границы нет
    ends_months_before: int | None = None

    def start(self, accepted: date) -> date:
        return minus_months(accepted, self.months_before)

    def end(self, accepted: date) -> date | None:
        if self.ends_months_before is None:
            return None
        return minus_months(accepted, self.ends_months_before)

    def covers(self, when: date, accepted: date) -> bool:
        """Сделка попадает в период, если совершена не ранее его начала и не позднее конца.

        Верхней границы нет у п. 2 ст. 61.3 и ст. 61.2: они охватывают и сделки,
        совершённые после принятия заявления. У п. 3 ст. 61.3 период кончается
        за месяц до принятия заявления.
        """
        end = self.end(accepted)
        return when >= self.start(accepted) and (end is None or when <= end)


PERIODS: tuple[Period, ...] = (
    Period("61.3-1m", "п. 2 ст. 61.3 Закона о банкротстве",
           "Предпочтение, один месяц", 1),
    Period("61.3-6m", "п. 3 ст. 61.3 Закона о банкротстве",
           "Предпочтение при осведомлённости, от шести до одного месяца", 6, 1),
    Period("61.2-1y", "п. 1 ст. 61.2 Закона о банкротстве",
           "Неравноценное встречное исполнение, один год", 12),
    Period("61.2-3y", "п. 2 ст. 61.2 Закона о банкротстве",
           "Цель причинения вреда, три года", 36),
)


def applicable(when: date, accepted: date) -> list[Period]:
    """Все периоды, в которые попадает дата сделки, от узкого к широкому."""
    return [p for p in PERIODS if p.covers(when, accepted)]


def deepest_window_start(accepted: date) -> date:
    """Самая ранняя дата, начиная с которой платежи вообще интересны."""
    return minus_months(accepted, max(p.months_before for p in PERIODS))
