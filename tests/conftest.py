import os
import pytest

TRADE_FLAG_PREFIX = 'ECONSIM_TRADE_'

@pytest.fixture(autouse=True)
def clear_trade_flags():  # type: ignore[no-untyped-def]
    """Ensure each test starts with a clean slate for trade feature flags.

    This prevents cross-test leakage where one test enabling a flag affects
    another test that assumes default (disabled) state.
    """
    # Snapshot values if ever needed for debugging (not restored to keep tests explicit)
    for k in list(os.environ.keys()):
        if k.startswith(TRADE_FLAG_PREFIX):
            del os.environ[k]
    # Provide deterministic default disabled state
    # (No flags set unless a test explicitly opts in.)
    yield
    # Post-test cleanup again in case test created new flags
    for k in list(os.environ.keys()):
        if k.startswith(TRADE_FLAG_PREFIX):
            del os.environ[k]
