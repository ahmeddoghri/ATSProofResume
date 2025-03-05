"""
Handles AI-powered rewriting of resumes
"""
from docx import Document
import shutil
from openai import OpenAI
import os
import logging
from resume.writer import ResumeWriter


class ResumeProcessor:
    """Handles AI-powered rewriting of resumes"""
    
    def __init__(self, api_key=None, writer=None):
        """
        Initialize the ResumeProcessor with an API key and writer.
        
        Args:
            api_key: OpenAI API key
            writer: ResumeWriter instance (or None to create a new one)
        """
        self.api_key = api_key
        self.writer = writer or ResumeWriter()
    
    def process_resume(
        self,
        resume_path, 
        job_description, 
        output_path, 
        model="gpt-4o", 
        temperature=0.1
    ):
        """
        Rewrites a resume to better match a job description.
        
        Args:
            resume_path: Path to the resume DOCX file
            job_description: Job description text
            output_path: Path to save the rewritten resume
            model: OpenAI model to use
            temperature: Temperature for generation
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Extract text from resume
            doc = Document(resume_path)
            resume_text = "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
            
            # Create OpenAI client
            client = OpenAI(api_key=self.api_key)
            
            # Create the prompt with explicit formatting instructions
            prompt = self._create_resume_prompt(job_description, resume_text)
            
            # Make the API call with retry logic
            max_retries = 3
            retry_count = 0
            success = False
            resume_text = ""
            
            while retry_count < max_retries and not success:
                try:
                    logging.info(f"Attempt {retry_count + 1} to rewrite resume using model: {model}")
                    
                    # Handle different model types
                    response = self._get_model_response(client, model, prompt, temperature)
                    
                    # Get the generated resume text
                    resume_text = response.choices[0].message.content.strip()
                    
                    # Validate the format
                    if self._validate_resume_format(resume_text):
                        success = True
                        logging.info("Successfully generated resume with correct format")
                    else:
                        logging.warning("Generated resume has incorrect format. Retrying...")
                        retry_count += 1
                        
                except Exception as api_error:
                    logging.error(f"API error: {str(api_error)}")
                    retry_count += 1
            
            if not success:
                logging.error("Failed to generate properly formatted resume after multiple attempts")
                return False
            
            return self.writer.document_writer(resume_text, output_path, resume_path)
        
        except Exception as e:
            logging.error(f"Resume rewriting failed: {e}")
            # If there's an error, copy the original resume to the output path
            if os.path.exists(resume_path):
                shutil.copy(resume_path, output_path)
            return False
    
    def _get_model_response(self, client, model, prompt, temperature):
        """
        Get response from the appropriate model type.
        
        Args:
            client: OpenAI client
            model: Model name
            prompt: Prompt text
            temperature: Temperature setting
            
        Returns:
            Response from the model
        """
        if model.startswith('o1') or model.startswith('o3') or model.startswith('claude'):
            # For o1/o3/claude models, use a single user message without system message
            return client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": "You are an expert resume writer who tailors resumes to job descriptions. Follow the format instructions exactly.\n\n" + prompt}
                ]
            )
        else:
            # For standard GPT models, use system+user message format
            return client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are an expert resume writer who tailors resumes to job descriptions. Follow the format instructions exactly."},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature
            )
    
    def _create_resume_prompt(self, job_description, resume_text):
        """
        Create the prompt for resume rewriting.
        
        Args:
            job_description: The job description text
            resume_text: The resume text
            
        Returns:
            str: The formatted prompt
        """
        return f"""
        You are an expert resume writer. Rewrite the provided resume to better match the job description.
        
        Focus on:
        1. Highlighting relevant skills and experiences
        2. Using keywords from the job description
        3. Quantifying achievements where possible
        4. Maintaining a professional tone
        5. Keeping the same basic information but rephrasing for impact
        
        JOB DESCRIPTION:
        {job_description}
        
        RESUME:
        {resume_text}
        
        FORMAT YOUR RESPONSE EXACTLY USING THE FOLLOWING TAGS AND STRUCTURE:
        
        <NAME>
        [Full Name]
        
        <CONTACT>
        [Email] | [LinkedIn] | [Phone]
        
        <SUMMARY>
        [Professional summary paragraph]
        
        <SKILLS>
        [Skill 1] | [Skill 4]
        [Skill 2] | [Skill 5]
        [Skill 3] | [Skill 6]
        
        <EXPERIENCE>
        <COMPANY>
        [Company Name] | [Location]
        
        <POSITION_DATE>
        [Position Title] | [MM/YYYY – MM/YYYY]
        
        <BULLET>
        [skill area]: [Achievement with metrics]
        
        <BULLET>
        [skill area]: [Achievement with metrics]
        
        <COMPANY>
        [Company Name] | [Location]
        
        <POSITION_DATE>
        [Position Title] | [MM/YYYY – MM/YYYY]
        
        <BULLET>
        [skill area]: [Achievement with metrics]
        
        <EDUCATION>
        [University Name] | [Location]
        [Degree] – [Honors]
        [GPA information] | [MM/YYYY – MM/YYYY]
        
        [University Name] | [Location]
        [Degree] – [Honors]
        [GPA information] | [MM/YYYY – MM/YYYY]
        
        <VOLUNTEERISM>
        [Organization] | [MM/YYYY – MM/YYYY]
        [Brief description of volunteer work]
        
        [Organization] | [MM/YYYY – MM/YYYY]
        [Brief description of volunteer work]
        
        <OTHER RELEVANT INFORMATION>
        [Category]: [Details]
        
        IMPORTANT: For the skills section, list exactly 6 skills total, arranged in 3 rows with 2 skills per row, separated by the pipe character (|).
        """
    
    def _validate_resume_format(self, resume_text):
        """
        Validate that the generated resume has the correct format.
        
        Args:
            resume_text: The generated resume text
            
        Returns:
            bool: True if the format is valid, False otherwise
        """
        required_tags = [
            "<NAME>", "<CONTACT>", "<SUMMARY>", "<SKILLS>", 
            "<EXPERIENCE>", "<COMPANY>", "<POSITION_DATE>", "<BULLET>",
            "<EDUCATION>"
        ]
        
        # Check if all required tags are present
        if not all(tag in resume_text for tag in required_tags):
            missing_tags = [tag for tag in required_tags if tag not in resume_text]
            logging.warning(f"Generated resume is missing required tags: {missing_tags}")
            return False
            
        # Check if tags are in the correct order
        if not (resume_text.find("<NAME>") < resume_text.find("<CONTACT>") < 
                resume_text.find("<SUMMARY>") < resume_text.find("<SKILLS>") < 
                resume_text.find("<EXPERIENCE>")):
            logging.warning("Generated resume has tags in incorrect order")
            return False
                
        # Validate skills format - should have lines with pipe separators
        skills_section = resume_text.split("<SKILLS>")[1].split("<EXPERIENCE>")[0].strip()
        skills_lines = [line.strip() for line in skills_section.split('\n') if line.strip()]
        
        # Check if we have the right number of skill lines and each has a pipe
        if len(skills_lines) < 3 or not all('|' in line for line in skills_lines[:3]):
            logging.warning("Skills section doesn't match required format")
            return False
            
        return True



