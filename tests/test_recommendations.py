"""
Unit tests for the recommendations module.
"""
import unittest
from unittest.mock import patch, MagicMock
import json
from recommendations import (
    generate_recommendations,
    _create_recommendations_prompt,
    _get_model_response,
    get_fallback_recommendations
)


class TestRecommendations(unittest.TestCase):
    """Test cases for recommendations generation."""

    def setUp(self):
        """Set up test fixtures."""
        self.api_key = "test_api_key"
        self.job_description = """
        Senior Software Engineer
        
        We are looking for a Senior Software Engineer with experience in Python and cloud technologies.
        Responsibilities include developing microservices, implementing CI/CD pipelines, and leading a team.
        
        Requirements:
        - 5+ years of experience in software development
        - Proficiency in Python and JavaScript
        - Experience with AWS, Docker, and Kubernetes
        - Strong communication and leadership skills
        """
        
        self.resume_text = """
        John Doe
        john.doe@example.com | 555-123-4567
        
        SUMMARY
        Software engineer with 4 years of experience in web development.
        
        SKILLS
        Python, JavaScript, React, Node.js, Git
        
        EXPERIENCE
        Software Engineer, ABC Tech (2019-Present)
        - Developed web applications using React and Node.js
        - Implemented automated testing using Jest
        
        Junior Developer, XYZ Solutions (2018-2019)
        - Assisted in developing front-end components
        - Participated in code reviews
        
        EDUCATION
        Bachelor of Science in Computer Science, State University, 2018
        """
        
        # Sample API response
        self.sample_recommendations = """
        # Resume Improvement Recommendations

        ## Skills Gap Analysis
        
        Your resume shows strong web development skills, but there are several gaps compared to the job requirements:
        
        - **Cloud Technologies**: The job requires AWS, Docker, and Kubernetes experience, which are not mentioned in your resume.
        - **CI/CD Experience**: The job specifically mentions CI/CD pipelines, but your resume doesn't highlight this.
        """
    
    @patch('openai.OpenAI')
    def test_generate_recommendations(self, mock_openai_class):
        """Test generating recommendations."""
        # Mock OpenAI client
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        # Mock chat completion response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = self.sample_recommendations
        mock_client.chat.completions.create.return_value = mock_response
        
        result = generate_recommendations(
            self.job_description,
            self.resume_text,
            self.api_key,
            "gpt-4o",
            0.7
        )
        
        # Verify the result
        self.assertIn("RESUME IMPROVEMENT RECOMMENDATIONS", result)
        self.assertIn("Skills Gap Analysis", result)
        self.assertIn("Cloud Technologies", result)
        
        # Verify OpenAI was called correctly
        mock_client.chat.completions.create.assert_called_once()
        call_args = mock_client.chat.completions.create.call_args[1]
        self.assertEqual(call_args["model"], "gpt-4o")
    
    @patch('openai.OpenAI')
    def test_generate_recommendations_api_error(self, mock_openai_class):
        """Test error handling in recommendations generation."""
        # Mock OpenAI client
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        
        result = generate_recommendations(
            self.job_description,
            self.resume_text,
            self.api_key,
            "gpt-4o",
            0.7
        )
        
        # Verify fallback recommendations were returned
        self.assertIn("RESUME IMPROVEMENT RECOMMENDATIONS", result)
        self.assertIn("Tailor Your Resume to the Job Description", result)
        
        # Verify OpenAI was called
        mock_client.chat.completions.create.assert_called_once()
    
    def test_create_recommendations_prompt(self):
        """Test creating the recommendations prompt."""
        prompt = _create_recommendations_prompt(self.job_description, self.resume_text)
        
        # Verify the prompt structure
        self.assertIn("JOB DESCRIPTION:", prompt)
        self.assertIn(self.job_description, prompt)
        self.assertIn("RESUME:", prompt)
        self.assertIn(self.resume_text, prompt)
        self.assertIn("expert career coach", prompt.lower())
        self.assertIn("skills gaps", prompt.lower())
        self.assertIn("markdown formatting", prompt.lower())
    
    @patch('openai.OpenAI')
    def test_get_model_response_standard_model(self, mock_openai_class):
        """Test getting response from standard GPT model."""
        # Mock OpenAI client
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        
        # Test with standard GPT model
        _get_model_response(mock_client, "gpt-4o", "test prompt", 0.7)
        
        # Verify correct format was used
        mock_client.chat.completions.create.assert_called_once()
        call_args = mock_client.chat.completions.create.call_args[1]
        
        # Check for system+user message format
        messages = call_args["messages"]
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]["role"], "system")
        self.assertEqual(messages[1]["role"], "user")
        self.assertEqual(call_args["temperature"], 0.7)
    
    @patch('openai.OpenAI')
    def test_get_model_response_o1_model(self, mock_openai_class):
        """Test getting response from o1 model."""
        # Mock OpenAI client
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        
        # Test with o1 model
        _get_model_response(mock_client, "o1-preview", "test prompt", 0.7)
        
        # Verify correct format was used
        mock_client.chat.completions.create.assert_called_once()
        call_args = mock_client.chat.completions.create.call_args[1]
        
        # Check for single user message format
        messages = call_args["messages"]
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]["role"], "user")
        
        # Temperature should not be included for o1 models
        self.assertNotIn("temperature", call_args)
    
    def test_get_fallback_recommendations(self):
        """Test getting fallback recommendations."""
        result = get_fallback_recommendations()
        
        # Verify the result
        self.assertIsInstance(result, str)
        self.assertIn("RESUME IMPROVEMENT RECOMMENDATIONS", result)
        self.assertIn("Tailor Your Resume to the Job Description", result)
        self.assertIn("Strengthen Your Professional Summary", result)
        self.assertIn("Quantify Your Achievements", result)
        self.assertIn("Optimize Your Skills Section", result)
        self.assertIn("Improve Formatting and Readability", result)
        self.assertIn("Unable to generate specific recommendations due to an error", result)


if __name__ == '__main__':
    unittest.main() 