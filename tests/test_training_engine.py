import unittest
from unittest.mock import patch
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from services.training_engine import TrainingEngine

class TestTrainingEngine(unittest.TestCase):
    def setUp(self):
        self.engine = TrainingEngine()

    @patch('services.training_engine.TrainingEngine._extract_text')
    def test_case_1_import_txt(self, mock_extract):
        mock_extract.return_value = "This is a simple text. \"Hello\" she said."
        profile = {"documents_processed": 0, "total_words": 0, "themes": {}, "relationship_patterns": {}, "character_patterns": {}, "style_fingerprint": {}, "training_history": []}
        
        updated = self.engine.process_document(Path("dummy.txt"), profile)
        self.assertEqual(updated["documents_processed"], 1)
        self.assertGreater(updated["style_fingerprint"]["dialogue_ratio"], 0.0)

    @patch('services.training_engine.TrainingEngine._extract_text')
    def test_case_2_import_docx(self, mock_extract):
        mock_extract.return_value = "This is a DOCX document."
        profile = {"documents_processed": 0, "total_words": 0, "themes": {}, "relationship_patterns": {}, "character_patterns": {}, "style_fingerprint": {}, "training_history": []}
        
        updated = self.engine.process_document(Path("dummy.docx"), profile)
        self.assertEqual(updated["documents_processed"], 1)

    @patch('services.training_engine.TrainingEngine._extract_text')
    def test_case_3_import_pdf(self, mock_extract):
        mock_extract.return_value = "This is a PDF document."
        profile = {"documents_processed": 0, "total_words": 0, "themes": {}, "relationship_patterns": {}, "character_patterns": {}, "style_fingerprint": {}, "training_history": []}
        
        updated = self.engine.process_document(Path("dummy.pdf"), profile)
        self.assertEqual(updated["documents_processed"], 1)

    @patch('services.training_engine.TrainingEngine._extract_text')
    def test_case_4_multiple_documents(self, mock_extract):
        mock_extract.return_value = "Word."
        profile = {"documents_processed": 0, "total_words": 0, "themes": {}, "relationship_patterns": {}, "character_patterns": {}, "style_fingerprint": {}, "training_history": []}
        
        self.engine.process_document(Path("dummy1.txt"), profile)
        self.engine.process_document(Path("dummy2.txt"), profile)
        self.assertEqual(profile["documents_processed"], 2)

    def test_case_5_unsupported_file(self):
        profile = {"documents_processed": 0, "total_words": 0}
        updated = self.engine.process_document(Path("dummy.exe"), profile)
        self.assertEqual(updated["documents_processed"], 0)  # Should gracefully reject

if __name__ == "__main__":
    unittest.main()
