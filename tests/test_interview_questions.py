"""
Unit tests for the interview_questions module.
"""
import unittest
from unittest.mock import patch, MagicMock
import json
from interview_questions import (
    generate_interview_questions,
    parse_questions_from_text,
    get_fallback_questions
)


class TestInterviewQuestions(unittest.TestCase):
    """Test cases for interview questions generation."""

    def setUp(self):
        """Set up test fixtures."""
        self.api_key = "test_api_key"
        self.job_description = "We are looking for a Senior Software Engineer..."
        self.resume_text = "John Doe\nSenior Software Engineer with 5+ years experience..."
        self.company_name = "TechCorp"
        
        # Sample API response in text format
        self.sample_text_response = """
        STRATEGIC/BUSINESS QUESTIONS
        1. Given TechCorp's recent expansion into cloud services, how do you see this affecting your strategic priorities in the next year?
        2. How does TechCorp differentiate its products from competitors like Amazon and Microsoft?
        3. What metrics do you use to measure success for your engineering teams?
        4. How does this role contribute to TechCorp's broader strategic objectives?
        5. What do you see as the most significant market opportunity for TechCorp that isn't yet being fully addressed?

        TECHNICAL/DOMAIN QUESTIONS
        1. How is TechCorp approaching the integration of AI into its core products?
        2. What's your approach to balancing technical innovation with stability and reliability?
        3. How does TechCorp handle technical debt management across its product lines?
        4. What cloud infrastructure decisions have been most impactful for TechCorp's scalability?
        5. How do you ensure security is built into the development process?
        """
        
        # Sample API response in JSON format
        self.sample_json_response = json.dumps({
            "Strategic/Business Questions": [
                "Given TechCorp's recent expansion into cloud services, how do you see this affecting your strategic priorities in the next year?",
                "How does TechCorp differentiate its products from competitors like Amazon and Microsoft?",
                "What metrics do you use to measure success for your engineering teams?",
                "How does this role contribute to TechCorp's broader strategic objectives?",
                "What do you see as the most significant market opportunity for TechCorp that isn't yet being fully addressed?"
            ],
            "Technical/Domain Questions": [
                "How is TechCorp approaching the integration of AI into its core products?",
                "What's your approach to balancing technical innovation with stability and reliability?",
                "How does TechCorp handle technical debt management across its product lines?",
                "What cloud infrastructure decisions have been most impactful for TechCorp's scalability?",
                "How do you ensure security is built into the development process?"
            ],
            "Role-Specific Questions": [
                "What would you consider the most challenging aspect of this role?",
                "How does decision-making authority work for this position?",
                "What does success look like for this role in the first 6-12 months?",
                "How does this role collaborate with other teams or departments?",
                "What specific problems are you hoping the person in this role will solve?"
            ],
            "Culture/Team Questions": [
                "How would you describe the team's approach to handling disagreements?",
                "What aspects of TechCorp's culture are you most proud of?",
                "How has the team's working style evolved over the past year?",
                "How do you support work-life balance while maintaining high performance?",
                "What's your approach to professional development and growth for team members?"
            ],
            "Growth/Future Questions": [
                "How do you see this role evolving as TechCorp grows?",
                "What learning opportunities would be available to help me grow?",
                "How does TechCorp approach internal mobility and career progression?",
                "What emerging skills do you anticipate becoming increasingly important?",
                "How does TechCorp support employees in staying ahead of industry trends?"
            ]
        })
    
    @patch('openai.OpenAI')
    def test_generate_interview_questions_success(self, mock_openai_class):
        """Test successful generation of interview questions."""
        # Mock OpenAI client
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        # Mock chat completion response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = self.sample_text_response
        mock_client.chat.completions.create.return_value = mock_response
        
        result = generate_interview_questions(
            self.job_description,
            self.resume_text,
            self.company_name,
            self.api_key,
            "gpt-4o"
        )
        
        # Verify the result structure
        self.assertIsInstance(result, dict)
        self.assertIn("Strategic/Business Questions", result)
        self.assertIn("Technical/Domain Questions", result)
        
        # Verify questions were extracted correctly
        strategic_questions = result["Strategic/Business Questions"]
        self.assertEqual(len(strategic_questions), 5)
        self.assertIn("TechCorp", strategic_questions[0])
        
        # Verify OpenAI was called correctly
        mock_client.chat.completions.create.assert_called_once()
        call_args = mock_client.chat.completions.create.call_args[1]
        self.assertEqual(call_args["model"], "gpt-4o")
    
    @patch('openai.OpenAI')
    def test_generate_interview_questions_api_error(self, mock_openai_class):
        """Test handling of API errors."""
        # Mock OpenAI client to raise an exception
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        
        result = generate_interview_questions(
            self.job_description,
            self.resume_text,
            self.company_name,
            self.api_key,
            "gpt-4o"
        )
        
        # Verify fallback questions were returned
        self.assertIsInstance(result, dict)
        self.assertIn("Strategic/Business Questions", result)
        self.assertEqual(len(result["Strategic/Business Questions"]), 5)
        
        # Verify OpenAI was called
        mock_client.chat.completions.create.assert_called_once()
    
    def test_parse_questions_from_text(self):
        """Test parsing questions from text format."""
        result = parse_questions_from_text(self.sample_text_response, self.company_name)
        
        # Verify the result structure
        self.assertIsInstance(result, dict)
        self.assertIn("Strategic/Business Questions", result)
        self.assertIn("Technical/Domain Questions", result)
        
        # Verify questions were extracted correctly
        strategic_questions = result["Strategic/Business Questions"]
        self.assertEqual(len(strategic_questions), 5)
        self.assertIn("TechCorp", strategic_questions[0])
    
    def test_parse_questions_from_json(self):
        """Test parsing questions from JSON format."""
        result = parse_questions_from_text(self.sample_json_response, self.company_name)
        
        # Verify the result structure
        self.assertIsInstance(result, dict)
        self.assertIn("Strategic/Business Questions", result)
        self.assertIn("Technical/Domain Questions", result)
        
        # Verify questions were extracted correctly
        strategic_questions = result["Strategic/Business Questions"]
        self.assertEqual(len(strategic_questions), 5)
        self.assertIn("TechCorp", strategic_questions[0])
    
    def test_parse_questions_incomplete_text(self):
        """Test parsing incomplete text with missing categories."""
        incomplete_text = """
        STRATEGIC/BUSINESS QUESTIONS
        1. Question one about strategy?
        2. Question two about business?
        
        TECHNICAL/DOMAIN QUESTIONS
        1. Technical question one?
        """
        
        result = parse_questions_from_text(incomplete_text, self.company_name)
        
        # Verify all categories are present
        self.assertIn("Strategic/Business Questions", result)
        self.assertIn("Technical/Domain Questions", result)
        self.assertIn("Role-Specific Questions", result)
        self.assertIn("Culture/Team Questions", result)
        self.assertIn("Growth/Future Questions", result)
        
        # Verify partial categories were filled with fallbacks
        self.assertEqual(len(result["Strategic/Business Questions"]), 5)
        self.assertEqual(len(result["Technical/Domain Questions"]), 5)
    
    def test_get_fallback_questions(self):
        """Test getting fallback questions."""
        result = get_fallback_questions(self.company_name)
        
        # Verify the result structure
        self.assertIsInstance(result, dict)
        self.assertIn("Strategic/Business Questions", result)
        self.assertIn("Technical/Domain Questions", result)
        self.assertIn("Role-Specific Questions", result)
        self.assertIn("Culture/Team Questions", result)
        self.assertIn("Growth/Future Questions", result)
        
        # Verify company name is included in questions
        strategic_questions = result["Strategic/Business Questions"]
        self.assertTrue(any(self.company_name in q for q in strategic_questions))


if __name__ == '__main__':
    unittest.main() 