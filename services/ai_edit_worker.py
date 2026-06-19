from PySide6.QtCore import QThread, Signal
from services.ai_service import AIService

class AIEditWorker(QThread):
    edit_finished = Signal(str, str) # Emits original_text, new_text
    edit_failed = Signal(str)

    def __init__(self, action: str, selected_text: str, ranked_context: list, parent=None):
        super().__init__(parent)
        self.action = action
        self.selected_text = selected_text
        self.ranked_context = ranked_context
        self.ai_service = AIService()

    def run(self):
        try:
            # We can optionally pass context blocks down the line
            blocks = self.ranked_context.get("selected", []) if isinstance(self.ranked_context, dict) else self.ranked_context
            new_text = self.ai_service.generate_edit(self.action, self.selected_text, blocks)
            self.edit_finished.emit(self.selected_text, new_text)
        except Exception as e:
            self.edit_failed.emit(str(e))
