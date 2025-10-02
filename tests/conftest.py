import os
import sys
import pathlib
import pytest

# --- Path bootstrap for tests expecting `src.*` imports ---------------------
# Some tests import modules as `from src.econsim...`. When running pytest in
# certain environments the repository root may not be on sys.path early enough.
# We defensively add the repo root (parent of this file's directory) if `src`
# is not importable. This is hash-neutral and only affects test import setup.
try:  # pragma: no cover - trivial bootstrap
    import src  # type: ignore
except Exception:  # noqa: BLE001
    repo_root = pathlib.Path(__file__).resolve().parent.parent
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    try:
        import src  # type: ignore  # noqa: F401
    except Exception:
        # Fallback: in CI some layouts may shift; attempt grandparent
        alt_root = repo_root.parent
        if str(alt_root) not in sys.path:
            sys.path.insert(0, str(alt_root))


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
