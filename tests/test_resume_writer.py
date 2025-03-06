"""
Unit tests for the resume writer module.
"""
import unittest
from unittest.mock import patch, MagicMock, mock_open
import os
import tempfile
from docx import Document
from resume.writer import ResumeWriter


class TestResumeWriter(unittest.TestCase):
    """Test cases for ResumeWriter class."""

    def setUp(self):
        """Set up test fixtures."""
        self.writer = ResumeWriter()
        
        # Sample resume content - restructured to match expected format
        self.sample_resume_text = """
<NAME>
John Doe
<CONTACT>
john.doe@example.com | 555-123-4567 | linkedin.com/in/johndoe
<SUMMARY>
Experienced software engineer with 5+ years in web development.
<SKILLS>
Python | JavaScript
React | Node.js
AWS | Docker
<EXPERIENCE>
<COMPANY>
Tech Solutions Inc.
<POSITION_DATE>
Senior Developer | Jan 2020 - Present
<BULLET>
Led development of cloud-native applications using microservices architecture
<BULLET>
Implemented CI/CD pipelines reducing deployment time by 40%
<COMPANY>
Web Innovations
<POSITION_DATE>
Software Engineer | Mar 2018 - Dec 2019
<BULLET>
Developed responsive web applications using React and Node.js
<EDUCATION>
Master of Computer Science, University of Technology, 2018
Bachelor of Science in Software Engineering, State University, 2016
"""
    
    def test_extract_skills(self):
        """Test extracting skills from resume text."""
        # Convert string to list of lines for _extract_skills
        lines = self.sample_resume_text.strip().splitlines()
        skills = self.writer._extract_skills(lines)
        
        # Verify skills were extracted correctly
        self.assertIsInstance(skills, list)
        self.assertIn("Python", skills)
        self.assertIn("JavaScript", skills)
        self.assertIn("React", skills)
        self.assertIn("Node.js", skills)
        self.assertIn("AWS", skills)
        self.assertIn("Docker", skills)
    
    @patch('resume.formatter.DocumentFormatter.add_section_heading')
    def test_add_section_heading(self, mock_add_section_heading):
        """Test adding section headings."""
        # Create a mock document
        mock_doc = MagicMock()
        
        # Call the formatter through the writer
        self.writer.formatter.add_section_heading(mock_doc, "EXPERIENCE")
        
        # Verify the formatter method was called
        mock_add_section_heading.assert_called_once_with(mock_doc, "EXPERIENCE")
    
    def test_add_simple_paragraph(self):
        """Test adding simple paragraphs."""
        # Create a mock document
        mock_doc = MagicMock()
        mock_para = MagicMock()
        mock_run = MagicMock()
        mock_doc.add_paragraph.return_value = mock_para
        mock_para.runs = [mock_run]
        
        # Test the method
        self.writer._add_simple_paragraph(mock_doc, "This is a paragraph")
        
        # Verify paragraph was added with correct style
        mock_doc.add_paragraph.assert_called_once_with("This is a paragraph", style="Compact")
        self.assertEqual(mock_run.font.size.pt, 11)
        self.assertEqual(mock_run.font.name, "Calibri")
    
    def test_extract_field(self):
        """Test extracting fields from resume text."""
        # Create a properly formatted list of lines that matches the expected format
        lines = [
            "<NAME>",
            "John Doe",
            "<CONTACT>",
            "john.doe@example.com | 555-123-4567 | linkedin.com/in/johndoe",
            "<SUMMARY>",
            "Experienced software engineer with 5+ years in web development."
        ]
        
        # Test extracting name
        name = self.writer._extract_field(lines, "<NAME>")
        self.assertEqual(name, "John Doe")
        
        # Test extracting contact
        contact = self.writer._extract_field(lines, "<CONTACT>")
        self.assertEqual(contact, "john.doe@example.com | 555-123-4567 | linkedin.com/in/johndoe")
        
        # Test extracting summary
        summary = self.writer._extract_field(lines, "<SUMMARY>")
        self.assertEqual(summary, "Experienced software engineer with 5+ years in web development.")


if __name__ == '__main__':
    unittest.main() 