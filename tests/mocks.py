"""
Mock objects for testing.
"""
from unittest.mock import MagicMock

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