"""Main GUI window with Start Menu → Simulation stack (Phase A scaffold).

Environment opt-in: set ECONSIM_NEW_GUI=1 to launch this window instead of
legacy EmbeddedPygame-only frame. Keeps legacy tests stable while scaffolding.

Design notes:
* Uses QStackedWidget with two pages (menu, simulation)
* Simulation page populated lazily via SessionFactory + SimulationController
* Determinism preserved: all stepping still occurs via EmbeddedPygameWidget timer
  using Simulation.step (no extra loops introduced here)
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QStackedWidget,
    QMessageBox,
    QVBoxLayout,
)

from .start_menu import StartMenuPage, MenuSelection
from .session_factory import SessionFactory, SimulationSessionDescriptor
from .simulation_controller import SimulationController
from .panels.controls_panel import ControlsPanel
from .panels.metrics_panel import MetricsPanel
from .panels.overlays_panel import OverlaysPanel
from .embedded_pygame import EmbeddedPygameWidget  # reuse existing rendering widget


@dataclass
class _SimulationPageBundle:
    container: QWidget
    controller: SimulationController
    pygame_widget: EmbeddedPygameWidget
    controls: ControlsPanel
    metrics: MetricsPanel


class MainWindow(QMainWindow):  # pragma: no cover (GUI; exercised via smoke tests later)
    MENU_INDEX = 0
    SIM_INDEX = 1

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("EconSim – Experimental GUI Shell")
        self._stack = QStackedWidget(self)
        self.setCentralWidget(self._stack)
        self._session: Optional[_SimulationPageBundle] = None

        # Build pages
        self._menu_page = StartMenuPage(on_launch=self._on_launch_requested, parent=self)
        self._stack.addWidget(self._menu_page)  # index 0
        placeholder = QWidget()
        self._stack.addWidget(placeholder)  # simulation page placeholder index 1
        self._stack.setCurrentIndex(self.MENU_INDEX)

    # --- Menu Launch Handling -------------------------------------------------
    def _on_launch_requested(self, selection: MenuSelection) -> None:
        """Callback from StartMenuPage indicating user pressed Launch.

        Translates menu selection → SimulationSessionDescriptor → builds simulation.
        """
        try:
            descriptor = SimulationSessionDescriptor(
                name=selection.scenario,
                mode=selection.mode,
                seed=selection.seed,
                grid_size=selection.grid_size,
                agents=selection.agents,
                density=selection.density,
                enable_respawn=selection.enable_respawn,
                enable_metrics=selection.enable_metrics,
                preference_type=selection.preference_type,
                turn_auto_interval_ms=None,
                start_paused=selection.start_paused,
            )
            controller = SessionFactory.build(descriptor)
        except Exception as exc:  # pragma: no cover - user input / validation path
            QMessageBox.critical(self, "Launch Error", f"Failed to build simulation: {exc}")
            return

        # Build simulation page lazily
        sim_container = QWidget()
        layout = QVBoxLayout(sim_container)
        # Reuse existing widget for rendering; pass simulation + decision mode
        pygame_widget = EmbeddedPygameWidget(
            simulation=controller.simulation,
            decision_mode=(descriptor.mode != "legacy"),
        )
        # Attach back-reference so widget can consult controller pause state / record timestamps
        setattr(pygame_widget, "_controller_ref", controller)
        controls = ControlsPanel(on_back=self._request_return_to_menu, controller=controller)
        metrics = MetricsPanel(controller=controller)
        overlay_panel = OverlaysPanel(pygame_widget.overlay_state) if pygame_widget.overlay_state else None
        # Align controller decision mode with widget decision mode (for manual steps determinism)
        try:
            controller.set_decision_mode(descriptor.mode != "legacy")  # type: ignore[attr-defined]
        except Exception:
            pass
        # Configure initial playback pacing per mode (turn vs continuous/legacy)
        try:
            controls.configure_for_mode(descriptor.mode)  # type: ignore[attr-defined]
        except Exception:
            pass
        layout.addWidget(pygame_widget)
        layout.addWidget(controls)
        layout.addWidget(metrics)
        if overlay_panel is not None:
            layout.addWidget(overlay_panel)
        self._session = _SimulationPageBundle(
            container=sim_container,
            controller=controller,
            pygame_widget=pygame_widget,
            controls=controls,
            metrics=metrics,
        )
        # Replace placeholder
        self._stack.removeWidget(self._stack.widget(self.SIM_INDEX))
        self._stack.insertWidget(self.SIM_INDEX, sim_container)
        self._stack.setCurrentIndex(self.SIM_INDEX)

    # --- Return to Menu -------------------------------------------------------
    def _request_return_to_menu(self) -> None:
        if self._session is None:
            self._stack.setCurrentIndex(self.MENU_INDEX)
            return
        resp = QMessageBox.question(
            self,
            "Return to Menu",
            "End current simulation and return to menu?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if resp == QMessageBox.StandardButton.Yes:
            self._teardown_session()
            self._stack.setCurrentIndex(self.MENU_INDEX)

    def _teardown_session(self) -> None:
        if self._session is None:
            return
        try:
            # Stop widget timer by closing widget (ensures correct order)
            self._session.pygame_widget.close()
            self._session.controller.teardown()
        finally:
            self._session = None

    # --- Close Event ---------------------------------------------------------
    def closeEvent(self, event):  # type: ignore[override]
        self._teardown_session()
        super().closeEvent(event)


def should_use_new_gui() -> bool:
    return os.environ.get("ECONSIM_NEW_GUI") == "1"


__all__ = ["MainWindow", "should_use_new_gui"]
