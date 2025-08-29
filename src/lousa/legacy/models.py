from __future__ import annotations

import math
from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict


class Posture(str, Enum):
    ACCEPTABLE = "ACCEPTABLE"
    CONDITIONAL = "CONDITIONAL"
    BLOCKING = "BLOCKING"
    EXPIRED = "EXPIRED"


class EvidenceKind(str, Enum):
    TEST = "TEST"
    AUDIT = "AUDIT"
    LOG = "LOG"
    METRIC = "METRIC"
    REPORT = "REPORT"
    REDTEAM = "REDTEAM"
    SIMULATION = "SIMULATION"
    OTHER = "OTHER"


class EvidenceItem(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=False)

    id: str
    kind: EvidenceKind
    title: Optional[str] = None
    description: Optional[str] = None
    source: Optional[str] = None  # URL, file path, or locator
    observed_at: datetime
    supports: bool = True  # True if observation supports the risk hypothesis
    lr_pos: float = Field(..., description="Positive likelihood ratio (>= 1.0)")
    lr_neg: float = Field(..., description="Negative likelihood ratio (<= 1.0)")
    weight: float = Field(1.0, ge=0.0, description="Confidence weight multiplier")
    halflife_days: Optional[float] = Field(
        default=None, gt=0.0, description="Half-life for this evidence item"
    )

    @field_validator("lr_pos")
    @classmethod
    def _check_lr_pos(cls, v: float) -> float:
        if not (v >= 1.0 and math.isfinite(v)):
            raise ValueError("lr_pos must be finite and >= 1.0")
        return v

    @field_validator("lr_neg")
    @classmethod
    def _check_lr_neg(cls, v: float) -> float:
        if not (0.0 < v <= 1.0 and math.isfinite(v)):
            raise ValueError("lr_neg must be finite and in (0, 1]")
        return v


class Investigation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=False)

    id: str
    title: str
    description: Optional[str] = None
    expected_lr_support: float = Field(..., ge=1.0, description="LR+ if investigation supports risk")
    expected_lr_refute: float = Field(..., gt=0.0, le=1.0, description="LR- if investigation refutes risk")
    cost_hours: float = Field(..., gt=0.0)
    probability_support: float = Field(0.5, ge=0.0, le=1.0)


class Claim(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=False)

    id: str
    title: str
    description: Optional[str] = None

    prior: float = Field(..., gt=0.0, lt=1.0, description="Prior probability of risk")
    threshold_conditional: float = Field(..., gt=0.0, lt=1.0)
    threshold_blocking: float = Field(..., gt=0.0, lt=1.0)

    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None

    staleness_halflife_days: Optional[float] = Field(
        default=None,
        gt=0.0,
        description="Half-life to decay claim prior toward 0.5 as claim ages",
    )

    contexts: List[str] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)
    justifications: List[str] = Field(default_factory=list)

    evidence: List[EvidenceItem] = Field(default_factory=list)
    investigations: List[Investigation] = Field(default_factory=list)

    @model_validator(mode="after")
    def _check_thresholds_and_times(self) -> "Claim":
        if not (self.threshold_conditional < self.threshold_blocking):
            raise ValueError("threshold_conditional must be < threshold_blocking")
        if self.valid_from and self.valid_until and not (self.valid_from < self.valid_until):
            raise ValueError("valid_from must be earlier than valid_until")
        return self


class RiskNote(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=False)

    version: str
    id: str
    title: str
    description: Optional[str] = None
    context: dict = Field(default_factory=dict)
    claims: List[Claim] = Field(default_factory=list)


import math
from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict


class Posture(str, Enum):
    ACCEPTABLE = "ACCEPTABLE"
    CONDITIONAL = "CONDITIONAL"
    BLOCKING = "BLOCKING"
    EXPIRED = "EXPIRED"


class EvidenceKind(str, Enum):
    TEST = "TEST"
    AUDIT = "AUDIT"
    LOG = "LOG"
    METRIC = "METRIC"
    REPORT = "REPORT"
    REDTEAM = "REDTEAM"
    SIMULATION = "SIMULATION"
    OTHER = "OTHER"


class EvidenceItem(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=False)

    id: str
    kind: EvidenceKind
    title: Optional[str] = None
    description: Optional[str] = None
    source: Optional[str] = None  # URL, file path, or locator
    observed_at: datetime
    supports: bool = True  # True if observation supports the risk hypothesis
    lr_pos: float = Field(..., description="Positive likelihood ratio (>= 1.0)")
    lr_neg: float = Field(..., description="Negative likelihood ratio (<= 1.0)")
    weight: float = Field(1.0, ge=0.0, description="Confidence weight multiplier")
    halflife_days: Optional[float] = Field(
        default=None, gt=0.0, description="Half-life for this evidence item"
    )

    @field_validator("lr_pos")
    @classmethod
    def _check_lr_pos(cls, v: float) -> float:
        if not (v >= 1.0 and math.isfinite(v)):
            raise ValueError("lr_pos must be finite and >= 1.0")
        return v

    @field_validator("lr_neg")
    @classmethod
    def _check_lr_neg(cls, v: float) -> float:
        if not (0.0 < v <= 1.0 and math.isfinite(v)):
            raise ValueError("lr_neg must be finite and in (0, 1]")
        return v


class Investigation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=False)

    id: str
    title: str
    description: Optional[str] = None
    expected_lr_support: float = Field(..., ge=1.0, description="LR+ if investigation supports risk")
    expected_lr_refute: float = Field(..., gt=0.0, le=1.0, description="LR- if investigation refutes risk")
    cost_hours: float = Field(..., gt=0.0)
    probability_support: float = Field(0.5, ge=0.0, le=1.0)


class Claim(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=False)

    id: str
    title: str
    description: Optional[str] = None

    prior: float = Field(..., gt=0.0, lt=1.0, description="Prior probability of risk")
    threshold_conditional: float = Field(..., gt=0.0, lt=1.0)
    threshold_blocking: float = Field(..., gt=0.0, lt=1.0)

    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None

    staleness_halflife_days: Optional[float] = Field(
        default=None,
        gt=0.0,
        description="Half-life to decay claim prior toward 0.5 as claim ages",
    )

    contexts: List[str] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)
    justifications: List[str] = Field(default_factory=list)

    evidence: List[EvidenceItem] = Field(default_factory=list)
    investigations: List[Investigation] = Field(default_factory=list)

    @model_validator(mode="after")
    def _check_thresholds_and_times(self) -> "Claim":
        if not (self.threshold_conditional < self.threshold_blocking):
            raise ValueError("threshold_conditional must be < threshold_blocking")
        if self.valid_from and self.valid_until and not (self.valid_from < self.valid_until):
            raise ValueError("valid_from must be earlier than valid_until")
        return self


class RiskNote(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=False)

    version: str
    id: str
    title: str
    description: Optional[str] = None
    context: dict = Field(default_factory=dict)
    claims: List[Claim] = Field(default_factory=list)


    


        if self.staleness_halflife_days is None:
            return 1.0
        age = (now - self.observed_at).total_seconds()
        halflife = self.staleness_halflife_days * 86400.0
        return 0.5 ** (age / halflife)

class Investigation(BaseModel):
    id: str
    description: str
    cost_hours: float
    expected_lr_pos: float
    expected_lr_neg: float
    target_claim: str

class Claim(BaseModel):
    id: str
    title: str
    description: str
    prior_risk: float = Field(..., gt=0.0, lt=1.0)  # P(risk) prior
    threshold_blocking: float = 0.5
    threshold_conditional: float = 0.2
    observed_at: datetime
    valid_until: Optional[datetime] = None
    staleness_halflife_days: Optional[float] = Field(default=180.0)
    evidence: List[EvidenceItem] = []
    investigations: List[Investigation] = []

    @field_validator("valid_until")
    @classmethod
    def check_valid(cls, v, info):
        if v and v <= info.data["observed_at"]:
            raise ValueError("valid_until must be after observed_at")
        return v

class RiskNote(BaseModel):
    version: str
    id: str
    title: str
    context: Dict[str,str] = {}
    claims: List[Claim]
