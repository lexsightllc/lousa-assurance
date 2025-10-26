# SPDX-License-Identifier: MPL-2.0
import math
from typing import Dict
from .models import Claim, Investigation
from .eval import p_to_logodds, logodds_to_p


def expected_posterior(p: float, inv: Investigation) -> float:
    lo = p_to_logodds(p)
    lo_pos = lo + math.log(inv.expected_lr_pos)
    lo_neg = lo + math.log(inv.expected_lr_neg)
    # Assume Bernoulli outcome weighted by current belief p
    return p * logodds_to_p(lo_pos) + (1 - p) * logodds_to_p(lo_neg)


def posture_cost(p: float, t_cond: float, t_block: float, c_cond: float = 1.0, c_block: float = 5.0) -> float:
    if p >= t_block: return c_block
    if p >= t_cond: return c_cond
    return 0.0


def evoi_for_claim(claim: Claim, posterior: float, inv: Investigation) -> Dict[str, float]:
    before = posture_cost(posterior, claim.threshold_conditional, claim.threshold_blocking)
    after_p = expected_posterior(posterior, inv)
    after = posture_cost(after_p, claim.threshold_conditional, claim.threshold_blocking)
    gain = max(0.0, before - after)
    roi = gain / max(1e-6, inv.cost_hours)
    return {"investigation_id": inv.id, "expected_gain": gain, "roi_per_hour": roi, "after_posterior": after_p}
