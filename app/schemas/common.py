from __future__ import annotations

from enum import Enum


class PeriodEnum(str, Enum):
    morning = "morning"
    noon = "noon"
    evening = "evening"


class SchemeTypeEnum(str, Enum):
    siting = "siting"
    dispatch = "dispatch"
    analysis = "analysis"
    mixed = "mixed"
