# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

import math
from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict


class Posture(str, Enum):
    """Aggregate risk posture of a claim or a note."""

    ACCEPTABLE = "ACCEPTABLE"
    CONDITIONAL = "CONDITIONAL"
    BLOCKING = "BLOCKING"
    EXPIRED = "EXPIRED"


class EvidenceKind(str, Enum):
    """High-level category of an evidence item."""

    TEST = "TEST"
    AUDIT = "AUDIT"
    LOG = "LOG"
    METRIC = "METRIC"
    REPORT = "REPORT"
    REDTEAM = "REDTEAM"
    SIMULATION = "SIMULATION"
    OTHER = "OTHER"


class EvidenceItem(BaseModel):
    """Single observation bearing on a risk claim."""

    model_config = ConfigDict(extra="forbid", frozen=False)

    id: str
    kind: EvidenceKind
    title: Optional[str] = None
    description: Optional[str] = None
    source: Optional[str] = None  # URL, file path, or locator
    observed_at: datetime

    supports: bool = Field(
        True, description="True if the observation supports the presence of risk"
    )
    lr_pos: float = Field(
        ..., ge=1.0, description="Positive likelihood ratio (>=1.0) if supports=True"
    )
    lr_neg: float = Field(
        ..., gt=0.0, le=1.0, description="Negative likelihood ratio (<=1.0) if supports=False"
    )
    weight: float = Field(
        1.0, ge=0.0, description="Confidence multiplier applied to the LR in log-space"
    )
    halflife_days: Optional[float] = Field(
        None, gt=0.0, description="Optional half-life to decay evidential weight over time"
    )

    # ---------------- Validators -----------------

    @field_validator("lr_pos")
    @classmethod
    def _check_lr_pos(cls, v: float) -> float:  # noqa: D401
        """Ensure LR+ is finite and >=1."""
        if not (v >= 1.0 and math.isfinite(v)):
            raise ValueError("lr_pos must be finite and >= 1.0")
        return v

    @field_validator("lr_neg")
    @classmethod
    def _check_lr_neg(cls, v: float) -> float:  # noqa: D401
        """Ensure LR- is in (0,1] and finite."""
        if not (0.0 < v <= 1.0 and math.isfinite(v)):
            raise ValueError("lr_neg must be finite and in (0, 1]")
        return v


class Investigation(BaseModel):
    """Potential future activity to gather more evidence about a claim."""

    model_config = ConfigDict(extra="forbid", frozen=False)

    id: str
    title: str
    description: Optional[str] = None

    expected_lr_support: float = Field(..., ge=1.0)
    expected_lr_refute: float = Field(..., gt=0.0, le=1.0)
    cost_hours: float = Field(..., gt=0.0)
    probability_support: float = Field(0.5, ge=0.0, le=1.0)


class Claim(BaseModel):
    """Risk hypothesis tracked over time by accumulating evidence."""

    model_config = ConfigDict(extra="forbid", frozen=False)

    id: str
    title: str
    description: Optional[str] = None
    observed_at: Optional[datetime] = None

    prior: float = Field(..., gt=0.0, lt=1.0, description="Prior probability of risk")
    threshold_conditional: float = Field(..., gt=0.0, lt=1.0)
    threshold_blocking: float = Field(..., gt=0.0, lt=1.0)

    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None

    staleness_halflife_days: Optional[float] = Field(
        None,
        gt=0.0,
        description="Half-life that decays the prior log-odds toward neutral (0) as the claim ages",
    )

    contexts: List[str] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)
    justifications: List[str] = Field(default_factory=list)

    evidence: List[EvidenceItem] = Field(default_factory=list)
    investigations: List[Investigation] = Field(default_factory=list)

    # ---------------- Validators -----------------

    @model_validator(mode="after")
    def _check_thresholds_and_times(self) -> "Claim":  # noqa: D401
        """Domain checks that depend on multiple fields."""

        if not (self.threshold_conditional < self.threshold_blocking):
            raise ValueError("threshold_conditional must be < threshold_blocking")

        if self.valid_from and self.valid_until and not (self.valid_from < self.valid_until):
            raise ValueError("valid_from must be earlier than valid_until")
        return self


class RiskNote(BaseModel):
    """Top-level document containing multiple claims."""

    model_config = ConfigDict(extra="forbid", frozen=False)

    version: str
    id: str
    title: str
    description: Optional[str] = None
    context: dict = Field(default_factory=dict)
    claims: List[Claim] = Field(default_factory=list)
