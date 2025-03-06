"""
Pytest configuration file.
"""
import os
import sys
import pytest
from unittest.mock import MagicMock

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock JobPostingScraper
class MockJobPostingScraper:
    """Mock implementation of JobPostingScraper for testing."""
    
    def __init__(self, *args, **kwargs):
        """Initialize the mock scraper."""
        self.scrape_job_posting = MagicMock()
        self.scrape_job_posting.return_value = {
            "job_title": "Software Engineer",
            "company_name": "Test Company",
            "job_description": "This is a test job description.",
            "location": "Remote",
            "date_posted": "2023-01-01",
            "salary": "$100,000 - $150,000"
        }

# Mock the job_scraper module
sys.modules['job_scraper'] = MagicMock()
sys.modules['job_scraper'].JobPostingScraper = MockJobPostingScraper

@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    from fastapi.testclient import TestClient
    from app.main import app
    return TestClient(app) 