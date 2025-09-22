from econsim.preferences import CobbDouglasPreference, PreferenceFactory


def test_round_trip_serialization_equivalence():
    original = CobbDouglasPreference(alpha=0.42)
    data = original.serialize()
    clone = PreferenceFactory.from_serialized(data)
    # verify same utility across several bundles
    samples = [(1.0, 2.0), (2.5, 3.5), (4.0, 1.0)]
    for bundle in samples:
        assert abs(original.utility(bundle) - clone.utility(bundle)) < 1e-12
