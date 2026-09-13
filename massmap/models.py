from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, field_validator

RiskLevel = Literal["низкий", "средний", "высокий", "неизвестен"]


class Entity(BaseModel):
    """Участник расчётов."""
    inn: str = Field(..., min_length=10, max_length=12)
    name: str
    affiliated: bool = False
    affiliation_source: str | None = None
    risk: RiskLevel = "неизвестен"
    risk_factors: list[str] = Field(default_factory=list)

    @field_validator("inn")
    @classmethod
    def _digits(cls, v: str) -> str:
        if not v.isdigit():
            raise ValueError("ИНН должен состоять из цифр")
        return v


class Payment(BaseModel):
    payer: str
    payee: str
    amount: float = Field(..., gt=0)
    when: date
    purpose: str = ""
    doc: str = ""

    @field_validator("payee")
    @classmethod
    def _no_self(cls, v: str, info) -> str:
        if info.data.get("payer") == v:
            raise ValueError("платёж самому себе")
        return v


class Cycle(BaseModel):
    """Компонента сильной связности размером больше одного узла."""
    members: list[str]
    turnover: float
    payments: int
    first: date
    last: date
    excluded: bool = False
    exclusion_reason: str | None = None


class Ground(BaseModel):
    """Основание для оспаривания, подобранное под найденную фактуру."""
    norm: str
    title: str
    cycle_members: list[str]
    facts_supporting: list[str]
    facts_to_prove: list[str]
    practice: list[str] = Field(default_factory=list)


class Case(BaseModel):
    debtor_inn: str
    debtor_name: str
    accepted: date = Field(..., description="дата принятия заявления о банкротстве")
    creditor_claim: float | None = None
