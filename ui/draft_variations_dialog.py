from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit, QTabWidget, QApplication, QWidget
)

class DraftVariationsDialog(QDialog):
    def __init__(self, variations: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Draft Variations")
        self.resize(800, 500)
        self.variations = variations
        self.selected_variation_text = ""
        self.action_result = "cancel" # "use", "copy", "cancel"
        
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("QTabWidget::pane { border: 1px solid #3a3a5a; } QTabBar::tab { background: #1e1e38; color: #b0b0c0; padding: 8px 16px; border: 1px solid #3a3a5a; } QTabBar::tab:selected { background: #2a2a4a; color: #ffffff; font-weight: bold; }")
        
        # Tabs
        self.editors = {}
        for version in ["A", "B", "C"]:
            if self.variations.get(version):
                tab = QWidget()
                tab_layout = QVBoxLayout(tab)
                tab_layout.setContentsMargins(0, 0, 0, 0)
                
                text_edit = QTextEdit()
                text_edit.setReadOnly(True)
                text_edit.setPlainText(self.variations[version])
                text_edit.setStyleSheet("background-color: #1e1e38; color: #d0d0e8; border: none;")
                tab_layout.addWidget(text_edit)
                
                self.tabs.addTab(tab, f"Version {version}")
                self.editors[version] = text_edit
                
        layout.addWidget(self.tabs)
        
        # Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        
        btn_cancel = QPushButton("❌ Cancel")
        btn_cancel.clicked.connect(self.reject)
        
        btn_copy = QPushButton("📄 Copy Version")
        btn_copy.clicked.connect(self._on_copy)
        
        btn_use = QPushButton("✅ Use Version")
        btn_use.setObjectName("btnSave")
        btn_use.setStyleSheet("background-color: #6c63ff; color: white; font-weight: bold;")
        btn_use.clicked.connect(self._on_use)
        
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_copy)
        btn_row.addWidget(btn_use)
        
        layout.addLayout(btn_row)

    def _get_active_text(self) -> str:
        idx = self.tabs.currentIndex()
        if idx >= 0:
            version = ["A", "B", "C"][idx]
            return self.variations.get(version, "")
        return ""

    def _on_copy(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self._get_active_text())
        self.action_result = "copy"
        self.accept()

    def _on_use(self):
        self.selected_variation_text = self._get_active_text()
        self.action_result = "use"
        self.accept()
