# SPDX-License-Identifier: MPL-2.0
from datetime import datetime, timedelta

from lousa.eval import evaluate_claim
from lousa.models import Claim, EvidenceItem, EvidenceKind


def test_supporting_evidence_increases_risk():
    now = datetime(2025, 8, 10)
    c = Claim(
        id="c",
        title="t",
        prior=0.2,
        threshold_conditional=0.4,
        threshold_blocking=0.6,
    )
    c.evidence.append(
        EvidenceItem(
            id="e1",
            kind=EvidenceKind.TEST,
            observed_at=now,
            lr_pos=3.0,
            lr_neg=0.4,
            supports=True,
        )
    )
    r = evaluate_claim(c, now)
    assert r.posterior > 0.2


def test_temporal_decay_reduces_influence():
    now = datetime(2025, 8, 10)
    old = now - timedelta(days=365)
    c = Claim(
        id="c",
        title="t",
        prior=0.2,
        threshold_conditional=0.4,
        threshold_blocking=0.6,
    )
    fresh = EvidenceItem(
        id="fresh",
        kind=EvidenceKind.TEST,
        observed_at=now,
        lr_pos=3.0,
        lr_neg=0.4,
        supports=True,
    )
    stale = EvidenceItem(
        id="stale",
        kind=EvidenceKind.TEST,
        observed_at=old,
        halflife_days=90,
        lr_pos=3.0,
        lr_neg=0.4,
        supports=True,
    )
    c.evidence.extend([fresh, stale])
    r = evaluate_claim(c, now)
    # remove stale evidence and recompute
    c.evidence = [fresh]
    r2 = evaluate_claim(c, now)
    assert r.posterior > r2.posterior
