"""Public launcher entrypoint (early stub).

Part 2 objective: Provide a stable `main()` callable so that a console script
`econsim-launcher` can later be exposed. For now we keep behaviour minimal and
backwards compatible: constructing QApplication, styling, registry assembly,
and (optionally) building the new component stack once Phase 3 completes.

This stub intentionally does not import heavy Qt components at module import
time to keep CLI operations like `--list-tests` lightweight.
"""
from __future__ import annotations

from typing import Sequence, List
import sys
import os
import json

from .style import PlatformStyler
from .adapters import load_registry_from_monolith


def _parse_args(argv: Sequence[str]) -> dict:
    # Minimal hand-rolled parser to avoid adding deps.
    flags = {"headless": False, "list_tests": False, "json_registry": False}
    for arg in argv:
        if arg == "--headless":
            flags["headless"] = True
        elif arg == "--list-tests":
            flags["list_tests"] = True
        elif arg == "--json-registry":
            flags["json_registry"] = True
    return flags


def main(argv: List[str] | None = None, headless: bool | None = None) -> int:
    """Launcher entrypoint.

    Parameters
    ----------
    argv: list[str] | None
        Command line style arguments (excluding program name).
    headless: bool | None
        Override headless mode (used mainly by tests). When True we set
        `QT_QPA_PLATFORM=offscreen` if not already set.

    Behaviour
    ---------
    * Loads registry via adapter.
    * If `--list-tests` or `--json-registry` passed, prints test info then exits 0.
    * Otherwise constructs QApplication + (future) LauncherWindow.
    """
    if argv is None:
        argv = sys.argv[1:]
    flags = _parse_args(argv)
    if headless is not None:
        flags["headless"] = headless

    if flags["headless"] and os.environ.get("QT_QPA_PLATFORM") is None:
        os.environ["QT_QPA_PLATFORM"] = "offscreen"

    registry = load_registry_from_monolith()

    if flags["list_tests"] or flags["json_registry"]:
        data = [cfg.label for cfg in registry.all().values()]
        if flags["json_registry"]:
            json.dump({"tests": [cfg.to_dict() for cfg in registry.all().values()]}, sys.stdout)
        else:
            print("\n".join(data))
        return 0

    # Lazy import Qt only when actually launching GUI
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    PlatformStyler.configure_application(app)

    # Phase 3 complete: construct VMTLauncherWindow with all migrated functionality
    from .app_window import VMTLauncherWindow
    
    if flags["headless"]:
        # In headless mode, just validate construction and exit
        try:
            window = VMTLauncherWindow()
            return 0
        except Exception as e:
            print(f"Error creating launcher window: {e}")
            return 1
    else:
        # Normal GUI mode
        window = VMTLauncherWindow()
        window.show()  # type: ignore[attr-defined]
        return app.exec()  # type: ignore[attr-defined]


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
