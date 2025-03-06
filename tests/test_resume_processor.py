"""
Unit tests for the resume processor module.
"""
import unittest
from unittest.mock import patch, MagicMock, mock_open
import os
import tempfile
from resume.processor import ResumeProcessor


class TestResumeProcessor(unittest.TestCase):
    """Test cases for ResumeProcessor class."""

    def setUp(self):
        """Set up test fixtures."""
        self.api_key = "test_api_key"
        self.processor = ResumeProcessor(api_key=self.api_key)
        
        # Sample resume content
        self.sample_resume_text = """
        <NAME>John Doe</NAME>
        <CONTACT>john.doe@example.com | 555-123-4567 | linkedin.com/in/johndoe</CONTACT>
        <SUMMARY>Experienced software engineer with 5+ years in web development.</SUMMARY>
        <SKILLS>
        Python | JavaScript
        React | Node.js
        AWS | Docker
        </SKILLS>
        <EXPERIENCE>
        <COMPANY>Tech Solutions Inc.</COMPANY>
        <POSITION_DATE>Senior Developer | Jan 2020 - Present</POSITION_DATE>
        <BULLET>Led development of cloud-native applications using microservices architecture</BULLET>
        <BULLET>Implemented CI/CD pipelines reducing deployment time by 40%</BULLET>
        <COMPANY>Web Innovations</COMPANY>
        <POSITION_DATE>Software Engineer | Mar 2018 - Dec 2019</POSITION_DATE>
        <BULLET>Developed responsive web applications using React and Node.js</BULLET>
        </EXPERIENCE>
        <EDUCATION>
        Master of Computer Science, University of Technology, 2018
        Bachelor of Science in Software Engineering, State University, 2016
        </EDUCATION>
        """
        
        # Sample job description
        self.sample_job_description = """
        We are looking for a Senior Software Engineer with experience in Python and cloud technologies.
        Responsibilities include developing microservices, implementing CI/CD pipelines, and leading a team.
        Requirements:
        - 5+ years of experience in software development
        - Proficiency in Python and JavaScript
        - Experience with AWS, Docker, and Kubernetes
        - Strong communication and leadership skills
        """
    
    @patch('openai.OpenAI')
    def test_get_model_response(self, mock_openai_class):
        """Test getting response from the model."""
        # Mock OpenAI client
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        # Mock chat completion response
        mock_response = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        
        # Test with standard GPT model
        self.processor._get_model_response(mock_client, "gpt-4", "test prompt", 0.1)
        
        # Verify OpenAI was called correctly for standard model
        mock_client.chat.completions.create.assert_called_once()
        call_args = mock_client.chat.completions.create.call_args[1]
        self.assertEqual(call_args["model"], "gpt-4")
        self.assertEqual(len(call_args["messages"]), 2)  # System + user message
        
        # Reset mock
        mock_client.chat.completions.create.reset_mock()
        
        # Test with o1/o3/claude model
        self.processor._get_model_response(mock_client, "o1-preview", "test prompt", 0.1)
        
        # Verify OpenAI was called correctly for o1 model
        mock_client.chat.completions.create.assert_called_once()
        call_args = mock_client.chat.completions.create.call_args[1]
        self.assertEqual(call_args["model"], "o1-preview")
        self.assertEqual(len(call_args["messages"]), 1)  # Only user message
    
    def test_create_resume_prompt(self):
        """Test creating the resume prompt."""
        prompt = self.processor._create_resume_prompt(
            self.sample_job_description,
            "Original resume text"
        )
        
        # Verify the prompt contains key elements
        self.assertIn("JOB DESCRIPTION:", prompt)
        self.assertIn("RESUME:", prompt)
        self.assertIn("Original resume text", prompt)
        self.assertIn("<NAME>", prompt)
        self.assertIn("<SKILLS>", prompt)
        self.assertIn("<EXPERIENCE>", prompt)
    

    def test_validate_resume_format_valid(self):
        """Test validation of a correctly formatted resume."""
        result = self.processor._validate_resume_format(self.sample_resume_text)
        self.assertTrue(result)
    
    def test_validate_resume_format_invalid(self):
        """Test validation of an incorrectly formatted resume."""
        # Missing required tags
        invalid_resume = """
        <NAME>John Doe</NAME>
        <CONTACT>john.doe@example.com</CONTACT>
        Some random text without proper structure
        """
        result = self.processor._validate_resume_format(invalid_resume)
        self.assertFalse(result)
        
        # Incorrect order of tags
        invalid_resume = """
        <SKILLS>Python | JavaScript</SKILLS>
        <NAME>John Doe</NAME>
        <CONTACT>john.doe@example.com</CONTACT>
        <SUMMARY>Experienced software engineer</SUMMARY>
        <EXPERIENCE>...</EXPERIENCE>
        <EDUCATION>...</EDUCATION>
        """
        result = self.processor._validate_resume_format(invalid_resume)
        self.assertFalse(result)
        
        # Invalid skills format
        invalid_resume = """
        <NAME>John Doe</NAME>
        <CONTACT>john.doe@example.com</CONTACT>
        <SUMMARY>Experienced software engineer</SUMMARY>
        <SKILLS>
        Python, JavaScript, React
        </SKILLS>
        <EXPERIENCE>...</EXPERIENCE>
        <EDUCATION>...</EDUCATION>
        """
        result = self.processor._validate_resume_format(invalid_resume)
        self.assertFalse(result)
    
    @patch('openai.OpenAI')
    @patch('logging.error')
    def test_process_resume_api_error(self, mock_logging_error, mock_openai_class):
        """Test error handling in resume processing."""
        # Mock OpenAI client to raise an exception
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("API error")
        
        # Mock document
        mock_doc = MagicMock()
        
        with patch('docx.Document', return_value=mock_doc), \
             patch('os.path.exists', return_value=True), \
             patch('shutil.copy') as mock_copy, \
             tempfile.NamedTemporaryFile(suffix='.docx') as input_file, \
             tempfile.NamedTemporaryFile(suffix='.docx') as output_file:
            
            result = self.processor.process_resume(
                input_file.name,
                self.sample_job_description,
                output_file.name,
                "gpt-4o",
                0.1
            )
            
            # Verify the result is False due to error
            self.assertFalse(result)
            
            # Verify error was logged
            mock_logging_error.assert_called()
            
            # Verify original file was copied to output
            mock_copy.assert_called_once()


if __name__ == '__main__':
    unittest.main() 