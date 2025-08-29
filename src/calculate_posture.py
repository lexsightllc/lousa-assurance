from typing import Literal

# Simple posture calculation based on severity, probability, and reversibility.
# High severity or poor reversibility triggers "red". Moderate combined factors
# produce "amber". Otherwise the posture is "green".

def calculate_posture(severity: int, probability: int, reversibility: int) -> Literal["red","amber","green"]:
    if severity >= 4 or reversibility <= 2:
        return "red"
    if severity >= 2 and probability >= 2:
        return "amber"
    return "green"
