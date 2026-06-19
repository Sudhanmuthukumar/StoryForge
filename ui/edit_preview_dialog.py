from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QTextEdit, QSplitter, QApplication
)

class EditPreviewDialog(QDialog):
    def __init__(self, original_text: str, new_text: str, is_append: bool = False, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AI Edit Preview")
        self.resize(800, 500)
        self.original_text = original_text
        self.new_text = new_text
        self.is_append = is_append
        self.action_result = "keep" # "replace", "keep", "copy"
        
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Original
        orig_widget = QWidget()
        orig_layout = QVBoxLayout(orig_widget)
        orig_layout.setContentsMargins(0,0,0,0)
        orig_label = QLabel("Original Text")
        orig_label.setStyleSheet("font-weight: bold; color: #a0a0c0;")
        orig_text = QTextEdit()
        orig_text.setReadOnly(True)
        orig_text.setPlainText(self.original_text)
        orig_text.setStyleSheet("background-color: #1e1e38; color: #d0d0e8;")
        orig_layout.addWidget(orig_label)
        orig_layout.addWidget(orig_text)
        
        # New
        new_widget = QWidget()
        new_layout = QVBoxLayout(new_widget)
        new_layout.setContentsMargins(0,0,0,0)
        new_label = QLabel("AI Edited Text")
        new_label.setStyleSheet("font-weight: bold; color: #6c63ff;")
        new_text_widget = QTextEdit()
        new_text_widget.setReadOnly(True)
        new_text_widget.setPlainText(self.new_text)
        new_text_widget.setStyleSheet("background-color: #1e1e38; color: #ffffff;")
        new_layout.addWidget(new_label)
        new_layout.addWidget(new_text_widget)
        
        splitter.addWidget(orig_widget)
        splitter.addWidget(new_widget)
        layout.addWidget(splitter, stretch=1)
        
        # Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        
        btn_copy = QPushButton("📄 Copy")
        btn_copy.clicked.connect(self._on_copy)
        
        btn_keep = QPushButton("❌ Cancel")
        btn_keep.clicked.connect(self._on_keep)
        
        btn_label = "✅ Insert" if self.is_append else "✅ Replace"
        btn_replace = QPushButton(btn_label)
        btn_replace.setObjectName("btnSave")
        btn_replace.setStyleSheet("background-color: #6c63ff; color: white; font-weight: bold;")
        btn_replace.clicked.connect(self._on_replace)
        
        btn_row.addWidget(btn_copy)
        btn_row.addWidget(btn_keep)
        btn_row.addWidget(btn_replace)
        
        layout.addLayout(btn_row)

    def _on_copy(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.new_text)
        self.action_result = "copy"
        self.accept()

    def _on_keep(self):
        self.action_result = "keep"
        self.reject()

    def _on_replace(self):
        self.action_result = "replace"
        self.accept()
