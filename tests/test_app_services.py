"""
Unit tests for the app services module.
"""
import unittest
from app.services import get_model_description


class TestAppServices(unittest.TestCase):
    """Test cases for app services."""

    def test_get_model_description(self):
        """Test getting model descriptions."""
        # Test known models - adjust these based on your actual implementation
        self.assertIsInstance(get_model_description("gpt-4"), str)
        self.assertIsInstance(get_model_description("gpt-4-turbo"), str)
        self.assertIsInstance(get_model_description("gpt-3.5-turbo"), str)
        
        # Test partial matches
        self.assertIsInstance(get_model_description("gpt-4-1106-preview"), str)
        self.assertIsInstance(get_model_description("gpt-4-turbo-preview"), str)
        
        # Test unknown model
        self.assertEqual(
            get_model_description("unknown-model"),
            "OpenAI language model"
        )


if __name__ == '__main__':
    unittest.main() 