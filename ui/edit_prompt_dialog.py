from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, QLabel

class EditPromptDialog(QDialog):
    def __init__(self, prompt_text: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Prompt")
        self.resize(500, 300)
        self.new_text = prompt_text
        self.accepted_action = False
        self._build_ui(prompt_text)

    def _build_ui(self, prompt_text: str) -> None:
        layout = QVBoxLayout(self)
        
        lbl = QLabel("Edit your prompt:")
        lbl.setStyleSheet("font-weight: bold;")
        layout.addWidget(lbl)
        
        self._text_edit = QTextEdit()
        self._text_edit.setPlainText(prompt_text)
        self._text_edit.setStyleSheet("background-color: #1e1e38; color: #d0d0e8;")
        layout.addWidget(self._text_edit)
        
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        
        btn_regen = QPushButton("Regenerate")
        btn_regen.setStyleSheet("background-color: #6c63ff; color: white; font-weight: bold;")
        btn_regen.clicked.connect(self._on_regenerate)
        
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_regen)
        layout.addLayout(btn_row)

    def _on_regenerate(self) -> None:
        text = self._text_edit.toPlainText().strip()
        if text:
            self.new_text = text
            self.accepted_action = True
            self.accept()
