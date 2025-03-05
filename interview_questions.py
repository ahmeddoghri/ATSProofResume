"""
Generates interview questions based on job description and resume.
"""
import logging
from openai import OpenAI
from typing import List, Dict, Any, Optional
import json
import re

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def generate_interview_questions(
    job_description: str, 
    resume_text: str, 
    company_name: str,
    api_key: Optional[str] = None,
    model: str = "gpt-4o"
) -> Dict[str, List[str]]:
    """
    Generate smart interview questions based on job description and resume.
    
    Args:
        job_description: Full job description text
        resume_text: Full resume text
        company_name: Name of the company
        api_key: OpenAI API key
        model: OpenAI model to use
        
    Returns:
        dict: Categories of interview questions
    """
    try:
        client = OpenAI(api_key=api_key)
        
        # Create a simplified prompt that doesn't require web crawling
        prompt = f"""
        Create insightful, thought-provoking questions for a job candidate to ask during an interview.
        
        Company: {company_name}
        
        Job Description:
        {job_description[:3000]}  # Limit length to avoid token issues
        
        Candidate's Resume:
        {resume_text[:3000]}  # Limit length to avoid token issues
        
        Generate 5 questions in each of these categories:
        
        1. Strategic/Business Questions - Demonstrate understanding of the company's market position, challenges, and opportunities
        2. Technical/Domain Questions - Show deep expertise in the technical aspects of the role without being pedantic
        3. Role-Specific Questions - Reveal sophisticated understanding of the position's challenges and impact
        4. Culture/Team Questions - Demonstrate interest in team dynamics and working relationships
        5. Growth/Future Questions - Show forward thinking and long-term commitment
        
        The questions should:
        - Be specific to this company and role (not generic)
        - Demonstrate the candidate's knowledge without being arrogant
        - Invite a thoughtful response rather than a yes/no answer
        - Be phrased professionally and respectfully
        - Impress the interviewer with their insight and depth
        - Occasionally be slightly challenging or contrarian (but always respectful)
        
        Format your response as follows:

        STRATEGIC/BUSINESS QUESTIONS
        1. [First question]
        2. [Second question]
        3. [Third question]
        4. [Fourth question]
        5. [Fifth question]

        TECHNICAL/DOMAIN QUESTIONS
        1. [First question]
        2. [Second question]
        3. [Third question]
        4. [Fourth question]
        5. [Fifth question]

        And so on for each category.
        
        Use markdown formatting for emphasis where appropriate:
        - Use **bold** for important terms or concepts
        - Use *italics* for subtle emphasis
        - Use bullet points for lists within questions if needed
        """
        
        # Determine which approach to use based on model
        try:
            logger.info(f"Generating interview questions using model: {model}")
            
            # For newer models that support system messages
            if not (model.startswith('o1') or model.startswith('o3') or model.startswith('claude')):
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": "You are an expert interview coach who creates sophisticated, insightful questions for job candidates. Use markdown formatting for emphasis where appropriate."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7
                )
            else:
                # For models that don't support system messages or specific temperature
                response = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": "You are an expert interview coach who creates sophisticated, insightful questions for job candidates. Use markdown formatting for emphasis where appropriate.\n\n" + prompt}]
                )
            
            # Parse the response
            content = response.choices[0].message.content
            logger.info("Successfully received response from OpenAI")
            
            # Parse the structured text format
            return parse_questions_from_text(content, company_name)
            
        except Exception as api_error:
            logger.error(f"API error: {str(api_error)}")
            # Return fallback questions
            return get_fallback_questions(company_name)
            
    except Exception as e:
        logger.error(f"Error generating interview questions: {str(e)}")
        return get_fallback_questions(company_name)

def parse_questions_from_text(content: str, company_name: str) -> Dict[str, List[str]]:
    """
    Parse questions from the text response.
    
    Args:
        content: Text response from the API
        company_name: Name of the company for fallback questions
        
    Returns:
        dict: Categories of interview questions
    """
    # Initialize result structure
    result = {
        "Strategic/Business Questions": [],
        "Technical/Domain Questions": [],
        "Role-Specific Questions": [],
        "Culture/Team Questions": [],
        "Growth/Future Questions": []
    }
    
    # Try to parse as JSON first
    try:
        json_result = json.loads(content)
        # Check if the result has the expected structure
        if all(key in json_result for key in result.keys()):
            return json_result
        
        # If JSON doesn't have the right structure, fall through to text parsing
        logger.info("JSON response doesn't have expected structure, falling back to text parsing")
    except json.JSONDecodeError:
        logger.info("Response is not valid JSON, parsing as text")
    
    # Parse the text format
    current_category = None
    
    # Map various possible category headers to our standard categories
    category_mapping = {
        "STRATEGIC": "Strategic/Business Questions",
        "BUSINESS": "Strategic/Business Questions",
        "STRATEGIC/BUSINESS": "Strategic/Business Questions",
        "TECHNICAL": "Technical/Domain Questions",
        "DOMAIN": "Technical/Domain Questions",
        "TECHNICAL/DOMAIN": "Technical/Domain Questions",
        "ROLE": "Role-Specific Questions",
        "ROLE-SPECIFIC": "Role-Specific Questions",
        "CULTURE": "Culture/Team Questions",
        "TEAM": "Culture/Team Questions",
        "CULTURE/TEAM": "Culture/Team Questions",
        "GROWTH": "Growth/Future Questions",
        "FUTURE": "Growth/Future Questions",
        "GROWTH/FUTURE": "Growth/Future Questions"
    }
    
    # Process each line
    for line in content.split('\n'):
        line = line.strip()
        if not line:
            continue
            
        # Check if this is a category header
        upper_line = line.upper()
        for key, category in category_mapping.items():
            if key in upper_line:
                current_category = category
                break
                
        # If we have a category and this looks like a question
        if current_category:
            # Check if line starts with a number or bullet
            question_match = re.match(r'^(\d+\.|\*|\-)\s*(.*)', line)
            if question_match:
                question = question_match.group(2).strip()
                if question.endswith('?') and len(result[current_category]) < 5:
                    result[current_category].append(question)
            # Or if it's just a question without numbering
            elif line.endswith('?') and not any(key in upper_line for key in category_mapping):
                if len(result[current_category]) < 5:
                    result[current_category].append(line)
    
    # Check if we have enough questions in each category
    for category, questions in result.items():
        if len(questions) < 5:
            # Fill in missing questions with fallbacks
            fallbacks = get_fallback_questions(company_name)
            while len(questions) < 5:
                fallback_index = len(questions)
                if fallback_index < len(fallbacks[category]):
                    questions.append(fallbacks[category][fallback_index])
                else:
                    questions.append(f"What are your thoughts on {category.lower().replace('questions', '').strip()} at {company_name}?")
    
    return result

def get_fallback_questions(company_name: str) -> Dict[str, List[str]]:
    """
    Get fallback questions if generation fails.
    
    Args:
        company_name: Name of the company
        
    Returns:
        dict: Categories of fallback questions
    """
    return {
        "Strategic/Business Questions": [
            f"Given {company_name}'s position in the market, what do you see as your biggest strategic challenges in the next year?",
            f"How does {company_name} differentiate itself from competitors in this space?",
            "What metrics do you use to measure success for this area of the business?",
            "How does this role contribute to the company's broader strategic objectives?",
            "What do you see as the most significant market opportunity that isn't yet being fully addressed?"
        ],
        "Technical/Domain Questions": [
            "What technologies or tools are you currently using that you're most excited about?",
            "How do you balance technical innovation with stability and reliability?",
            "What's your approach to technical debt management?",
            "How do you ensure technical decisions align with business outcomes?",
            "What technical challenges has your team found most interesting recently?"
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
            "What aspects of the company culture are you most proud of?",
            "How has the team's working style evolved over the past year?",
            "How do you support work-life balance while maintaining high performance?",
            "What's your approach to professional development and growth for team members?"
        ],
        "Growth/Future Questions": [
            "How do you see this role evolving as the company grows?",
            "What learning opportunities would be available to help me grow?",
            "How does the company approach internal mobility and career progression?",
            "What emerging skills do you anticipate becoming increasingly important?",
            "How does the company support employees in staying ahead of industry trends?"
        ]
    } 