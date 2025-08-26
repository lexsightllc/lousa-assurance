def calculate_posture(severity, exploitability, reversibility):
    """Default posture calculation with asymmetric risk weighting.
    Severity and reversibility can dominate; otherwise use a simple risk matrix.
    """
    if severity >= 4 or reversibility <= 2:
        if exploitability >= 3:
            return "red"
        elif exploitability >= 2:
            return "amber"
    risk_score = (severity * exploitability) / max(reversibility, 1e-9)
    if risk_score >= 4.0:
        return "red"
    elif risk_score >= 2.0:
        return "amber"
    else:
        return "green"
