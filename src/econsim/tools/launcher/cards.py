"""Launcher UI – Card models & placeholder widget.

Phase 3 extraction target. This module intentionally keeps business logic out;
card models are pure data derived from the `TestRegistry`. The Qt widget will
remain minimal and delegate actions back via provided controllers (ComparisonController,
TestExecutor).

Part 2 Gate G11 focuses on deterministic model ordering & purity.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List
from pathlib import Path

try:  # Typed import; ignore if Qt not available in headless minimal test
    from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
except Exception:  # pragma: no cover - allows pure tests without Qt plugin
    QWidget = object  # type: ignore
    QVBoxLayout = QLabel = QPushButton = object  # type: ignore

from .registry import TestRegistry
from .comparison import ComparisonController
from .executor import TestExecutor


@dataclass(frozen=True, slots=True)
class TestCardModel:
    """Pure representation of a test configuration for UI rendering.

    Ordering Invariant: Instances will be produced by `build_card_models` in a
    deterministic order (default ascending test id). A future enhancement may
    allow alternate sort strategies but G11 fixes the baseline for snapshot tests.
    """

    id: int
    label: str
    mode: str
    file: Path | None
    order: int
    meta: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:  # convenience for JSON export / tests
        return {
            "id": self.id,
            "label": self.label,
            "mode": self.mode,
            "file": str(self.file) if self.file else None,
            "order": self.order,
            "meta": self.meta,
        }


def build_card_models(registry: TestRegistry) -> List[TestCardModel]:
    """Build deterministic list of card models from the registry.

    Current strategy: ascending by test id. This mirrors the implicit ordering of
    the legacy `ALL_TEST_CONFIGS.values()` iteration (dict insertion order based
    on original construction). If a future divergence is detected we can inject
    a custom ordering map; snapshot tests will highlight changes.
    """
    models: List[TestCardModel] = []
    # registry.all() returns dict[int, TestConfiguration]; iteration order is key order
    for order, (tid, cfg) in enumerate(sorted(registry.all().items()), start=1):
        models.append(
            TestCardModel(
                id=tid,
                label=cfg.label,
                mode=cfg.mode,
                file=cfg.file,
                order=order,
                meta=cfg.meta,
            )
        )
    return models


class TestCard(QWidget):  # pragma: no cover - GUI behaviour will be smoke/integration tested
    """Minimal placeholder widget (will be expanded in later sub-phases).

    Responsibilities kept intentionally thin for initial extraction:
    * Display label
    * Provide basic launch buttons (original / framework) – wired externally
    * Provide comparison add toggle
    """

    def __init__(self, model: TestCardModel, comparison: ComparisonController, executor: TestExecutor):  # type: ignore[override]
        super().__init__()  # type: ignore[misc]
        self._model = model
        self._comparison = comparison
        self._executor = executor
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout()  # type: ignore[call-arg]
        layout.addWidget(QLabel(self._model.label))  # type: ignore[arg-type]
        btn_launch_original = QPushButton("Launch Original")  # type: ignore[call-arg]
        btn_launch_framework = QPushButton("Launch Framework")  # type: ignore[call-arg]
        btn_compare = QPushButton("Add to Comparison")  # type: ignore[call-arg]

        # Wire actions – deferring robust error handling until later phases
        try:
            btn_launch_original.clicked.connect(lambda: self._executor.launch_original(self._model.label))  # type: ignore[attr-defined]
            btn_launch_framework.clicked.connect(lambda: self._executor.launch_framework(self._model.label))  # type: ignore[attr-defined]
            btn_compare.clicked.connect(lambda: self._comparison.add(self._model.label))  # type: ignore[attr-defined]
        except Exception:
            pass  # In headless/type-stub environment signals may be absent

        layout.addWidget(btn_launch_original)  # type: ignore[arg-type]
        layout.addWidget(btn_launch_framework)  # type: ignore[arg-type]
        layout.addWidget(btn_compare)  # type: ignore[arg-type]
        try:
            self.setLayout(layout)  # type: ignore[attr-defined]
        except Exception:
            pass
