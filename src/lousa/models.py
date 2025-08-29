from __future__ import annotations
from pydantic import BaseModel, Field, field_validator
from datetime import datetime, timedelta
from typing import Literal, Optional, Dict, List

class EvidenceItem(BaseModel):
    id: str
    kind: Literal["test_result","redteam_finding","human_review","monitoring_signal"]
    observed_at: datetime
    staleness_halflife_days: Optional[float] = Field(default=90.0)
    lr_pos: float = Field(..., gt=0)  # likelihood ratio if evidence supports risk
    lr_neg: float = Field(..., gt=0)  # likelihood ratio if evidence refutes risk
    supports: bool  # True if this instance supports the risk claim; False if refutes
    weight: float = Field(1.0, ge=0.0)  # downweight noisy sources

    def decay_factor(self, now: datetime) -> float:
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
