import pytest

from econsim.preferences import LeontiefPreference, PreferenceError
from econsim.simulation.constants import UTILITY_SCALE_FACTOR


def test_leontief_basic_utility():
    pref = LeontiefPreference(a=2.0, b=4.0)
    # U = min(6/2, 20/4) = 3 then scaled
    expected = 3.0 * UTILITY_SCALE_FACTOR
    assert abs(pref.utility((6.0, 20.0)) - expected) < 1e-7


def test_leontief_update_params():
    pref = LeontiefPreference(a=1.0, b=1.0)
    pref.update_params(a=2.0)
    expected = 2.0 * UTILITY_SCALE_FACTOR  # min(4/2, 10/1)=2 then scaled
    assert abs(pref.utility((4.0, 10.0)) - expected) < 1e-7


def test_leontief_invalid_coeff():
    with pytest.raises(PreferenceError):
        LeontiefPreference(a=-1.0, b=1.0)


def test_leontief_serialize_round_trip():
    pref = LeontiefPreference(a=1.2, b=3.4)
    data = pref.serialize()
    from econsim.preferences.leontief import LeontiefPreference as L

    clone = L.deserialize(data)
    assert abs(clone.utility((5.0, 10.0)) - pref.utility((5.0, 10.0))) < 1e-12
