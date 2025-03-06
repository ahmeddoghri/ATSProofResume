"""
Unit tests for app routes module.
"""
import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import os
import tempfile
import json
from fastapi.testclient import TestClient
from fastapi import UploadFile
from app.routes import router
from app.state import jobs_db, progress_status, OUTPUT_DIR
from app.main import app


class TestAppRoutes(unittest.TestCase):
    """Test cases for app routes."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = TestClient(app)
        
        # Create a temporary directory for testing
        self.temp_dir = tempfile.TemporaryDirectory()
        
        # Create a sample resume file
        self.resume_path = os.path.join(self.temp_dir.name, "test_resume.docx")
        with open(self.resume_path, "wb") as f:
            f.write(b"Test resume content")
        
        # Clear jobs_db and progress_status
        jobs_db.clear()
        progress_status.clear()

    def tearDown(self):
        """Clean up after tests."""
        # Clean up temporary directory
        self.temp_dir.cleanup()
        
        # Clear jobs_db and progress_status
        jobs_db.clear()
        progress_status.clear()

    @patch('app.routes.process_resume_job')
    @patch('app.routes.JobPostingScraper')
    def test_upload_resume(self, mock_scraper_class, mock_process_job):
        """Test uploading a resume."""
        # Mock the scraper to return valid job data
        mock_scraper = MagicMock()
        mock_scraper.scrape_job_posting.return_value = {
            "company": "Test Company",
            "job_title": "Software Engineer",
            "job_description": "Test description",
            "location": "Remote",
            "date_posted": "2023-01-01",
            "salary": "$100,000 - $150,000"
        }
        mock_scraper_class.return_value = mock_scraper

        # Create a test file
        with open(self.resume_path, "rb") as f:
            # Submit a job
            response = self.client.post(
                "/upload_resume/",
                data={
                    "job_link": "https://example.com/job",
                    "model": "gpt-4",
                    "temperature": 0.7,
                    "api_key": "test_api_key"
                },
                files={"file": ("test_resume.docx", f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
            )
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("redirect_url", data)
        self.assertIn("job_id", data)
        
        # Verify job was added to jobs_db
        job_id = data["job_id"]
        self.assertIn(job_id, jobs_db)
        
        # Verify progress status was initialized
        self.assertIn(job_id, progress_status)
        self.assertEqual(progress_status[job_id], 0)
        
        # Verify process_resume_job was called
        mock_process_job.assert_called_once()

    def test_get_progress(self):
        """Test getting job progress."""
        # Add a test job
        job_id = "test_job_123"
        jobs_db[job_id] = {
            "job_title": "Software Engineer",
            "company_name": "Test Company",
            "job_description": "This is a test job description."
        }
        progress_status[job_id] = 50
        
        # Get job status
        response = self.client.get(f"/progress/{job_id}")
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["progress"], 50)
        
        # Test with completed job
        progress_status[job_id] = 100
        response = self.client.get(f"/progress/{job_id}")
        data = response.json()
        self.assertEqual(data["progress"], 100)
        
        # Test with error
        progress_status[job_id] = -1
        response = self.client.get(f"/progress/{job_id}")
        data = response.json()
        self.assertEqual(data["progress"], -1)
        
        # Test with non-existent job
        response = self.client.get("/progress/non_existent_job")
        self.assertEqual(response.status_code, 404)

    @patch('starlette.responses.FileResponse.__init__', return_value=None)
    @patch('starlette.responses.FileResponse.__call__', return_value=MagicMock(
        status_code=200,
        headers={"content-type": "application/zip"},
        body=b"test content"
    ))
    @patch('os.stat')
    @patch('os.path.exists')
    def test_download_file(self, mock_exists, mock_stat, mock_file_response_call, mock_file_response_init):
        """Test downloading a file."""
        # Setup mocks
        mock_exists.return_value = True
        mock_stat.return_value = MagicMock(st_size=100, st_mtime=1234567890)
        
        # Test with a valid filename
        response = self.client.get("/download/test_file.zip")
        
        # Verify the response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"test content")
        
        # Verify FileResponse was initialized with the correct path
        mock_file_response_init.assert_called()


if __name__ == '__main__':
    unittest.main() 