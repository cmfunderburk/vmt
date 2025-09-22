from econsim.preferences import CobbDouglasPreference, PreferenceError


def test_cobb_douglas_basic_utility():
    pref = CobbDouglasPreference(alpha=0.5)
    # sqrt(4) * sqrt(9) = 2 * 3 = 6
    assert abs(pref.utility((4.0, 9.0)) - 6.0) < 1e-9


def test_cobb_douglas_zero_bundle():
    pref = CobbDouglasPreference(alpha=0.4)
    assert pref.utility((0.0, 5.0)) == 0.0
    assert pref.utility((3.0, 0.0)) == 0.0


def test_cobb_douglas_alpha_validation():
    try:
        CobbDouglasPreference(alpha=0.0)  # invalid
    except PreferenceError:
        pass
    else:
        assert False, "Expected PreferenceError for alpha=0.0"


def test_cobb_douglas_update_params():
    pref = CobbDouglasPreference(alpha=0.3)
    pref.update_params(alpha=0.7)
    assert abs(pref.alpha - 0.7) < 1e-12


def test_cobb_douglas_serialize_round_trip():
    pref = CobbDouglasPreference(alpha=0.55)
    data = pref.serialize()
    from econsim.preferences.cobb_douglas import CobbDouglasPreference as CD

    clone = CD.deserialize(data)
    assert abs(clone.alpha - pref.alpha) < 1e-12
    assert abs(clone.utility((2.0, 5.0)) - pref.utility((2.0, 5.0))) < 1e-12
