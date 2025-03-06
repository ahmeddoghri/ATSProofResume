"""
Unit tests for the resume parser module.
"""
import unittest
from unittest.mock import patch, MagicMock, mock_open
import os
import tempfile
from resume.parser import ResumeParser


class TestResumeParser(unittest.TestCase):
    """Test cases for ResumeParser class."""

    def setUp(self):
        """Set up test fixtures."""
        self.parser = ResumeParser()
        
        # Sample resume content
        self.sample_resume_text = """
        John Doe
        john.doe@example.com | 555-123-4567 | linkedin.com/in/johndoe
        
        SUMMARY
        Experienced software engineer with 5+ years in web development.
        
        SKILLS
        Programming: Python, JavaScript, TypeScript, Java
        Web Technologies: React, Node.js, HTML5, CSS3
        Cloud: AWS, Docker, Kubernetes
        Tools: Git, Jenkins, JIRA
        
        EXPERIENCE
        
        Tech Solutions Inc.
        Senior Developer | Jan 2020 - Present
        • Led development of cloud-native applications using microservices architecture
        • Implemented CI/CD pipelines reducing deployment time by 40%
        • Mentored junior developers and conducted code reviews
        
        Web Innovations
        Software Engineer | Mar 2018 - Dec 2019
        • Developed responsive web applications using React and Node.js
        • Collaborated with UX designers to implement user-friendly interfaces
        
        EDUCATION
        
        Master of Computer Science, University of Technology, 2018
        Bachelor of Science in Software Engineering, State University, 2016
        """
    
    def test_extract_contact_info(self):
        """Test extracting contact information."""
        contact_info = self.parser.extract_contact_info(self.sample_resume_text)
        
        # Verify contact information was extracted correctly
        self.assertIn("email", contact_info)
        self.assertEqual(contact_info["email"], "john.doe@example.com")
        self.assertIn("phone", contact_info)
        self.assertEqual(contact_info["phone"], "555-123-4567")
        self.assertIn("linkedin", contact_info)
        self.assertEqual(contact_info["linkedin"], "linkedin.com/in/johndoe")
    
    def test_extract_skills(self):
        """Test extracting skills."""
        skills = self.parser.extract_skills(self.sample_resume_text)
        
        # Verify skills were extracted correctly
        self.assertIn("Python", skills)
        self.assertIn("JavaScript", skills)
        self.assertIn("React", skills)
        self.assertIn("AWS", skills)
        self.assertIn("Docker", skills)
        self.assertGreaterEqual(len(skills), 10)
    
    def test_extract_education(self):
        """Test extracting education information."""
        education = self.parser.extract_education(self.sample_resume_text)
        
        # Verify education was extracted correctly
        self.assertEqual(len(education), 2)
        self.assertIn("Master of Computer Science", education[0])
        self.assertIn("University of Technology", education[0])
        self.assertIn("2018", education[0])
        self.assertIn("Bachelor of Science", education[1])
        self.assertIn("State University", education[1])
        self.assertIn("2016", education[1])
    
    def test_extract_experience(self):
        """Test extracting work experience."""
        experience = self.parser.extract_experience(self.sample_resume_text)
        
        # Verify experience was extracted correctly
        self.assertEqual(len(experience), 2)
        
        # First job
        self.assertIn("company", experience[0])
        self.assertEqual(experience[0]["company"], "Tech Solutions Inc.")
        self.assertIn("title", experience[0])
        self.assertEqual(experience[0]["title"], "Senior Developer")
        self.assertIn("dates", experience[0])
        self.assertEqual(experience[0]["dates"], "Jan 2020 - Present")
        self.assertIn("responsibilities", experience[0])
        self.assertGreaterEqual(len(experience[0]["responsibilities"]), 2)
        
        # Second job
        self.assertIn("company", experience[1])
        self.assertEqual(experience[1]["company"], "Web Innovations")
        self.assertIn("title", experience[1])
        self.assertEqual(experience[1]["title"], "Software Engineer")
        self.assertIn("dates", experience[1])
        self.assertEqual(experience[1]["dates"], "Mar 2018 - Dec 2019")
    
    def test_parse_resume(self):
        """Test parsing a complete resume."""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(suffix='.txt', mode='w+') as temp_file:
            temp_file.write(self.sample_resume_text)
            temp_file.flush()
            
            parsed_resume = self.parser.parse_resume(temp_file.name)
            
            # Verify the parsed resume structure
            self.assertIn("contact_info", parsed_resume)
            self.assertIn("skills", parsed_resume)
            self.assertIn("education", parsed_resume)
            self.assertIn("experience", parsed_resume)
            self.assertIn("summary", parsed_resume)
            
            # Verify content
            self.assertEqual(parsed_resume["contact_info"]["email"], "john.doe@example.com")
            self.assertIn("Python", parsed_resume["skills"])
            self.assertGreaterEqual(len(parsed_resume["education"]), 2)
            self.assertGreaterEqual(len(parsed_resume["experience"]), 2)
            self.assertIn("software engineer", parsed_resume["summary"].lower())


if __name__ == '__main__':
    unittest.main() 