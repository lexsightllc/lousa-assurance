import math
from datetime import datetime
from typing import Dict, Any
from .models import RiskNote, Claim


def p_to_logodds(p: float) -> float:
    p = min(max(p, 1e-9), 1-1e-9)
    return math.log(p / (1-p))


def logodds_to_p(lo: float) -> float:
    odds = math.exp(lo)
    return odds / (1 + odds)


def evaluate_claim(claim: Claim, now: datetime | None = None) -> Dict[str, Any]:
    now = now or datetime.utcnow()
    lo = p_to_logodds(claim.prior_risk)
    contributions = []
    for ev in claim.evidence:
        decay = ev.decay_factor(now)
        lr = ev.lr_pos if ev.supports else ev.lr_neg
        # convert LR to log space, apply weight and temporal decay
        delta = math.log(lr) * ev.weight * decay
        lo += delta
        contributions.append({
            "evidence_id": ev.id, "supports": ev.supports,
            "lr": lr, "decay": decay, "delta_logodds": delta
        })
    posterior = logodds_to_p(lo)
    if claim.valid_until and now > claim.valid_until:
        posture = "Expired"
    elif posterior >= claim.threshold_blocking:
        posture = "Blocking"
    elif posterior >= claim.threshold_conditional:
        posture = "Conditional"
    else:
        posture = "Acceptable"
    return {
        "claim_id": claim.id,
        "posterior_risk": posterior,
        "posture": posture,
        "contributions": contributions
    }


def evaluate(note: RiskNote, now: datetime | None = None) -> Dict[str, Any]:
    now = now or datetime.utcnow()
    claim_results = [evaluate_claim(c, now) for c in note.claims]
    posture_rollup = "Blocking" if any(r["posture"] == "Blocking" for r in claim_results) \
        else "Conditional" if any(r["posture"] == "Conditional" for r in claim_results) \
        else "Acceptable" if all(r["posture"] == "Acceptable" for r in claim_results) \
        else "Expired"
    return {"note_id": note.id, "at": now.isoformat(), "posture": posture_rollup, "claims": claim_results}
