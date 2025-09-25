import os
import pytest

TRADE_FLAG_PREFIX = 'ECONSIM_TRADE_'

@pytest.fixture(autouse=True)
def clear_trade_flags():  # type: ignore[no-untyped-def]
    """Ensure each test starts with a clean slate for trade feature flags.

    Removes any ECONSIM_TRADE_* variables before and after each test.
    """
    for k in list(os.environ.keys()):
        if k.startswith(TRADE_FLAG_PREFIX):
            del os.environ[k]
    yield
    for k in list(os.environ.keys()):
        if k.startswith(TRADE_FLAG_PREFIX):
            del os.environ[k]


@pytest.fixture(autouse=True)
def reset_forage_flag():  # type: ignore[no-untyped-def]
    """Normalize foraging flag between tests.

    Tests may toggle ECONSIM_FORAGE_ENABLED; to avoid leakage we explicitly
    restore the default enabled state ('1') before each test and clean up after.

    Rationale: Simulation defaults to foraging enabled when the flag is absent.
    Making the state explicit reduces ambiguity and ensures deterministic
    branching in gating logic across the suite.
    """
    os.environ['ECONSIM_FORAGE_ENABLED'] = '1'
    yield
    if 'ECONSIM_FORAGE_ENABLED' in os.environ:
        del os.environ['ECONSIM_FORAGE_ENABLED']
