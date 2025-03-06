"""
Unit tests for the app tasks module.
"""
import unittest
from unittest.mock import patch, MagicMock
import os
import tempfile
import json
from app.tasks import process_resume_job
from app.state import jobs_db, progress_status, OUTPUT_DIR


class TestAppTasks(unittest.TestCase):
    """Test cases for app tasks."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a unique job ID for testing
        self.job_id = "test_job_123"
        
        # Sample job data
        self.job_data = {
            "job_title": "Senior Software Engineer",
            "company": "Test Company",
            "job_text": """
            We are looking for a Senior Software Engineer with experience in Python.
            Requirements:
            - 5+ years of experience in software development
            - Proficiency in Python and JavaScript
            """
        }
        
        # Create a temporary resume file
        self.temp_dir = tempfile.TemporaryDirectory()
        self.resume_path = os.path.join(self.temp_dir.name, "test_resume.docx")
        with open(self.resume_path, "w") as f:
            f.write("Test resume content")
        
        # Create a company directory
        self.company_dir = os.path.join(self.temp_dir.name, "Test_Company")
        os.makedirs(self.company_dir, exist_ok=True)
        
        # Initialize job in jobs_db
        jobs_db[self.job_id] = self.job_data.copy()
        
        # Reset progress status
        if self.job_id in progress_status:
            del progress_status[self.job_id]

    def tearDown(self):
        """Clean up after tests."""
        # Clean up temporary directory
        self.temp_dir.cleanup()
        
        # Clean up job data
        if self.job_id in jobs_db:
            del jobs_db[self.job_id]
        
        # Clean up progress status
        if self.job_id in progress_status:
            del progress_status[self.job_id]

    @patch('app.tasks.ResumeProcessor')
    @patch('app.tasks.generate_recommendations')
    @patch('app.tasks.generate_interview_questions')
    def test_process_resume_job(self, mock_generate_questions, mock_generate_recommendations, mock_processor_class):
        """Test the resume processing job."""
        # Mock the ResumeProcessor instance
        mock_processor = MagicMock()
        mock_processor_class.return_value = mock_processor
        
        # Mock the recommendations
        mock_generate_recommendations.return_value = "Sample recommendations"
        
        # Mock the interview questions
        mock_generate_questions.return_value = {
            "Strategic Questions": ["Question 1", "Question 2"],
            "Technical Questions": ["Question 3", "Question 4"]
        }
        
        # Mock extract_text_from_docx
        with patch('app.tasks.extract_text_from_docx', return_value="Sample resume text"):
            # Mock open function for file writes
            with patch('builtins.open', mock_open()):
                # Mock zipfile
                with patch('zipfile.ZipFile'):
                    # Run the task
                    process_resume_job(
                        self.job_id,
                        self.job_data,
                        self.resume_path,
                        self.company_dir,
                        "gpt-4o",
                        0.1,
                        "test_api_key"
                    )
            
            # Verify progress was updated
            self.assertEqual(progress_status[self.job_id], 100)
            
            # Verify the processor was called correctly
            mock_processor.process_resume.assert_called_once()
            call_args = mock_processor.process_resume.call_args[0]
            self.assertEqual(call_args[0], self.resume_path)  # resume_path
            self.assertEqual(call_args[1], self.job_data["job_text"])  # job_description
            
            # Verify recommendations were generated
            mock_generate_recommendations.assert_called_once_with(
                self.job_data["job_text"],
                "Sample resume text",
                api_key="test_api_key",
                model="gpt-4o",
                temperature=0.1
            )
            
            # Verify interview questions were generated
            mock_generate_questions.assert_called_once_with(
                job_description=self.job_data["job_text"],
                resume_text="Sample resume text",
                company_name="Test Company",
                api_key="test_api_key",
                model="gpt-4o"
            )

    @patch('app.tasks.ResumeProcessor')
    def test_process_resume_job_error(self, mock_processor_class):
        """Test error handling in the resume processing job."""
        # Mock the ResumeProcessor to raise an exception
        mock_processor = MagicMock()
        mock_processor.process_resume.side_effect = Exception("Test error")
        mock_processor_class.return_value = mock_processor
        
        # Run the task
        process_resume_job(
            self.job_id,
            self.job_data,
            self.resume_path,
            self.company_dir,
            "gpt-4o",
            0.1,
            "test_api_key"
        )
        
        # Verify progress status indicates error
        self.assertEqual(progress_status[self.job_id], -1)


if __name__ == '__main__':
    unittest.main() 