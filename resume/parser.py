"""
Handles parsing and extracting information from resumes
"""
import logging
import re
import os


class ResumeParser:
    """Handles parsing and extracting information from resumes"""
    
    @staticmethod
    def parse_date(date_str):
        """
        Parse a date string in MM/YYYY format and return a tuple (year, month) for sorting.
        
        Args:
            date_str: A date string in MM/YYYY format
            
        Returns:
            tuple: (year, month) for sorting purposes
        """
        try:
            if '/' in date_str:
                month, year = date_str.strip().split('/')
                return (int(year), int(month))
            else:
                # Handle case where only year is provided
                return (int(date_str.strip()), 1)
        except (ValueError, IndexError):
            # Return a default value for unparseable dates
            logging.warning(f"Could not parse date: {date_str}")
            return (0, 0)
    
    def extract_contact_info(self, resume_text):
        """
        Extract contact information from resume text.
        
        Args:
            resume_text: The text content of the resume
            
        Returns:
            dict: Dictionary containing contact information
        """
        contact_info = {}
        
        # Extract email
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        email_match = re.search(email_pattern, resume_text)
        if email_match:
            contact_info["email"] = email_match.group()
        
        # Extract phone number
        phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
        phone_match = re.search(phone_pattern, resume_text)
        if phone_match:
            contact_info["phone"] = phone_match.group()
        
        # Extract LinkedIn
        linkedin_pattern = r'linkedin\.com/in/[A-Za-z0-9_-]+'
        linkedin_match = re.search(linkedin_pattern, resume_text)
        if linkedin_match:
            contact_info["linkedin"] = linkedin_match.group()
        
        return contact_info
    
    def extract_skills(self, resume_text):
        """
        Extract skills from resume text.
        
        Args:
            resume_text: The text content of the resume
            
        Returns:
            list: List of skills extracted from the resume
        """
        # Find the skills section
        skills_section_pattern = r'SKILLS.*?(?=\n\n[A-Z]+|\Z)'
        skills_section_match = re.search(skills_section_pattern, resume_text, re.DOTALL)
        
        if not skills_section_match:
            return []
        
        skills_section = skills_section_match.group()
        
        # Extract individual skills
        # This is a simplified approach - in a real implementation, you might use NLP
        # or a predefined list of skills to match against
        skills = []
        
        # Look for skills listed with commas or on separate lines
        skill_lines = skills_section.split('\n')[1:]  # Skip the "SKILLS" header
        for line in skill_lines:
            if ':' in line:
                # Handle "Category: Skill1, Skill2, Skill3" format
                category_skills = line.split(':', 1)[1].strip()
                for skill in category_skills.split(','):
                    skill = skill.strip()
                    if skill and len(skill) > 1:  # Avoid empty or single-character skills
                        skills.append(skill)
            else:
                # Handle skills listed on separate lines
                for skill in line.split(','):
                    skill = skill.strip()
                    if skill and len(skill) > 1:
                        skills.append(skill)
        
        return skills
    
    def extract_education(self, resume_text):
        """
        Extract education information from resume text.
        
        Args:
            resume_text: The text content of the resume
            
        Returns:
            list: List of education entries
        """
        # Find the education section
        education_section_pattern = r'EDUCATION.*?(?=\n\n[A-Z]+|\Z)'
        education_section_match = re.search(education_section_pattern, resume_text, re.DOTALL)
        
        if not education_section_match:
            return []
        
        education_section = education_section_match.group()
        
        # Split into individual education entries
        education_entries = []
        
        # Skip the "EDUCATION" header
        education_lines = education_section.split('\n')[1:]
        
        current_entry = ""
        for line in education_lines:
            line = line.strip()
            if line:
                if current_entry and (re.match(r'^[A-Z]', line) or re.search(r'\d{4}', line)):
                    # This looks like a new degree line
                    if current_entry.strip():
                        education_entries.append(current_entry.strip())
                    current_entry = line
                else:
                    current_entry += " " + line
        
        # Add the last entry if it exists
        if current_entry.strip():
            education_entries.append(current_entry.strip())
        
        return education_entries
    
    def extract_experience(self, resume_text):
        """
        Extract work experience from resume text.
        
        Args:
            resume_text: The text content of the resume
            
        Returns:
            list: List of dictionaries containing work experience details
        """
        # Find the experience section
        experience_section_pattern = r'EXPERIENCE\s*\n(.*?)(?=\n\s*[A-Z]+\s*\n|\Z)'
        experience_section_match = re.search(experience_section_pattern, resume_text, re.DOTALL)
        
        if not experience_section_match:
            return []
        
        experience_section = experience_section_match.group(1)
        
        # Split into individual job entries
        experience_entries = []
        
        # Parse job entries - looking for company names followed by title and dates
        job_pattern = r'([A-Za-z][\w\s&]+)\s*\n([^•\n]+\|\s*[^•\n]+)(.*?)(?=\n[A-Za-z][\w\s&]+\s*\n|\Z)'
        job_matches = re.finditer(job_pattern, experience_section, re.DOTALL)
        
        for job_match in job_matches:
            company = job_match.group(1).strip()
            title_dates = job_match.group(2).strip().split('|')
            
            title = title_dates[0].strip()
            dates = title_dates[1].strip() if len(title_dates) > 1 else ""
            
            responsibilities_text = job_match.group(3).strip()
            responsibilities = [line.strip() for line in responsibilities_text.split('\n') 
                               if line.strip() and (line.strip().startswith('•') or line.strip().startswith('-'))]
            
            # Create job entry
            job = {
                "company": company,
                "title": title,
                "dates": dates,
                "responsibilities": responsibilities
            }
            
            experience_entries.append(job)
        
        return experience_entries
    
    def parse_resume(self, file_path):
        """
        Parse a resume file and extract structured information.
        
        Args:
            file_path: Path to the resume file
            
        Returns:
            dict: Dictionary containing structured resume information
        """
        if not os.path.exists(file_path):
            logging.error(f"File not found: {file_path}")
            return {}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                resume_text = file.read()
            
            # Extract summary - make the pattern more specific
            summary_pattern = r'SUMMARY\s*\n(.*?)(?=\n\s*SKILLS|\n\s*EXPERIENCE|\Z)'
            summary_match = re.search(summary_pattern, resume_text, re.DOTALL)
            summary = summary_match.group(1).strip() if summary_match else ""
            
            # Build structured resume
            parsed_resume = {
                "contact_info": self.extract_contact_info(resume_text),
                "summary": summary,
                "skills": self.extract_skills(resume_text),
                "education": self.extract_education(resume_text),
                "experience": self.extract_experience(resume_text)
            }
            
            return parsed_resume
            
        except Exception as e:
            logging.error(f"Error parsing resume: {e}")
            return {}
