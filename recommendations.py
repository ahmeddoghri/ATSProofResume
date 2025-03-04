import logging
from openai import OpenAI
from typing import Optional

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def generate_recommendations(
    job_description: str, 
    resume_text: str, 
    api_key: Optional[str] = None, 
    model: str = "gpt-4",
    temperature: float = 0.7
) -> str:
    """
    Generates recommendations for improving the resume based on the job description.
    
    Args:
        job_description: The job description text
        resume_text: The resume text
        api_key: OpenAI API key
        model: The OpenAI model to use (default: "gpt-4")
        temperature: The temperature setting for generation (default: 0.7)
        
    Returns:
        str: Formatted recommendations text
    """
    try:
        # Create OpenAI client
        client = OpenAI(api_key=api_key)
        
        prompt = f"""
        You are an expert career coach and resume writer. Analyze the job description and resume below, then provide specific recommendations to improve the resume.
        
        Focus on:
        1. Skills gaps between the job requirements and the resume
        2. Specific sections that could be improved or added
        3. Keywords that should be included
        4. Formatting suggestions
        5. Content that could be removed or de-emphasized
        
        Provide actionable, specific advice that would help this candidate improve their chances of getting an interview.
        
        Use markdown formatting to make your recommendations more readable:
        - Use **bold** for important points and section headings
        - Use bullet points and numbered lists for organized recommendations
        - Use horizontal rules (---) to separate major sections
        - Use code blocks with ```markdown for example text
        - Use ### for section headers
        
        JOB DESCRIPTION:
        {job_description}
        
        RESUME:
        {resume_text}
        """
        
        # Handle different model requirements
        try:
            logger.info(f"Generating recommendations using model: {model}")
            
            # Check if using o1 or o3 models which have different API requirements
            if model.startswith('o1') or model.startswith('o3') or model.startswith('claude'):
                # For o1/o3/claude models, use a single user message without system message
                # and fixed temperature
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "user", "content": "You are an expert career coach who provides detailed, actionable advice to job seekers. Use markdown formatting to make your recommendations more readable.\n\n" + prompt}
                    ]
                )
            else:
                # For standard GPT models, use system+user message format
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": "You are an expert career coach who provides detailed, actionable advice to job seekers. Use markdown formatting to make your recommendations more readable."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=temperature
                )
            
            # Format the recommendations
            recommendations = response.choices[0].message.content.strip()
            
            # Add a header to the recommendations
            formatted_recommendations = "RESUME IMPROVEMENT RECOMMENDATIONS\n"
            formatted_recommendations += "================================\n\n"
            formatted_recommendations += recommendations
            
            return formatted_recommendations
            
        except Exception as api_error:
            logger.error(f"API error: {str(api_error)}")
            return get_fallback_recommendations()
        
    except Exception as e:
        logger.error(f"Recommendation generation failed: {e}")
        return get_fallback_recommendations()

def get_fallback_recommendations() -> str:
    """
    Returns fallback recommendations if the API call fails.
    
    Returns:
        str: Formatted fallback recommendations
    """
    return """RESUME IMPROVEMENT RECOMMENDATIONS
================================

1. Tailor Your Resume to the Job Description
   - Customize your resume for each application by highlighting relevant skills and experiences
   - Use keywords from the job description to pass through Applicant Tracking Systems (ATS)
   - Prioritize experiences that directly relate to the job requirements

2. Strengthen Your Professional Summary
   - Create a compelling 3-4 line summary that highlights your most relevant qualifications
   - Include your years of experience, key skills, and notable achievements
   - Avoid generic statements and focus on what makes you uniquely qualified

3. Quantify Your Achievements
   - Add metrics and specific results to demonstrate your impact (e.g., "increased sales by 20%")
   - Use action verbs to begin each bullet point
   - Focus on outcomes rather than just listing responsibilities

4. Optimize Your Skills Section
   - Create a dedicated skills section that includes both technical and soft skills
   - Organize skills by category for better readability
   - Include proficiency levels for technical skills when relevant

5. Improve Formatting and Readability
   - Use a clean, professional design with consistent formatting
   - Ensure adequate white space to avoid a cluttered appearance
   - Use bullet points rather than paragraphs for work experience
   - Keep your resume to 1-2 pages depending on experience level

Unable to generate specific recommendations due to an error. Please try again later.""" 