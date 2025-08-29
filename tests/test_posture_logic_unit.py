from calculate_posture import calculate_posture


def test_posture_logic_asymmetric_dominance():
    # high severity dominates
    assert calculate_posture(4, 3, 3) == "red"
    # very low reversibility also dominates
    assert calculate_posture(3, 2, 2) in ("amber", "red")
    # moderate risk falls in amber, low in green
    assert calculate_posture(3, 2, 3) in ("amber", "red")
    assert calculate_posture(1, 1, 4) == "green"
