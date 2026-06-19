from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, 
                             QTableWidget, QTableWidgetItem, QHeaderView, QLabel)
from PySide6.QtCore import Qt
from modules.research_lab.services.telemetry_service import TelemetryService

class ResearchDashboardView(QWidget):
    def __init__(self):
        super().__init__()
        self.telemetry = TelemetryService()
        self._init_ui()
        self.load_data()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("<b>Research Lab Analytics & Rankings</b>")
        header.setStyleSheet("font-size: 16px; margin-bottom: 10px;")
        layout.addWidget(header)
        
        # Tabs for different telemetry views
        self.tabs = QTabWidget()
        
        # Tab 1: Pattern Performance
        self.pattern_tab = QWidget()
        self._init_pattern_tab()
        self.tabs.addTab(self.pattern_tab, "Pattern Performance")
        
        # Tab 2: Evaluation History
        self.eval_tab = QWidget()
        self._init_eval_tab()
        self.tabs.addTab(self.eval_tab, "Evaluation History")
        
        layout.addWidget(self.tabs)

    def _init_pattern_tab(self):
        layout = QVBoxLayout(self.pattern_tab)
        
        self.pattern_table = QTableWidget()
        self.pattern_table.setColumnCount(4)
        self.pattern_table.setHorizontalHeaderLabels(["Pattern ID", "Usage Count", "Avg Eval Delta", "Success Score"])
        self.pattern_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.pattern_table)

    def _init_eval_tab(self):
        layout = QVBoxLayout(self.eval_tab)
        
        self.eval_table = QTableWidget()
        self.eval_table.setColumnCount(5)
        self.eval_table.setHorizontalHeaderLabels(["Timestamp", "Job ID", "Base Score", "Adapter Score", "Improvement %"])
        self.eval_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.eval_table)

    def load_data(self):
        # Load Pattern Performance
        patterns = self.telemetry.read_db("pattern_performance.json")
        # Sort by success score descending
        patterns.sort(key=lambda x: x.get("success_score", 0), reverse=True)
        
        self.pattern_table.setRowCount(len(patterns))
        for row, p in enumerate(patterns):
            self.pattern_table.setItem(row, 0, QTableWidgetItem(str(p.get("pattern_id"))))
            self.pattern_table.setItem(row, 1, QTableWidgetItem(str(p.get("usage_count", 0))))
            self.pattern_table.setItem(row, 2, QTableWidgetItem(f"{p.get('avg_eval_delta', 0):.2f}%"))
            self.pattern_table.setItem(row, 3, QTableWidgetItem(f"{p.get('success_score', 5):.1f}/10"))
            
        # Load Evaluation History
        evals = self.telemetry.read_db("evaluation_history.json")
        evals.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        self.eval_table.setRowCount(len(evals))
        for row, e in enumerate(evals):
            self.eval_table.setItem(row, 0, QTableWidgetItem(str(e.get("timestamp"))[:10]))
            self.eval_table.setItem(row, 1, QTableWidgetItem(str(e.get("job_id"))))
            self.eval_table.setItem(row, 2, QTableWidgetItem(str(e.get("base_score"))))
            self.eval_table.setItem(row, 3, QTableWidgetItem(str(e.get("adapter_score"))))
            self.eval_table.setItem(row, 4, QTableWidgetItem(f"{e.get('improvement_pct', 0):.2f}%"))

    def clear(self):
        """Reset telemetry dashboard tables by reloading latest database content."""
        self.load_data()
