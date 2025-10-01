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

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QStackedWidget,
    QMessageBox,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
)

from .start_menu import StartMenuPage, MenuSelection
from .session_factory import SessionFactory, SimulationSessionDescriptor
from .simulation_controller import SimulationController
from .panels.controls_panel import ControlsPanel
from .panels.metrics_panel import MetricsPanel
from .panels.overlays_panel import OverlaysPanel
from .panels.status_footer_bar import StatusFooterBar
from .embedded_pygame import EmbeddedPygameWidget  # reuse existing rendering widget


@dataclass
class _SimulationPageBundle:
    container: QWidget
    controller: SimulationController
    pygame_widget: EmbeddedPygameWidget
    controls: ControlsPanel
    metrics: MetricsPanel
    agent_inspector: QWidget


class MainWindow(QMainWindow):  # pragma: no cover (GUI; exercised via smoke tests later)
    MENU_INDEX = 0
    SIM_INDEX = 1

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("EconSim – Experimental GUI Shell")
        self._stack = QStackedWidget(self)
        self.setCentralWidget(self._stack)
        self._session: Optional[_SimulationPageBundle] = None
        self.setStyleSheet(
            """
            QMainWindow, QWidget, QDialog {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QGroupBox {
                font-weight: 600;
                margin-top: 8px;
                color: #ffffff;
                border: 2px solid #555555;
                border-radius: 3px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 6px;
                padding: 0 4px;
                background-color: #2b2b2b;
            }
            QLabel {
                font-size: 11px;
                color: #ffffff;
            }
            QPushButton {
                background-color: #404040;
                color: #ffffff;
                border: 1px solid #666666;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #4a4a4a;
            }
            QTextEdit, QPlainTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid #555555;
            }
            """
        )

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
                viewport_size=selection.viewport_size,
                distance_scaling_factor=getattr(selection, 'distance_scaling_factor', 0.0),
            )
            controller = SessionFactory.build(descriptor)
        except Exception as exc:  # pragma: no cover - user input / validation path
            QMessageBox.critical(self, "Launch Error", f"Failed to build simulation: {exc}")
            return

        decision_enabled = bool(selection.decision_mode_enabled)
        if selection.mode == "legacy":
            decision_enabled = False

        # Build simulation page lazily with horizontal layout per ASCII design
        sim_container = QWidget()
        main_layout = QVBoxLayout(sim_container)
        
        # Top section: Pygame viewport (left) + Control panels (right)
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)

        # Left side: Pygame viewport (configurable size)
        pygame_widget = EmbeddedPygameWidget(
            simulation=controller.simulation,
            decision_mode=decision_enabled,
        )
        pygame_widget.setFixedSize(descriptor.viewport_size, descriptor.viewport_size)  # Enforce viewport size per selection
        pygame_widget.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        # Attach controller for pause state / pacing coordination (legacy alias retained for compatibility)
        pygame_widget.controller = controller  # type: ignore[attr-defined]
        setattr(pygame_widget, "_controller_ref", controller)
        
        # Right side: Control panels in vertical stack
        panels_layout = QVBoxLayout()
        
        # Create panels with group boxes per ASCII layout
        from .panels.agent_inspector_panel import AgentInspectorPanel
        from .panels.event_log_panel import EventLogPanel
        
        # Controls group
        controls_group = QGroupBox("CONTROLS")
        controls_layout = QVBoxLayout(controls_group)
        controls = ControlsPanel(on_back=self._request_return_to_menu, controller=controller)
        controls_layout.addWidget(controls)
        
        # Overlays group  
        overlays_group = QGroupBox("OVERLAYS")
        overlays_layout = QVBoxLayout(overlays_group)
        if pygame_widget.overlay_state:
            overlay_panel = OverlaysPanel(pygame_widget.overlay_state)
            overlays_layout.addWidget(overlay_panel)
        
        # Metrics group
        metrics_group = QGroupBox("METRICS")
        metrics_layout = QVBoxLayout(metrics_group)
        metrics = MetricsPanel(controller=controller)
        metrics_layout.addWidget(metrics)
        
        # Agent Inspector group
        inspector_group = QGroupBox("AGENT INSPECTOR")
        inspector_layout = QVBoxLayout(inspector_group)
        agent_inspector = AgentInspectorPanel(controller=controller)
        inspector_layout.addWidget(agent_inspector)
        
        # Connect agent inspector to pygame widget for visual highlighting
        pygame_widget.agent_inspector = agent_inspector  # type: ignore[attr-defined]
        
        # Add grouped panels to right side
        panels_layout.addWidget(controls_group)
        panels_layout.addWidget(overlays_group)
        panels_layout.addWidget(metrics_group)
        panels_layout.addWidget(inspector_group)
        panels_layout.addStretch()  # Push panels to top
        
        # Event Log group (left side)
        event_log_group = QGroupBox("EVENT LOG")
        event_log_layout = QVBoxLayout(event_log_group)
        event_log = EventLogPanel(controller=controller)
        event_log_layout.addWidget(event_log)
        event_log_group.setFixedWidth(300)  # Fixed width for consistent layout
        
        # Add all three sections to content layout: [Event Log] [Pygame] [Panels]
        content_layout.addWidget(event_log_group, 0)
        content_layout.addWidget(pygame_widget, 0)
        content_layout.addLayout(panels_layout, 1)
        content_layout.setStretch(0, 0)  # Event log: fixed width
        content_layout.setStretch(1, 0)  # Pygame: fixed size
        content_layout.setStretch(2, 1)  # Panels: expandable

        # Align controller decision mode with widget decision mode (for manual steps determinism)
        try:
            controller.set_decision_mode(decision_enabled)  # type: ignore[attr-defined]
        except Exception:
            pass
        # Bilateral exchange is now controlled via the simulation controls panel, not start menu
        # Configure initial playback pacing per mode (turn vs continuous/legacy)
        try:
            controls.configure_for_mode(descriptor.mode)  # type: ignore[attr-defined]
        except Exception:
            pass
        
        # Add content and status footer to main layout
        main_layout.addLayout(content_layout)
        
        # Status footer bar per ASCII layout design
        if pygame_widget.overlay_state:
            status_footer = StatusFooterBar(controller=controller, overlay_state=pygame_widget.overlay_state)
            main_layout.addWidget(status_footer)
        
        self._session = _SimulationPageBundle(
            container=sim_container,
            controller=controller,
            pygame_widget=pygame_widget,
            controls=controls,
            metrics=metrics,
            agent_inspector=agent_inspector,
        )
        # Replace placeholder
        self._stack.removeWidget(self._stack.widget(self.SIM_INDEX))
        self._stack.insertWidget(self.SIM_INDEX, sim_container)
        self._stack.setCurrentIndex(self.SIM_INDEX)
        pygame_widget.setFocus()

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
        super().closeEvent(event)  # type: ignore[arg-type]


def should_use_new_gui() -> bool:
    return os.environ.get("ECONSIM_NEW_GUI") == "1"


__all__ = ["MainWindow", "should_use_new_gui"]
