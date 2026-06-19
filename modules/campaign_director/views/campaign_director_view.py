"""
campaign_director_view.py — Campaign Director Dashboard UI (Phase 14).

A tabbed visual dashboard for campaign health:
1. 🎬 Health Analytics: Graphical metric bars, pacing state, active directives
2. 📈 Arc Progression: Main campaign, regional, faction, and character arc trees
3. 📜 Director Logs & Reports: Director mode control, report generation, constraint viewer
"""

import json
from pathlib import Path
from typing import Dict
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QGroupBox, QMessageBox, QTabWidget,
    QTreeWidget, QTreeWidgetItem, QSplitter, QComboBox,
    QProgressBar, QFrame, QGridLayout
)
from PySide6.QtCore import Qt

from modules.campaign_director.services.campaign_director_service import CampaignDirectorService


class MetricBar(QWidget):
    """A compact metric display widget with label, progress bar, and value."""

    def __init__(self, label: str, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)

        self.label = QLabel(label)
        self.label.setFixedWidth(140)
        self.label.setStyleSheet("color: #b0b0d0; font-size: 12px; font-weight: bold;")

        self.bar = QProgressBar()
        self.bar.setRange(0, 100)
        self.bar.setValue(0)
        self.bar.setTextVisible(False)
        self.bar.setFixedHeight(18)
        self.bar.setStyleSheet("""
            QProgressBar {
                background-color: #1a1a2e;
                border: 1px solid #2a2a4e;
                border-radius: 4px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #6c63ff, stop:1 #e91e63);
                border-radius: 3px;
            }
        """)

        self.value_label = QLabel("0.000")
        self.value_label.setFixedWidth(55)
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.value_label.setStyleSheet("color: #e0e0ff; font-size: 12px; font-family: monospace;")

        self.status_label = QLabel("—")
        self.status_label.setFixedWidth(100)
        self.status_label.setStyleSheet("color: #a0a0c0; font-size: 11px;")

        layout.addWidget(self.label)
        layout.addWidget(self.bar)
        layout.addWidget(self.value_label)
        layout.addWidget(self.status_label)

    def set_value(self, value: float, status: str = ""):
        self.bar.setValue(int(value * 100))
        self.value_label.setText(f"{value:.3f}")
        self.status_label.setText(status)

        # Color the bar based on value
        if value >= 0.7:
            color = "#e91e63"
        elif value >= 0.4:
            color = "#ff9800"
        else:
            color = "#4caf50"

        self.bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: #1a1a2e;
                border: 1px solid #2a2a4e;
                border-radius: 4px;
            }}
            QProgressBar::chunk {{
                background: {color};
                border-radius: 3px;
            }}
        """)


class CampaignDirectorView(QWidget):
    """UI View for the Autonomous Campaign Director Layer (Phase 14)."""

    def __init__(self):
        super().__init__()
        self.service = CampaignDirectorService()
        self._build_ui()
        self.refresh_all()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        # Header
        header = QHBoxLayout()
        title = QLabel("🎬 Autonomous Campaign Director")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #e91e63; margin-bottom: 5px;")
        header.addWidget(title)

        # Mode selector
        header.addStretch()
        mode_lbl = QLabel("Director Mode:")
        mode_lbl.setStyleSheet("color: #b0b0d0; font-size: 12px;")
        header.addWidget(mode_lbl)

        self.combo_mode = QComboBox()
        self.combo_mode.addItems(["Observation", "Recommendation", "Control"])
        self.combo_mode.setStyleSheet("""
            QComboBox {
                background: #1a1a2e;
                color: #e0e0ff;
                border: 1px solid #6c63ff;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 12px;
            }
        """)
        self.combo_mode.currentIndexChanged.connect(self._on_mode_changed)
        header.addWidget(self.combo_mode)

        layout.addLayout(header)

        # Sub Tabs
        self.tabs = QTabWidget()
        self.tabs.setObjectName("campaignDirectorTabs")

        # Tab 1: Health Analytics
        self.health_tab = QWidget()
        self._build_health_tab()
        self.tabs.addTab(self.health_tab, "🎬 Health Analytics")

        # Tab 2: Arc Progression
        self.arc_tab = QWidget()
        self._build_arc_tab()
        self.tabs.addTab(self.arc_tab, "📈 Arc Progression")

        # Tab 3: Director Logs & Reports
        self.logs_tab = QWidget()
        self._build_logs_tab()
        self.tabs.addTab(self.logs_tab, "📜 Director Logs")

        layout.addWidget(self.tabs)

    def _build_health_tab(self):
        layout = QHBoxLayout(self.health_tab)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left Panel: Metrics
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        metrics_group = QGroupBox("📊 Narrative Health Metrics")
        metrics_layout = QVBoxLayout(metrics_group)

        self.metric_bars = {}
        metric_names = [
            ("tension", "⚡ Tension"),
            ("conflict", "⚔️ Conflict"),
            ("mystery", "🔮 Mystery"),
            ("quest_density", "📜 Quest Density"),
            ("event_frequency", "📅 Event Frequency"),
            ("faction_pressure", "🏛️ Faction Pressure"),
            ("world_stability", "🌍 World Stability"),
        ]
        for key, label in metric_names:
            bar = MetricBar(label)
            self.metric_bars[key] = bar
            metrics_layout.addWidget(bar)

        left_layout.addWidget(metrics_group)

        # Pacing State
        pacing_group = QGroupBox("🎭 Pacing State")
        pacing_layout = QVBoxLayout(pacing_group)

        self.lbl_pacing_state = QLabel("Phase: Rising Action")
        self.lbl_pacing_state.setStyleSheet("color: #e91e63; font-size: 16px; font-weight: bold;")
        pacing_layout.addWidget(self.lbl_pacing_state)

        self.lbl_pacing_signal = QLabel("Pacing Signal: 0.000")
        self.lbl_pacing_signal.setStyleSheet("color: #b0b0d0; font-size: 12px;")
        pacing_layout.addWidget(self.lbl_pacing_signal)

        self.lbl_pacing_ticks = QLabel("Ticks in State: 0")
        self.lbl_pacing_ticks.setStyleSheet("color: #b0b0d0; font-size: 12px;")
        pacing_layout.addWidget(self.lbl_pacing_ticks)

        left_layout.addWidget(pacing_group)

        # Run Director Button
        self.btn_run_director = QPushButton("🎬 Run Campaign Director Tick")
        self.btn_run_director.setStyleSheet(
            "background-color: #e91e63; color: white; font-weight: bold; "
            "padding: 12px; font-size: 14px; border-radius: 6px;"
        )
        self.btn_run_director.clicked.connect(self._run_director_tick)
        left_layout.addWidget(self.btn_run_director)

        left_layout.addStretch()
        splitter.addWidget(left_widget)

        # Right Panel: Active Directives
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)

        directives_group = QGroupBox("📋 Active Director Directives")
        directives_layout = QVBoxLayout(directives_group)
        self.tree_directives = QTreeWidget()
        self.tree_directives.setHeaderLabels(["Priority", "Type", "Description"])
        self.tree_directives.setStyleSheet("background: #15152a; color: #d0d0e8; font-size: 12px;")
        self.tree_directives.setColumnWidth(0, 80)
        self.tree_directives.setColumnWidth(1, 120)
        directives_layout.addWidget(self.tree_directives)
        right_layout.addWidget(directives_group)

        constraints_group = QGroupBox("🔒 Active DM Constraints")
        constraints_layout = QVBoxLayout(constraints_group)
        self.tree_constraints = QTreeWidget()
        self.tree_constraints.setHeaderLabels(["Type", "Description", "Duration"])
        self.tree_constraints.setStyleSheet("background: #15152a; color: #d0d0e8; font-size: 12px;")
        self.tree_constraints.setColumnWidth(0, 150)
        constraints_layout.addWidget(self.tree_constraints)
        right_layout.addWidget(constraints_group)

        splitter.addWidget(right_widget)
        splitter.setSizes([400, 500])
        layout.addWidget(splitter)

    def _build_arc_tab(self):
        layout = QVBoxLayout(self.arc_tab)

        splitter = QSplitter(Qt.Orientation.Vertical)

        # Top: Main Campaign & Regional Arcs
        top_widget = QWidget()
        top_layout = QHBoxLayout(top_widget)
        top_layout.setContentsMargins(0, 0, 0, 0)

        # Main Campaign Tree
        campaign_group = QGroupBox("🏰 Main Campaign Acts")
        campaign_layout = QVBoxLayout(campaign_group)
        self.tree_campaign_acts = QTreeWidget()
        self.tree_campaign_acts.setHeaderLabels(["Act", "Status", "Progress"])
        self.tree_campaign_acts.setStyleSheet("background: #15152a; color: #d0d0e8;")
        self.tree_campaign_acts.setColumnWidth(0, 200)
        self.tree_campaign_acts.setColumnWidth(1, 100)
        campaign_layout.addWidget(self.tree_campaign_acts)
        top_layout.addWidget(campaign_group)

        # Regional Arcs Tree
        regional_group = QGroupBox("🗺️ Regional Arcs")
        regional_layout = QVBoxLayout(regional_group)
        self.tree_regional_arcs = QTreeWidget()
        self.tree_regional_arcs.setHeaderLabels(["Region", "Act", "Progress"])
        self.tree_regional_arcs.setStyleSheet("background: #15152a; color: #d0d0e8;")
        self.tree_regional_arcs.setColumnWidth(0, 200)
        regional_layout.addWidget(self.tree_regional_arcs)
        top_layout.addWidget(regional_group)

        splitter.addWidget(top_widget)

        # Bottom: Faction & Character Arcs
        bottom_widget = QWidget()
        bottom_layout = QHBoxLayout(bottom_widget)
        bottom_layout.setContentsMargins(0, 0, 0, 0)

        # Faction Arcs
        faction_group = QGroupBox("🏛️ Faction Arcs")
        faction_layout = QVBoxLayout(faction_group)
        self.tree_faction_arcs = QTreeWidget()
        self.tree_faction_arcs.setHeaderLabels(["Faction", "State", "Progress"])
        self.tree_faction_arcs.setStyleSheet("background: #15152a; color: #d0d0e8;")
        self.tree_faction_arcs.setColumnWidth(0, 200)
        faction_layout.addWidget(self.tree_faction_arcs)
        bottom_layout.addWidget(faction_group)

        # Character Arcs
        char_group = QGroupBox("👤 Character Arcs")
        char_layout = QVBoxLayout(char_group)
        self.tree_character_arcs = QTreeWidget()
        self.tree_character_arcs.setHeaderLabels(["NPC", "Phase", "Progress", "Milestones"])
        self.tree_character_arcs.setStyleSheet("background: #15152a; color: #d0d0e8;")
        self.tree_character_arcs.setColumnWidth(0, 180)
        self.tree_character_arcs.setColumnWidth(1, 100)
        self.tree_character_arcs.setColumnWidth(2, 80)
        char_layout.addWidget(self.tree_character_arcs)
        bottom_layout.addWidget(char_group)

        splitter.addWidget(bottom_widget)
        splitter.setSizes([350, 350])
        layout.addWidget(splitter)

    def _build_logs_tab(self):
        layout = QVBoxLayout(self.logs_tab)

        # Report generation
        report_group = QGroupBox("📜 Campaign Director Report")
        report_layout = QVBoxLayout(report_group)

        btn_bar = QHBoxLayout()
        self.btn_generate_report = QPushButton("📄 Generate Report")
        self.btn_generate_report.setStyleSheet(
            "background-color: #6c63ff; color: white; font-weight: bold; "
            "padding: 8px 16px; font-size: 13px; border-radius: 4px;"
        )
        self.btn_generate_report.clicked.connect(self._generate_report)
        btn_bar.addWidget(self.btn_generate_report)

        self.btn_refresh = QPushButton("🔄 Refresh View")
        self.btn_refresh.setStyleSheet(
            "background-color: #4caf50; color: white; font-weight: bold; "
            "padding: 8px 16px; font-size: 13px; border-radius: 4px;"
        )
        self.btn_refresh.clicked.connect(self.refresh_all)
        btn_bar.addWidget(self.btn_refresh)

        btn_bar.addStretch()
        report_layout.addLayout(btn_bar)

        self.txt_report = QTextEdit()
        self.txt_report.setReadOnly(True)
        self.txt_report.setStyleSheet(
            "background: #0d0d1a; color: #c0c0e0; font-family: 'Consolas', monospace; font-size: 12px;"
        )
        report_layout.addWidget(self.txt_report)

        layout.addWidget(report_group)

        # Diversity Overview
        diversity_group = QGroupBox("🎲 Diversity Overview")
        diversity_layout = QVBoxLayout(diversity_group)
        self.lbl_diversity = QLabel("Overall Diversity: —")
        self.lbl_diversity.setStyleSheet("color: #d0d0e8; font-size: 14px; font-weight: bold;")
        diversity_layout.addWidget(self.lbl_diversity)

        self.txt_diversity = QTextEdit()
        self.txt_diversity.setReadOnly(True)
        self.txt_diversity.setMaximumHeight(150)
        self.txt_diversity.setStyleSheet(
            "background: #15152a; color: #d0d0e8; font-size: 12px;"
        )
        diversity_layout.addWidget(self.txt_diversity)
        layout.addWidget(diversity_group)

    # ══════════════════════════════════════════════════════════════════
    #  GUI ACTIONS
    # ══════════════════════════════════════════════════════════════════

    def refresh_all(self):
        """Reload latest campaign health data and update all views."""
        try:
            # Try to load existing health data
            health_path = self.service.db.db_dir / "campaign_health.json"
            if health_path.exists():
                with open(health_path, "r", encoding="utf-8") as f:
                    snapshot = json.load(f)
                self._update_metrics(snapshot.get("metrics", {}))
                self._update_pacing(snapshot.get("pacing_state", "rising_action"))
                self._update_directives(snapshot.get("active_directives", []))
                self._update_arcs(snapshot.get("arc_progress", {}))

            # Update constraints
            self._update_constraints(self.service.get_active_constraints())

            # Update mode selector
            mode_map = {"observation": 0, "recommendation": 1, "control": 2}
            self.combo_mode.setCurrentIndex(mode_map.get(self.service.mode, 0))

        except Exception:
            pass

    def _run_director_tick(self):
        """Execute a Campaign Director tick and update all views."""
        try:
            result = self.service.run_director_tick()

            health = result.get("health", {})
            pacing = result.get("pacing", {})
            diversity = result.get("diversity", {})
            arcs = result.get("arcs", {})

            # Update all views
            self._update_metrics(health.get("metrics", {}))
            self._update_pacing(pacing.get("current_state", "rising_action"),
                                pacing.get("pacing_signal", 0.0),
                                pacing.get("ticks_in_state", 0))
            self._update_directives(health.get("active_directives", []))
            self._update_constraints(result.get("constraints", []))
            self._update_arcs(health.get("arc_progress", {}))
            self._update_full_arcs(arcs)
            self._update_diversity(diversity)

            # Success message
            mode = result.get("mode", "observation")
            n_recs = len(result.get("recommendations", []))
            n_constraints = len(result.get("constraints", []))

            QMessageBox.information(
                self,
                "Campaign Director Update",
                f"Director tick completed successfully!\n\n"
                f"Mode: {mode.upper()}\n"
                f"Pacing: {pacing.get('current_state', 'unknown').replace('_', ' ').title()}\n"
                f"Recommendations: {n_recs}\n"
                f"Constraints: {n_constraints}"
            )

        except Exception as e:
            QMessageBox.critical(self, "Director Error", f"Campaign Director tick failed: {e}")

    def _on_mode_changed(self, index: int):
        """Handle director mode change."""
        modes = ["observation", "recommendation", "control"]
        if 0 <= index < len(modes):
            selected = modes[index]
            if selected == "control":
                reply = QMessageBox.warning(
                    self,
                    "Control Mode Warning",
                    "Control mode allows the Campaign Director to actively manipulate DM behavior.\n\n"
                    "This mode should only be enabled after validating Observation and Recommendation modes.\n\n"
                    "Proceed?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No,
                )
                if reply != QMessageBox.StandardButton.Yes:
                    mode_map = {"observation": 0, "recommendation": 1, "control": 2}
                    self.combo_mode.setCurrentIndex(mode_map.get(self.service.mode, 0))
                    return
            self.service.set_mode(selected)

    def _generate_report(self):
        """Generate and display the campaign director report."""
        try:
            report = self.service.generate_report()
            self.txt_report.setPlainText(report)
            QMessageBox.information(
                self,
                "Report Generated",
                "Campaign Director report has been compiled and saved to campaign_director_report.md"
            )
        except Exception as e:
            QMessageBox.critical(self, "Report Error", f"Failed to generate report: {e}")

    # ══════════════════════════════════════════════════════════════════
    #  VIEW UPDATE HELPERS
    # ══════════════════════════════════════════════════════════════════

    def _update_metrics(self, metrics: Dict):
        """Update the metric bar displays."""
        status_map = {
            "tension": lambda v: "🔴 High" if v >= 0.7 else ("⚠️ Moderate" if v >= 0.4 else "✅ Low"),
            "conflict": lambda v: "🔴 High" if v >= 0.7 else ("⚠️ Moderate" if v >= 0.4 else "✅ Low"),
            "mystery": lambda v: "📈 High" if v >= 0.7 else ("📊 Moderate" if v >= 0.3 else "📉 Low"),
            "quest_density": lambda v: "📈 High" if v >= 0.7 else ("📊 Moderate" if v >= 0.3 else "📉 Low"),
            "event_frequency": lambda v: "📈 High" if v >= 0.7 else ("📊 Moderate" if v >= 0.3 else "📉 Low"),
            "faction_pressure": lambda v: "🔴 High" if v >= 0.7 else ("⚠️ Moderate" if v >= 0.4 else "✅ Low"),
            "world_stability": lambda v: "✅ Stable" if v >= 0.7 else ("⚠️ Unstable" if v >= 0.4 else "🔴 Critical"),
        }

        for key, bar in self.metric_bars.items():
            value = metrics.get(key, 0.0)
            status_fn = status_map.get(key, lambda v: "—")
            bar.set_value(value, status_fn(value))

    def _update_pacing(self, state: str, signal: float = 0.0, ticks: int = 0):
        """Update pacing state labels."""
        state_display = state.replace("_", " ").title()
        state_colors = {
            "Rising Action": "#ff9800",
            "Climax": "#e91e63",
            "Falling Action": "#9c27b0",
            "Resolution": "#4caf50",
            "Cooldown": "#2196f3",
        }
        color = state_colors.get(state_display, "#e0e0ff")
        self.lbl_pacing_state.setText(f"Phase: {state_display}")
        self.lbl_pacing_state.setStyleSheet(f"color: {color}; font-size: 16px; font-weight: bold;")
        self.lbl_pacing_signal.setText(f"Pacing Signal: {signal:.3f}")
        self.lbl_pacing_ticks.setText(f"Ticks in State: {ticks}")

    def _update_directives(self, directives: list):
        """Update the directives tree."""
        self.tree_directives.clear()
        for d in directives:
            item = QTreeWidgetItem()
            priority = d.get("priority", "low")
            icon = {"low": "🟢", "medium": "🟡", "high": "🟠", "critical": "🔴"}.get(priority, "⚪")
            item.setText(0, f"{icon} {priority.upper()}")
            item.setText(1, d.get("type", "pacing"))
            item.setText(2, d.get("description", ""))
            self.tree_directives.addTopLevelItem(item)

    def _update_constraints(self, constraints: list):
        """Update the constraints tree."""
        self.tree_constraints.clear()
        if not constraints:
            item = QTreeWidgetItem()
            item.setText(0, "No active constraints")
            item.setText(1, "DM operating freely")
            item.setText(2, "—")
            self.tree_constraints.addTopLevelItem(item)
            return

        for c in constraints:
            item = QTreeWidgetItem()
            item.setText(0, c.get("type", "unknown"))
            item.setText(1, c.get("description", ""))
            item.setText(2, f"{c.get('duration_ticks', 0)} ticks")
            self.tree_constraints.addTopLevelItem(item)

    def _update_arcs(self, arc_progress: dict):
        """Update arc progression from health snapshot."""
        # Main campaign
        self.tree_campaign_acts.clear()
        main = arc_progress.get("main_campaign", {})
        if main:
            item = QTreeWidgetItem()
            item.setText(0, f"Current Act: {main.get('act', '?')}")
            item.setText(1, "Active")
            item.setText(2, f"{main.get('progress', 0):.1%}")
            self.tree_campaign_acts.addTopLevelItem(item)

        # Regional arcs
        self.tree_regional_arcs.clear()
        for r in arc_progress.get("regional_arcs", []):
            item = QTreeWidgetItem()
            item.setText(0, r.get("region", "?"))
            item.setText(1, r.get("act", "?"))
            item.setText(2, f"{r.get('progress', 0):.1%}")
            self.tree_regional_arcs.addTopLevelItem(item)

        # Faction arcs
        self.tree_faction_arcs.clear()
        for f in arc_progress.get("faction_arcs", []):
            item = QTreeWidgetItem()
            item.setText(0, f.get("faction", "?"))
            item.setText(1, f.get("state", "?").title())
            item.setText(2, f"{f.get('progress', 0):.1%}")
            self.tree_faction_arcs.addTopLevelItem(item)

        # Character arcs
        self.tree_character_arcs.clear()
        for c in arc_progress.get("character_arcs", []):
            item = QTreeWidgetItem()
            item.setText(0, c.get("name", "?"))
            item.setText(1, c.get("arc_phase", "?").title())
            item.setText(2, f"{c.get('progress', 0):.1%}")
            item.setText(3, "")
            self.tree_character_arcs.addTopLevelItem(item)

    def _update_full_arcs(self, arcs: dict):
        """Update arc trees with full detail from director tick result."""
        # Full campaign acts
        self.tree_campaign_acts.clear()
        for act in arcs.get("acts", []):
            item = QTreeWidgetItem()
            status_icon = {"completed": "✅", "active": "🔵", "pending": "⚪"}.get(act.get("status", "pending"), "⚪")
            item.setText(0, f"{status_icon} {act.get('name', act.get('act_id', '?'))}")
            item.setText(1, act.get("status", "pending").title())
            item.setText(2, f"{act.get('progress', 0):.1%}")
            self.tree_campaign_acts.addTopLevelItem(item)

        # Full regional arcs
        self.tree_regional_arcs.clear()
        for r in arcs.get("regional_arcs", []):
            item = QTreeWidgetItem()
            item.setText(0, r.get("region", "?"))
            item.setText(1, r.get("act", "?"))
            item.setText(2, f"{r.get('progress', 0):.1%}")
            self.tree_regional_arcs.addTopLevelItem(item)

        # Full faction arcs
        self.tree_faction_arcs.clear()
        for f in arcs.get("faction_arcs", []):
            item = QTreeWidgetItem()
            state_icon = {
                "dormant": "⚪", "rising": "📈", "peak": "🔺", "declining": "📉", "resolved": "✅"
            }.get(f.get("arc_state", "dormant"), "⚪")
            item.setText(0, f.get("faction", "?"))
            item.setText(1, f"{state_icon} {f.get('arc_state', '?').title()}")
            item.setText(2, f"{f.get('progress', 0):.1%}")

            # Add key events as children
            for ke in f.get("key_events", []):
                child = QTreeWidgetItem(item)
                child.setText(0, "")
                child.setText(1, "Event")
                child.setText(2, ke)

            self.tree_faction_arcs.addTopLevelItem(item)

        # Full character arcs
        self.tree_character_arcs.clear()
        for c in arcs.get("character_arcs", []):
            item = QTreeWidgetItem()
            phase_icon = {
                "introduction": "🌱", "development": "📖", "crisis": "⚡", "resolution": "🌅"
            }.get(c.get("arc_phase", "introduction"), "❓")
            item.setText(0, c.get("name", "?"))
            item.setText(1, f"{phase_icon} {c.get('arc_phase', '?').title()}")
            item.setText(2, f"{c.get('progress', 0):.1%}")
            item.setText(3, ", ".join(c.get("milestones", [])))
            self.tree_character_arcs.addTopLevelItem(item)

    def _update_diversity(self, diversity: dict):
        """Update diversity overview."""
        overall = diversity.get("overall_diversity", 0.0)
        self.lbl_diversity.setText(f"Overall Diversity: {overall:.1%}")

        lines = []
        quest = diversity.get("quest_diversity", {})
        if quest:
            lines.append(f"Quest Diversity: {quest.get('diversity_score', 0):.1%}  |  Total: {quest.get('total_quests', 0)}")
            if quest.get("missing_types"):
                lines.append(f"  Missing types: {', '.join(quest['missing_types'][:3])}")

        faction = diversity.get("faction_coverage", {})
        if faction:
            lines.append(f"Faction Coverage: {faction.get('diversity_score', 0):.1%}")
            if faction.get("neglected_factions"):
                lines.append(f"  Neglected: {', '.join(faction['neglected_factions'][:3])}")

        npc = diversity.get("npc_engagement", {})
        if npc:
            lines.append(f"NPC Engagement: {npc.get('engagement_score', 0):.1%}  |  Active: {npc.get('active_npcs', 0)}/{npc.get('total_npcs', 0)}")

        event = diversity.get("event_variety", {})
        if event:
            lines.append(f"Event Variety: {event.get('variety_score', 0):.1%}")
            if event.get("repetition_detected"):
                lines.append(f"  ⚠️ Repetition detected: {event.get('dominant_type', '?')}")

        self.txt_diversity.setPlainText("\n".join(lines))

    def clear(self):
        """Reset view state."""
        for bar in self.metric_bars.values():
            bar.set_value(0.0, "—")
        self.lbl_pacing_state.setText("Phase: Rising Action")
        self.lbl_pacing_signal.setText("Pacing Signal: 0.000")
        self.lbl_pacing_ticks.setText("Ticks in State: 0")
        self.tree_directives.clear()
        self.tree_constraints.clear()
        self.tree_campaign_acts.clear()
        self.tree_regional_arcs.clear()
        self.tree_faction_arcs.clear()
        self.tree_character_arcs.clear()
        self.txt_report.clear()
        self.txt_diversity.clear()
        self.lbl_diversity.setText("Overall Diversity: —")


    def load_data(self, data=None):
        """Adapter for Workspace interface."""
        pass

