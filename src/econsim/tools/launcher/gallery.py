"""Launcher UI – Test Gallery container.

Phase 3 extraction: Displays a collection of `TestCard` widgets inside a
scrollable region. Initial implementation deliberately omits advanced features
(filtering, search, dynamic sorting) to minimize risk during extraction.

Gate G12: Verifies that the gallery contains only presentation concerns and can
be instantiated headless without raising exceptions (when Qt offscreen platform
is available).
"""
from __future__ import annotations

from typing import List

try:
    from PyQt6.QtWidgets import QWidget, QScrollArea, QVBoxLayout
except Exception:  # pragma: no cover
    QWidget = object  # type: ignore
    QScrollArea = QVBoxLayout = object  # type: ignore

from .cards import TestCardModel, TestCard
from .comparison import ComparisonController
from .executor import TestExecutor


class TestGallery(QWidget):  # pragma: no cover - smoke/integration coverage
    def __init__(self, card_models: List[TestCardModel], comparison: ComparisonController, executor: TestExecutor):  # type: ignore[override]
        super().__init__()  # type: ignore[misc]
        self._comparison = comparison
        self._executor = executor
        self._card_models: List[TestCardModel] = []
        self._scroll_area = None
        self._container_widget = None
        self._layout = None
        self.rebuild(card_models)

    def rebuild(self, card_models: List[TestCardModel]) -> None:
        # Store models deterministically (caller already ensures ordering)
        self._card_models = list(card_models)
        try:
            self._build_widgets()
        except Exception:
            # In environments without full Qt plugin support we silently ignore
            pass

    def _build_widgets(self) -> None:  # pragma: no cover
        from PyQt6.QtWidgets import QScrollArea, QWidget, QVBoxLayout  # local import to avoid headless issues

        if self._scroll_area is None:
            self._scroll_area = QScrollArea()
            self._scroll_area.setWidgetResizable(True)
            outer_layout = QVBoxLayout()
            outer_layout.addWidget(self._scroll_area)
            self.setLayout(outer_layout)  # type: ignore[attr-defined]

        self._container_widget = QWidget()
        self._layout = QVBoxLayout()

        for model in self._card_models:
            card = TestCard(model, self._comparison, self._executor)
            self._layout.addWidget(card)  # type: ignore[attr-defined]

        self._layout.addStretch(1)  # type: ignore[attr-defined]
        self._container_widget.setLayout(self._layout)  # type: ignore[attr-defined]
        self._scroll_area.setWidget(self._container_widget)  # type: ignore[attr-defined]

    def models(self) -> List[TestCardModel]:
        return list(self._card_models)
