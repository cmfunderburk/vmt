import pytest

from econsim.preferences import (
    CobbDouglasPreference,
    PreferenceFactory,
    list_preferences,
)
from econsim.preferences.base import PreferenceError
from econsim.preferences.factory import register_preference


def test_factory_creates_cobb_douglas():
    obj = PreferenceFactory.create("cobb_douglas", alpha=0.6)
    assert isinstance(obj, CobbDouglasPreference)
    assert abs(obj.alpha - 0.6) < 1e-12


def test_factory_unknown_type():
    with pytest.raises(PreferenceError):
        PreferenceFactory.create("not_a_type")


def test_list_preferences_contains_core():
    types = list_preferences()
    assert "cobb_douglas" in types


def test_register_duplicate_rejected():
    from econsim.preferences.cobb_douglas import CobbDouglasPreference as CD

    with pytest.raises(PreferenceError):
        register_preference(CD.TYPE_NAME, CD)  # already registered


def test_serialization_via_factory():
    obj = PreferenceFactory.create("cobb_douglas", alpha=0.4)
    data = obj.serialize()
    clone = PreferenceFactory.from_serialized(data)
    assert abs(clone.utility((3.0, 7.0)) - obj.utility((3.0, 7.0))) < 1e-12
