"""
Pytest configuration file.
"""
import os
import sys
import pytest
from unittest.mock import MagicMock

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Store the original module and class
original_job_scraper_module = None
if 'job_scraper' in sys.modules:
    original_job_scraper_module = sys.modules['job_scraper']

# Mock JobPostingScraper
class MockJobPostingScraper:
    """Mock implementation of JobPostingScraper for testing."""
    
    def __init__(self, *args, **kwargs):
        """Initialize the mock scraper."""
        self.scrape_job_posting = MagicMock()
        self.scrape_job_posting.return_value = {
            "job_title": "Software Engineer",
            "company": "Test Company",  # Changed from company_name to company
            "job_text": "This is a test job description.",  # Changed from job_description to job_text
            "location": "Remote",
            "date_posted": "2023-01-01",
            "salary": "$100,000 - $150,000"
        }
        self.user_agent = "Mozilla/5.0"
        self.api_key = "test_api_key"

# Create a mock module
mock_job_scraper = MagicMock()
mock_job_scraper.JobPostingScraper = MockJobPostingScraper

# Mock the job_scraper module by default
sys.modules['job_scraper'] = mock_job_scraper

@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    from fastapi.testclient import TestClient
    from app.main import app
    return TestClient(app)

@pytest.fixture
def no_mock_job_scraper():
    """
    Fixture to skip mocking of JobPostingScraper.
    This allows tests to use the real implementation when needed.
    """
    # Restore the original module if it exists
    if original_job_scraper_module:
        sys.modules['job_scraper'] = original_job_scraper_module
    else:
        # If there was no original module, remove the mock to allow importing the real one
        del sys.modules['job_scraper']
    
    # This fixture yields control to the test
    yield
    
    # After the test completes, restore the mock
    sys.modules['job_scraper'] = mock_job_scraper 