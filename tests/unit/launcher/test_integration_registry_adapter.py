from econsim.tools.launcher.adapters import load_registry_from_monolith


def test_adapter_registry_basic():
    registry = load_registry_from_monolith()
    all_cfgs = registry.all()
    # Expect at least the 7 legacy tests (baseline + others)
    assert len(all_cfgs) >= 7
    labels = [c.label for c in all_cfgs.values()]
    # Ensure baseline style label present
    assert any("Baseline" in lbl or "Baseline" in lbl for lbl in labels)
    # Validate no duplicate labels
    assert len(labels) == len(set(labels))
