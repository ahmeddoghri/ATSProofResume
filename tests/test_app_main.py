"""
Unit tests for the app main module.
"""
import unittest
from unittest.mock import patch, MagicMock, mock_open
import os
import sys
import tempfile

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock JobPostingScraper before importing app
from tests.mocks import MockJobPostingScraper
sys.modules['job_scraper'] = MagicMock()
sys.modules['job_scraper'].JobPostingScraper = MockJobPostingScraper

# Now import the app
from fastapi.testclient import TestClient
from app.main import app


class TestAppMain(unittest.TestCase):
    """Test cases for app main module."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = TestClient(app)
    
    def test_app_initialization(self):
        """Test that the app is properly initialized."""
        # Verify app metadata
        self.assertEqual(app.title, "ATS-Proof Resume Generator")
        self.assertIn("AI-powered tool", app.description)
        self.assertEqual(app.version, "1.0.0")
        
        # Verify routes are registered - update with actual routes
        routes = [route.path for route in app.routes]
        self.assertIn("/upload_resume/", routes)
        self.assertIn("/generate_questions/", routes)
        self.assertIn("/available_models", routes)
        self.assertIn("/", routes)  # Root endpoint
    
    @patch('logging.info')
    def test_startup_event(self, mock_logging):
        """Test the startup event handler."""
        # Get the startup event handler
        startup_handler = None
        for event_handler in app.router.on_startup:
            startup_handler = event_handler
            break
        
        self.assertIsNotNone(startup_handler)
        
        # Call the startup handler
        import asyncio
        loop = asyncio.get_event_loop()
        loop.run_until_complete(startup_handler())
        
        # Verify logging was called
        mock_logging.assert_called_with("Application startup")
        
        # Note: We're not testing makedirs since it's called in app/__init__.py, not in the startup handler

    def test_root_endpoint(self):
        """Test the root endpoint."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.headers["content-type"])


if __name__ == '__main__':
    unittest.main() 