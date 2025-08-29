def calculate_posture(severity: int, reversibility: int, likelihood: int) -> str:
    if severity >= 4 or (severity >= 3 and reversibility >= 3):
        return "red"
    if severity <= 1 and reversibility <= 2:
        return "green"
    return "amber"
