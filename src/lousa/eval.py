from __future__ import annotations

"""Risk-note evaluator operating in log-odds space with decay and reasoning trace."""

import math
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from .models import Claim, EvidenceItem, Posture, RiskNote

########################
# Utility math helpers #
########################

def _now_utc() -> datetime:  # extracted for testability
    return datetime.now(timezone.utc)


def _clamp_prob(p: float, eps: float = 1e-9) -> float:
    return min(max(p, eps), 1.0 - eps)


def _prob_to_logodds(p: float) -> float:
    p = _clamp_prob(p)
    return math.log(p / (1.0 - p))


def _logodds_to_prob(l: float) -> float:
    # numerically stable logistic
    if l >= 0:
        z = math.exp(-l)
        return 1.0 / (1.0 + z)
    z = math.exp(l)
    return z / (1.0 + z)


def _half_life_decay(age_days: float, halflife_days: Optional[float]) -> float:
    if halflife_days is None or halflife_days <= 0.0:
        return 1.0
    return 0.5 ** (max(age_days, 0.0) / halflife_days)

#########################
# Trace dataclasses     #
#########################

@dataclass
class EvidenceContribution:
    evidence_id: str
    title: Optional[str]
    supports: bool
    lr_applied: float
    weight: float
    decay: float
    delta_logodds: float
    observed_at: str


@dataclass
class ClaimResult:
    claim_id: str
    title: str
    posterior: float
    posture: Posture
    expired: bool
    prior: float
    prior_decay: float
    prior_logodds_decayed: float
    contributions: List[EvidenceContribution]

#########################
# Core evaluation       #
#########################

def _map_posture(p: float, claim: Claim, expired: bool) -> Posture:
    if expired:
        return Posture.EXPIRED
    if p >= claim.threshold_blocking:
        return Posture.BLOCKING
    if p >= claim.threshold_conditional:
        return Posture.CONDITIONAL
    return Posture.ACCEPTABLE


def _decay_prior_logodds(claim: Claim, now: datetime) -> Tuple[float, float]:
    logodds = _prob_to_logodds(claim.prior)
    if claim.staleness_halflife_days and claim.valid_from:
        age_days = (now - claim.valid_from).total_seconds() / 86400.0
        d = _half_life_decay(age_days, claim.staleness_halflife_days)
        decayed_logodds = logodds * d
        return decayed_logodds, d
    return logodds, 1.0


def evaluate_claim(claim: Claim, now: Optional[datetime] = None) -> ClaimResult:
    """Evaluate a single claim, returning detailed trace information."""

    now = now or _now_utc()

    expired = False
    if claim.valid_until and now > claim.valid_until:
        expired = True

    # start with decayed prior in log-odds space
    prior_logodds_decayed, prior_decay = _decay_prior_logodds(claim, now)
    logodds = prior_logodds_decayed

    contribs: List[EvidenceContribution] = []

    # apply evidence in chronological order
    for ev in sorted(claim.evidence, key=lambda e: e.observed_at):
        lr = ev.lr_pos if ev.supports else ev.lr_neg
        log_lr = math.log(lr)
        age_days = (now - ev.observed_at).total_seconds() / 86400.0
        decay = _half_life_decay(age_days, ev.halflife_days)
        delta = log_lr * ev.weight * decay
        logodds += delta
        contribs.append(
            EvidenceContribution(
                evidence_id=ev.id,
                title=ev.title,
                supports=ev.supports,
                lr_applied=lr,
                weight=ev.weight,
                decay=decay,
                delta_logodds=delta,
                observed_at=ev.observed_at.isoformat(),
            )
        )

    posterior = _logodds_to_prob(logodds)
    posture = _map_posture(posterior, claim, expired)

    return ClaimResult(
        claim_id=claim.id,
        title=claim.title,
        posterior=posterior,
        posture=posture,
        expired=expired,
        prior=claim.prior,
        prior_decay=prior_decay,
        prior_logodds_decayed=prior_logodds_decayed,
        contributions=contribs,
    )

#########################
# Note-level evaluation #
#########################

def evaluate_note(note: RiskNote, now: Optional[datetime] = None) -> Dict:
    """Evaluate an entire risk note and rank investigations by EVOI per hour."""

    now = now or _now_utc()
    claim_results = [evaluate_claim(c, now) for c in note.claims]

    # roll-up posture
    def _rollup(postures: List[Posture]) -> Posture:
        if any(p == Posture.BLOCKING for p in postures):
            return Posture.BLOCKING
        if any(p == Posture.CONDITIONAL for p in postures):
            return Posture.CONDITIONAL
        if all(p == Posture.EXPIRED for p in postures) and postures:
            return Posture.EXPIRED
        return Posture.ACCEPTABLE

    posture = _rollup([r.posture for r in claim_results])

    # ------------------- EVOI --------------------
    recommendations: List[Dict] = []
    for claim, result in zip(note.claims, claim_results):
        if not claim.investigations:
            continue
        # recompute base posterior without expiration/posture logic
        base_logodds = result.prior_logodds_decayed
        for c in result.contributions:
            base_logodds += c.delta_logodds
        base_posterior = _logodds_to_prob(base_logodds)

        for inv in claim.investigations:
            log_lr_support = math.log(inv.expected_lr_support)
            log_lr_refute = math.log(inv.expected_lr_refute)
            p_support = inv.probability_support
            p_refute = 1.0 - p_support

            lo_support = base_logodds + log_lr_support
            lo_refute = base_logodds + log_lr_refute

            p_support_post = _logodds_to_prob(lo_support)
            p_refute_post = _logodds_to_prob(lo_refute)

            expected_delta = p_support * (p_support_post - base_posterior) + p_refute * (
                p_refute_post - base_posterior
            )
            score = abs(expected_delta) / inv.cost_hours

            recommendations.append(
                {
                    "claim_id": claim.id,
                    "investigation_id": inv.id,
                    "title": inv.title,
                    "expected_delta": expected_delta,
                    "delta_per_hour": score,
                    "base_posterior": base_posterior,
                    "posterior_if_support": p_support_post,
                    "posterior_if_refute": p_refute_post,
                    "prob_support": p_support,
                    "cost_hours": inv.cost_hours,
                }
            )

    recommendations.sort(key=lambda r: r["delta_per_hour"], reverse=True)

    # assemble full structured result
    return {
        "note": {
            "version": note.version,
            "id": note.id,
            "title": note.title,
            "description": note.description,
            "context": note.context,
        },
        "evaluated_at": now.isoformat(),
        "claims": [
            {
                "id": r.claim_id,
                "title": r.title,
                "posterior": r.posterior,
                "posture": r.posture.value,
                "expired": r.expired,
                "prior": r.prior,
                "prior_decay": r.prior_decay,
                "trace": [
                    {
                        "kind": "prior",
                        "prior": r.prior,
                        "prior_logodds_decayed": r.prior_logodds_decayed,
                        "decay": r.prior_decay,
                    },
                    *[
                        {
                            "kind": "evidence",
                            "evidence_id": c.evidence_id,
                            "title": c.title,
                            "supports": c.supports,
                            "lr_applied": c.lr_applied,
                            "weight": c.weight,
                            "decay": c.decay,
                            "delta_logodds": c.delta_logodds,
                            "observed_at": c.observed_at,
                        }
                        for c in r.contributions
                    ],
                    {"kind": "posterior", "posterior": r.posterior, "posture": r.posture.value},
                ],
            }
            for r in claim_results
        ],
        "posture": posture.value,
        "recommendations": recommendations,
    }
