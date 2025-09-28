import pytest

from econsim.preferences import PerfectSubstitutesPreference, PreferenceError
from econsim.simulation.constants import UTILITY_SCALE_FACTOR


def test_ps_basic_utility():
    pref = PerfectSubstitutesPreference(a=2.0, b=1.0)
    # U = 2*3 + 1*5 = 11 then scaled
    expected = 11.0 * UTILITY_SCALE_FACTOR
    assert abs(pref.utility((3.0, 5.0)) - expected) < 1e-7


def test_ps_update_params():
    pref = PerfectSubstitutesPreference(a=1.0, b=1.0)
    pref.update_params(a=3.0)
    expected = 4.0 * UTILITY_SCALE_FACTOR  # 3*1 + 1*1 then scaled
    assert abs(pref.utility((1.0, 1.0)) - expected) < 1e-7


def test_ps_invalid_coeff():
    with pytest.raises(PreferenceError):
        PerfectSubstitutesPreference(a=0.0, b=1.0)


def test_ps_serialize_round_trip():
    pref = PerfectSubstitutesPreference(a=1.5, b=0.75)
    data = pref.serialize()
    from econsim.preferences.perfect_substitutes import PerfectSubstitutesPreference as PS

    clone = PS.deserialize(data)
    assert abs(clone.utility((2.0, 4.0)) - pref.utility((2.0, 4.0))) < 1e-12
