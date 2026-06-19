import unittest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from services.ai_service import AIService
import ollama
from httpx import ConnectError

class TestAIService(unittest.TestCase):
    def setUp(self):
        self.ai = AIService(model="test_model")

    @patch('ollama.chat')
    def test_case_1_mock_response(self, mock_chat):
        mock_chat.return_value = {"message": {"content": "This is a test response"}}
        resp = self.ai.generate_response("Hello", [])
        self.assertEqual(resp, "This is a test response")

    @patch('ollama.chat')
    def test_case_2_connection_error(self, mock_chat):
        mock_chat.side_effect = ConnectError("Connection refused")
        resp = self.ai.generate_response("Hello", [])
        self.assertIn("Ollama is not running", resp)

    @patch('ollama.chat')
    def test_case_3_model_missing(self, mock_chat):
        # Create a mock ResponseError with status_code 404
        class MockResponseError(ollama.ResponseError):
            def __init__(self):
                self.status_code = 404
        
        mock_chat.side_effect = MockResponseError()
        resp = self.ai.generate_response("Hello", [])
        self.assertIn("Model not found", resp)
        self.assertIn("ollama pull test_model", resp)

    def test_case_4_prompt_construction(self):
        blocks = [{"source_type": "characters", "source": "Story", "content": "Arjun is cool."}]
        prompt = self.ai.build_prompt("Who is Arjun?", blocks)
        self.assertIn("Arjun is cool.", prompt)
        self.assertIn("Who is Arjun?", prompt)
        self.assertIn("=== CONTEXT ===", prompt)
        self.assertIn("=== USER ===", prompt)

    @patch('ollama.chat')
    def test_case_5_empty_context(self, mock_chat):
        mock_chat.return_value = {"message": {"content": "No context response"}}
        resp = self.ai.generate_response("Hello", [])
        self.assertEqual(resp, "No context response")

if __name__ == "__main__":
    unittest.main()
