import pytest

from econsim.preferences import LeontiefPreference, PreferenceError


def test_leontief_basic_utility():
    pref = LeontiefPreference(a=2.0, b=4.0)
    # U = min(x/a, y/b) = min(6/2, 20/4) = min(3,5)=3
    assert abs(pref.utility((6.0, 20.0)) - 3.0) < 1e-12


def test_leontief_update_params():
    pref = LeontiefPreference(a=1.0, b=1.0)
    pref.update_params(a=2.0)
    assert abs(pref.utility((4.0, 10.0)) - 2.0) < 1e-12  # min(4/2, 10/1)=min(2,10)=2


def test_leontief_invalid_coeff():
    with pytest.raises(PreferenceError):
        LeontiefPreference(a=-1.0, b=1.0)


def test_leontief_serialize_round_trip():
    pref = LeontiefPreference(a=1.2, b=3.4)
    data = pref.serialize()
    from econsim.preferences.leontief import LeontiefPreference as L

    clone = L.deserialize(data)
    assert abs(clone.utility((5.0, 10.0)) - pref.utility((5.0, 10.0))) < 1e-12
