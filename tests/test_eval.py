from datetime import datetime, timedelta
from lousa.models import Claim, EvidenceItem
from lousa.eval import evaluate_claim


def test_supporting_evidence_increases_risk():
    now = datetime(2025,8,10)
    c = Claim(id="c", title="t", description="d", prior_risk=0.2, observed_at=now)
    c.evidence.append(EvidenceItem(id="e1", kind="test_result", observed_at=now, lr_pos=3, lr_neg=0.4, supports=True))
    r = evaluate_claim(c, now)
    assert r["posterior_risk"] > 0.2


def test_temporal_decay_reduces_influence():
    now = datetime(2025,8,10)
    old = now - timedelta(days=365)
    c = Claim(id="c", title="t", description="d", prior_risk=0.2, observed_at=now)
    fresh = EvidenceItem(id="fresh", kind="test_result", observed_at=now, lr_pos=3, lr_neg=0.4, supports=True)
    stale = EvidenceItem(id="stale", kind="test_result", observed_at=old, staleness_halflife_days=90, lr_pos=3, lr_neg=0.4, supports=True)
    c.evidence.extend([fresh, stale])
    r = evaluate_claim(c, now)
    # remove stale and confirm a small delta
    c.evidence = [fresh]
    r2 = evaluate_claim(c, now)
    assert r["posterior_risk"] > r2["posterior_risk"]
