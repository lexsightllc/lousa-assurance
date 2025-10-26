# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

"""
Risk-note evaluator operating in log-odds space with decay and reasoning trace.

This module provides functionality to evaluate risk claims using Bayesian updating
in log-odds space, with support for temporal decay of evidence and comprehensive
tracing of the evaluation process.
"""

import math
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, TypedDict, Any

from pydantic import ValidationError

from .models import Claim, EvidenceItem, Posture, RiskNote

########################
# Utility math helpers #
########################

def _now_utc() -> datetime:
    """Get the current UTC time.
    
    Extracted to a function for testability.
    
    Returns:
        Current UTC time with timezone information.
    """
    return datetime.now(timezone.utc)


def _clamp_prob(p: float, eps: float = 1e-9) -> float:
    """Clamp probability to (eps, 1-eps) to avoid numerical instability.
    
    Args:
        p: Probability to clamp
        eps: Smallest allowed probability (default: 1e-9)
        
    Returns:
        Clamped probability
    """
    return min(max(p, eps), 1.0 - eps)


def _prob_to_logodds(p: float) -> float:
    """Convert probability to log-odds space.
    
    Args:
        p: Probability in (0,1)
        
    Returns:
        Log-odds value in (-∞, ∞)
        
    Raises:
        ValueError: If p is not a valid probability
    """
    if not (0 < p < 1):
        raise ValueError(f"Probability {p} must be in (0,1)")
    p = _clamp_prob(p)
    return math.log(p / (1.0 - p))


def _logodds_to_prob(l: float) -> float:
    """Convert log-odds back to probability space.
    
    Uses a numerically stable implementation of the logistic function.
    
    Args:
        l: Log-odds value
        
    Returns:
        Probability in (0,1)
    """
    if l >= 0:
        z = math.exp(-l)
        return 1.0 / (1.0 + z)
    z = math.exp(l)
    return z / (1.0 + z)


def _half_life_decay(age_days: float, halflife_days: Optional[float]) -> float:
    """Calculate decay factor based on half-life.
    
    Args:
        age_days: Age of the evidence in days
        halflife_days: Half-life in days, or None for no decay
        
    Returns:
        Decay factor in (0, 1]
    """
    if halflife_days is None or halflife_days <= 0.0:
        return 1.0
    return 0.5 ** (max(age_days, 0.0) / halflife_days)

#########################
# Trace dataclasses     #
#########################

class EvaluationError(Exception):
    """Raised when there is an error during evaluation."""
    pass


@dataclass
class EvidenceContribution:
    """Detailed contribution of a single piece of evidence to the final result."""
    
    evidence_id: str
    """Unique identifier of the evidence item."""
    
    title: Optional[str]
    """Human-readable title of the evidence, if available."""
    
    supports: bool
    """Whether this evidence supports (True) or refutes (False) the risk."""
    
    lr_applied: float
    """Likelihood ratio that was applied (LR+ if supports=True, LR- if supports=False)."""
    
    weight: float
    """Confidence weight applied to this evidence."""
    
    decay: float
    """Temporal decay factor applied (1.0 = no decay)."""
    
    delta_logodds: float
    """Net contribution to the log-odds from this evidence."""
    
    observed_at: str
    """ISO 8601 timestamp of when this evidence was observed."""


@dataclass
class ClaimResult:
    """Result of evaluating a single claim with detailed trace information."""
    
    claim_id: str
    """Unique identifier of the claim."""
    
    title: str
    """Human-readable title of the claim."""
    
    posterior: float
    """Final probability after applying all evidence (0-1)."""
    
    posture: Posture
    """Risk posture based on thresholds and expiration."""
    
    expired: bool
    """Whether this claim has expired (valid_until is in the past)."""
    
    prior: float
    """Original prior probability (0-1)."""
    
    prior_decay: float
    """Decay factor applied to the prior (1.0 = no decay)."""
    
    prior_logodds_decayed: float
    """Prior in log-odds space after applying decay."""
    
    contributions: List[EvidenceContribution]
    """Detailed contributions from each piece of evidence."""
    
    @property
    def log_odds_ratio(self) -> float:
        """Compute the log-odds ratio from prior to posterior."""
        return _prob_to_logodds(self.posterior) - self.prior_logodds_decayed

#########################
# Core evaluation       #
#########################

def _map_posture(posterior: float, claim: Claim, expired: bool) -> Posture:
    """Determine the risk posture based on posterior probability and thresholds.
    
    Args:
        posterior: Computed posterior probability (0-1)
        claim: The claim being evaluated
        expired: Whether the claim has expired
        
    Returns:
        The appropriate Posture enum value
    """
    if not (0 <= posterior <= 1):
        raise EvaluationError(f"Invalid posterior probability: {posterior}")
        
    if expired:
        return Posture.EXPIRED
        
    if not (0 < claim.threshold_conditional < claim.threshold_blocking < 1):
        raise EvaluationError(
            f"Invalid thresholds: conditional={claim.threshold_conditional}, "
            f"blocking={claim.threshold_blocking}"
        )
    
    if posterior >= claim.threshold_blocking:
        return Posture.BLOCKING
    if posterior >= claim.threshold_conditional:
        return Posture.CONDITIONAL
    return Posture.ACCEPTABLE


def _decay_prior_logodds(claim: Claim, now: datetime) -> Tuple[float, float]:
    """Apply temporal decay to the prior probability.
    
    If the claim has a staleness half-life and a valid_from date, the prior
    log-odds will be decayed toward zero (neutral evidence) over time.
    
    Args:
        claim: The claim with prior and decay parameters
        now: Current time for calculating age
        
    Returns:
        Tuple of (decayed_logodds, decay_factor)
    """
    try:
        logodds = _prob_to_logodds(claim.prior)
    except ValueError as e:
        raise EvaluationError(f"Invalid prior probability: {claim.prior}") from e
    
    if claim.staleness_halflife_days and claim.valid_from:
        try:
            age_days = (now - claim.valid_from).total_seconds() / 86400.0
            decay_factor = _half_life_decay(age_days, claim.staleness_halflife_days)
            decayed_logodds = logodds * decay_factor
            return decayed_logodds, decay_factor
        except (TypeError, OverflowError) as e:
            raise EvaluationError("Error calculating prior decay") from e
            
    return logodds, 1.0


def evaluate_claim(claim: Claim, now: Optional[datetime] = None) -> ClaimResult:
    """Evaluate a single claim, returning detailed trace information.
    
    This function performs Bayesian updating in log-odds space, applying temporal
    decay to both the prior and evidence items as specified.
    
    Args:
        claim: The claim to evaluate
        now: Optional timestamp to use as "now" (defaults to current time)
        
    Returns:
        A ClaimResult object with the evaluation results and full trace
        
    Raises:
        EvaluationError: If there's an error during evaluation
    """
    try:
        now = now or _now_utc()
        
        # Check claim expiration
        expired = bool(claim.valid_until and now > claim.valid_until)

        # Start with decayed prior in log-odds space
        prior_logodds_decayed, prior_decay = _decay_prior_logodds(claim, now)
        logodds = prior_logodds_decayed

        contribs: List[EvidenceContribution] = []

        # Apply evidence in chronological order
        for ev in sorted(claim.evidence, key=lambda e: e.observed_at):
            try:
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
            except (ValueError, OverflowError) as e:
                raise EvaluationError(f"Error processing evidence {ev.id}: {e}") from e

        try:
            posterior = _logodds_to_prob(logodds)
            posture = _map_posture(posterior, claim, expired)
        except (ValueError, ZeroDivisionError) as e:
            raise EvaluationError("Error calculating posterior probability") from e

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
        
    except Exception as e:
        if not isinstance(e, EvaluationError):
            raise EvaluationError(f"Unexpected error evaluating claim {claim.id}: {e}") from e
        raise

#########################
# Note-level evaluation #
#########################

class NoteEvaluationResult(TypedDict):
    """Result of evaluating a complete risk note."""
    
    note_id: str
    """Unique identifier of the evaluated note."""
    
    title: str
    """Title of the note."""
    
    evaluated_at: str
    """ISO 8601 timestamp of when the evaluation was performed."""
    
    overall_posture: Posture
    """Most severe posture across all claims."""
    
    claims: List[ClaimResult]
    """Results for each individual claim."""
    
    recommendations: List[Dict[str, Any]]
    """List of recommended investigations, sorted by expected value per hour."""


def evaluate_note(note: RiskNote, now: Optional[datetime] = None) -> NoteEvaluationResult:
    """Evaluate an entire risk note and rank investigations by EVOI per hour.
    
    This function evaluates all claims in the note and computes the expected value
    of information (EVOI) for each investigation to prioritize next steps.
    
    Args:
        note: The risk note to evaluate
        now: Optional timestamp to use as "now" (defaults to current time)
        
    Returns:
        A dictionary with the evaluation results and recommendations
    """
    now = now or _now_utc()
    
    # Evaluate all claims
    claim_results = []
    for claim in note.claims:
        try:
            result = evaluate_claim(claim, now)
            claim_results.append(result)
        except EvaluationError as e:
            # Skip claims that fail evaluation but continue with others
            print(f"Warning: {e}")
            continue
    
    # Determine overall posture (most severe across all claims)
    posture_priority = {
        Posture.BLOCKING: 3,
        Posture.CONDITIONAL: 2,
        Posture.ACCEPTABLE: 1,
        Posture.EXPIRED: 0
    }
    
    overall_posture = max(
        (cr.posture for cr in claim_results if not cr.expired),
        default=Posture.ACCEPTABLE,
        key=lambda p: posture_priority.get(p, -1)
    )
    
    # Generate recommendations by computing expected value of information
    recommendations = []
    for claim in note.claims:
        if not claim.investigations:
            continue
            
        # Get the current evaluation for this claim
        claim_result = next(
            (cr for cr in claim_results if cr.claim_id == claim.id),
            None
        )
        if not claim_result:
            continue
            
        current_logodds = _prob_to_logodds(claim_result.posterior)
        
        for inv in claim.investigations:
            # Skip invalid investigations
            if inv.probability_support <= 0 or inv.probability_support >= 1:
                continue
                
            # Calculate expected posterior if investigation supports risk
            support_logodds = current_logodds + math.log(inv.expected_lr_support)
            support_posterior = _logodds_to_prob(support_logodds)
            
            # Calculate expected posterior if investigation refutes risk
            refute_logodds = current_logodds + math.log(inv.expected_lr_refute)
            refute_posterior = _logodds_to_prob(refute_logodds)
            
            # Calculate expected change in probability
            p_support = inv.probability_support
            p_refute = 1 - p_support
            
            expected_delta = (
                p_support * (support_posterior - claim_result.posterior) +
                p_refute * (refute_posterior - claim_result.posterior)
            )
            
            # Skip recommendations with no expected impact
            if abs(expected_delta) < 1e-6 or inv.cost_hours <= 0:
                continue
                
            recommendations.append({
                "investigation_id": inv.id,
                "title": inv.title,
                "claim_id": claim.id,
                "claim_title": claim.title,
                "expected_delta": expected_delta,
                "cost_hours": inv.cost_hours,
                "delta_per_hour": abs(expected_delta) / inv.cost_hours,
                "probability_support": inv.probability_support,
            })
    
    # Sort recommendations by absolute impact per hour, descending
    recommendations.sort(key=lambda r: r["delta_per_hour"], reverse=True)

    return NoteEvaluationResult(
        note_id=note.id,
        title=note.title,
        evaluated_at=now.isoformat(),
        overall_posture=overall_posture,
        claims=claim_results,
        recommendations=recommendations,
    )
