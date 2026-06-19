from PySide6.QtCore import QThread, Signal
from services.ai_service import AIService
import re

class AIVariationWorker(QThread):
    variations_finished = Signal(dict) # Emits { "A": "...", "B": "...", "C": "..." }
    variations_failed = Signal(str)

    def __init__(self, selected_text: str, ranked_context: list, parent=None):
        super().__init__(parent)
        self.selected_text = selected_text
        self.ranked_context = ranked_context
        self.ai_service = AIService()

    def run(self):
        try:
            blocks = self.ranked_context.get("selected", []) if isinstance(self.ranked_context, dict) else self.ranked_context
            raw_output = self.ai_service.generate_variations(self.selected_text, blocks)
            
            # Parse the headers: === VERSION X ===
            variations = {"A": "", "B": "", "C": ""}
            
            pattern = r"===\s*VERSION\s*([A-C])\s*===([^=]+)(?=(?:===\s*VERSION\s*[A-C]\s*===)|$)"
            matches = re.finditer(pattern, raw_output, re.IGNORECASE | re.DOTALL)
            
            found_any = False
            for match in matches:
                version = match.group(1).upper()
                content = match.group(2).strip()
                if version in variations:
                    variations[version] = content
                    found_any = True
                    
            if not found_any:
                # Fallback if model ignored formatting
                variations["A"] = raw_output
                
            self.variations_finished.emit(variations)
        except Exception as e:
            self.variations_failed.emit(str(e))
