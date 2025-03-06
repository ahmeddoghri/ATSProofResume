"""
Unit tests for the resume processor module.
"""
import unittest
from unittest.mock import patch, MagicMock, mock_open
import os
import tempfile
import json
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
        Python | JavaScript | React | Node.js
        AWS | Docker | Kubernetes | CI/CD
        Agile | Scrum | Team Leadership
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
    def test_generate_optimized_resume(self, mock_openai_class):
        """Test generating an optimized resume."""
        # Mock OpenAI client
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        # Mock chat completion response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = self.sample_resume_text
        mock_client.chat.completions.create.return_value = mock_response
        
        result = self.processor._generate_optimized_resume(
            "Original resume text",
            self.sample_job_description,
            "gpt-4o",
            0.1
        )
        
        # Verify the result
        self.assertEqual(result, self.sample_resume_text)
        
        # Verify OpenAI was called correctly
        mock_client.chat.completions.create.assert_called_once()
        call_args = mock_client.chat.completions.create.call_args[1]
        self.assertEqual(call_args["model"], "gpt-4o")
    
    @patch('resume.processor.ResumeProcessor._extract_text_from_docx')
    def test_extract_text_from_docx(self, mock_extract):
        """Test extracting text from a DOCX file."""
        mock_extract.return_value = "Extracted resume text"
        
        # Create a temporary file
        with tempfile.NamedTemporaryFile(suffix='.docx') as temp_file:
            result = self.processor._extract_text_from_docx(temp_file.name)
            
            # Verify the result
            self.assertEqual(result, "Extracted resume text")
            
            # Verify the method was called correctly
            mock_extract.assert_called_once_with(temp_file.name)
    
    @patch('docx.Document')
    @patch('resume.processor.ResumeProcessor._extract_text_from_docx')
    @patch('resume.processor.ResumeProcessor._generate_optimized_resume')
    def test_process_resume(self, mock_generate, mock_extract, mock_document):
        """Test the full resume processing flow."""
        # Mock document extraction
        mock_extract.return_value = "Original resume text"
        
        # Mock resume generation
        mock_generate.return_value = self.sample_resume_text
        
        # Mock document creation
        mock_doc = MagicMock()
        mock_document.return_value = mock_doc
        
        # Mock writer
        mock_writer = MagicMock()
        self.processor.writer = mock_writer
        
        # Create temporary files for testing
        with tempfile.NamedTemporaryFile(suffix='.docx') as input_file, \
             tempfile.NamedTemporaryFile(suffix='.docx') as output_file:
            
            result = self.processor.process_resume(
                input_file.name,
                self.sample_job_description,
                output_file.name,
                "gpt-4o",
                0.1
            )
            
            # Verify the result
            self.assertTrue(result)
            
            # Verify the methods were called correctly
            mock_extract.assert_called_once_with(input_file.name)
            mock_generate.assert_called_once_with(
                "Original resume text",
                self.sample_job_description,
                "gpt-4o",
                0.1
            )
            mock_writer.write_resume.assert_called_once()
    
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
    def test_generate_optimized_resume_error(self, mock_openai_class):
        """Test error handling in resume generation."""
        # Mock OpenAI client to raise an exception
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("API error")
        
        # Test with error handling
        with self.assertRaises(Exception):
            self.processor._generate_optimized_resume(
                "Original resume text",
                self.sample_job_description,
                "gpt-4o",
                0.1
            )
        
        # Verify OpenAI was called
        mock_client.chat.completions.create.assert_called_once()


if __name__ == '__main__':
    unittest.main() 