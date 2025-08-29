from calculate_posture import calculate_posture


def test_posture_logic_asymmetric_dominance():
    # severidade alta domina
    assert calculate_posture(4, 3, 3) == "red"
    # reversibilidade muito baixa também
    assert calculate_posture(3, 2, 2) in ("amber","red")
    # risco moderado cai em amber, baixo em green
    assert calculate_posture(3, 2, 3) in ("amber","red")
    assert calculate_posture(1, 1, 4) == "green"
