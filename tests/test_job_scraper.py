"""
Unit tests for the job_scraper module.
"""
import unittest
from unittest.mock import patch, MagicMock, mock_open
import os
import tempfile
import json
from job_scraper import JobPostingScraper


class TestJobPostingScraper(unittest.TestCase):
    """Test cases for JobPostingScraper class."""

    def setUp(self):
        """Set up test fixtures."""
        self.api_key = "test_api_key"
        self.scraper = JobPostingScraper(api_key=self.api_key)
        self.test_url = "https://example.com/job-posting"
        
    @patch('requests.get')
    def test_scrape_job_posting_success(self, mock_get):
        """Test successful job posting scraping."""
        # Mock the HTTP response
        mock_response = MagicMock()
        mock_response.text = """
        <html>
            <head><title>Software Engineer at TestCorp</title></head>
            <body>
                <h1>Software Engineer</h1>
                <div>TestCorp is looking for a Software Engineer...</div>
            </body>
        </html>
        """
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        # Mock the LLM chain response
        with patch.object(self.scraper, 'llm') as mock_llm:
            mock_llm.invoke.return_value = {
                "company": "TestCorp",
                "job_title": "Software Engineer"
            }
            
            result = self.scraper.scrape_job_posting(self.test_url)
            
            # Verify the result
            self.assertEqual(result["company"], "TestCorp")
            self.assertEqual(result["job_title"], "Software Engineer")
            self.assertIn("job_text", result)
            
            # Verify the HTTP request was made correctly
            mock_get.assert_called_once_with(
                self.test_url, 
                headers={"User-Agent": self.scraper.user_agent}
            )
    
    @patch('requests.get')
    def test_scrape_job_posting_http_error(self, mock_get):
        """Test handling of HTTP errors during scraping."""
        # Mock an HTTP error
        mock_get.side_effect = Exception("Connection error")
        
        result = self.scraper.scrape_job_posting(self.test_url)
        
        # Verify fallback behavior
        self.assertEqual(result["company"], "Unknown_Company")
        self.assertEqual(result["job_title"], "Unknown")
        self.assertIn("Failed to fetch job posting", result["job_text"])
    
    @patch('requests.get')
    def test_scrape_job_posting_extraction_error(self, mock_get):
        """Test handling of extraction errors."""
        # Mock the HTTP response
        mock_response = MagicMock()
        mock_response.text = "<html><body>Minimal content</body></html>"
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        # Mock the LLM chain to raise an exception
        with patch.object(self.scraper, 'llm') as mock_llm:
            mock_llm.invoke.side_effect = Exception("Extraction error")
            
            # Mock the fallback extraction
            with patch.object(self.scraper, '_fallback_extraction') as mock_fallback:
                mock_fallback.return_value = {
                    "company": "Fallback Company",
                    "job_title": "Fallback Title",
                    "job_text": "Fallback text"
                }
                
                result = self.scraper.scrape_job_posting(self.test_url)
                
                # Verify fallback was used
                self.assertEqual(result["company"], "Fallback Company")
                self.assertEqual(result["job_title"], "Fallback Title")
                mock_fallback.assert_called_once()
    
    def test_fallback_extraction(self):
        """Test the fallback extraction method."""
        test_job_text = """
        About Company XYZ
        
        Job Title: Senior Developer
        
        We're looking for a Senior Developer to join our team...
        """
        
        result = self.scraper._fallback_extraction(test_job_text)
        
        # Verify extraction attempt
        self.assertIn("job_text", result)
        self.assertEqual(result["job_text"], test_job_text)
        # Note: exact extraction results will vary based on regex patterns
    
    @patch('selenium.webdriver.Chrome')
    @patch('selenium.webdriver.chrome.service.Service')
    def test_capture_screenshot_success(self, mock_service, mock_chrome):
        """Test successful screenshot capture."""
        # Set up mocks
        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver
        mock_driver.execute_script.side_effect = [1000, 2000]  # width, height
        
        # Create a temporary file for the screenshot
        with tempfile.NamedTemporaryFile(suffix='.png') as temp_file:
            self.scraper.capture_screenshot(self.test_url, temp_file.name)
            
            # Verify driver was configured correctly
            mock_chrome.assert_called_once()
            mock_driver.get.assert_called_once_with(self.test_url)
            mock_driver.save_screenshot.assert_called_once_with(temp_file.name)
            mock_driver.quit.assert_called_once()
    
    @patch('selenium.webdriver.Chrome')
    @patch('selenium.webdriver.chrome.service.Service')
    def test_capture_screenshot_error(self, mock_service, mock_chrome):
        """Test error handling during screenshot capture."""
        # Set up mocks to raise an exception
        mock_chrome.side_effect = Exception("WebDriver error")
        
        # Mock PIL Image
        with patch('PIL.Image.new') as mock_image_new:
            mock_image = MagicMock()
            mock_image_new.return_value = mock_image
            mock_draw = MagicMock()
            
            with patch('PIL.ImageDraw.Draw', return_value=mock_draw):
                # Create a temporary file for the screenshot
                with tempfile.NamedTemporaryFile(suffix='.png') as temp_file:
                    self.scraper.capture_screenshot(self.test_url, temp_file.name)
                    
                    # Verify fallback image was created
                    mock_image_new.assert_called_once()
                    mock_image.save.assert_called_once_with(temp_file.name)


if __name__ == '__main__':
    unittest.main() 