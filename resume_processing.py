from docx import Document
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

from docx import Document
from langchain_openai import ChatOpenAI  # Updated import
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

import re
from docx.enum.text import WD_TAB_ALIGNMENT
import shutil
from openai import OpenAI
import os

def append_ok_to_sentences_with_full_formatting(input_path, output_path):
    """
    Loads a DOCX document from `input_path`, iterates over all paragraphs and their runs,
    and appends ' ok' to the end of each sentence while preserving the original formatting.
    The modified document is saved to `output_path`.
    """
    # Load the document
    doc = Document(input_path)

    # Iterate through all paragraphs
    for para in doc.paragraphs:
        if para.text.strip():  # Process only non-empty paragraphs
            new_runs = []  # Will store the new runs with modifications

            for run in para.runs:
                # Split sentences in the current run (preserving punctuation)
                sentences = run.text.split('. ')
                # Append " ok" to each sentence
                modified_sentences = [sentence if sentence else '' for sentence in sentences]
                modified_text = '. '.join(modified_sentences)

                # Create a new run with the same formatting as the original run
                new_run = para.add_run(modified_text)
                new_run.bold = run.bold
                new_run.italic = run.italic
                new_run.underline = run.underline
                new_run.strike = run.font.strike
                new_run.font.double_strike = run.font.double_strike
                new_run.font.all_caps = run.font.all_caps
                new_run.font.small_caps = run.font.small_caps
                new_run.font.shadow = run.font.shadow
                new_run.font.outline = run.font.outline
                new_run.font.emboss = run.font.emboss
                new_run.font.imprint = run.font.imprint
                new_run.font.hidden = run.font.hidden
                new_run.font.highlight_color = run.font.highlight_color
                if run.font.color:
                    new_run.font.color.rgb = run.font.color.rgb
                    new_run.font.color.theme_color = run.font.color.theme_color
                new_run.font.size = run.font.size
                new_run.font.name = run.font.name
                new_run.font.subscript = run.font.subscript
                new_run.font.superscript = run.font.superscript
                new_run.font.rtl = run.font.rtl
                new_run.font.complex_script = run.font.complex_script
                new_run.font.cs_bold = run.font.cs_bold
                new_run.font.cs_italic = run.font.cs_italic
                new_run.font.math = run.font.math
                new_run.font.no_proof = run.font.no_proof
                new_run.font.snap_to_grid = run.font.snap_to_grid
                new_run.font.spec_vanish = run.font.spec_vanish
                new_run.font.web_hidden = run.font.web_hidden

                new_runs.append(new_run)

            # Clear original runs and replace them with the new runs
            para.clear()
            for new_run in new_runs:
                para._element.append(new_run._element)

    # Save the modified document
    doc.save(output_path)

def process_resume(resume_path, job_description, output_path):
    """
    Processes the DOCX resume by appending 'ok' to the end of each sentence.
    The job_description parameter is kept for compatibility with the interface but is not used.
    """
    append_ok_to_sentences_with_full_formatting(resume_path, output_path)

def parse_markdown_line(line, paragraph):
    """
    Parses a markdown-formatted line and adds runs to the given paragraph.
    Supports **bold** and *italic* formatting.
    """
    # Split the line into tokens (captures **bold** and *italic*)
    tokens = re.split(r'(\*\*.*?\*\*|\*.*?\*)', line)
    for token in tokens:
        if token.startswith("**") and token.endswith("**"):
            run = paragraph.add_run(token.strip("**"))
            run.bold = True
        elif token.startswith("*") and token.endswith("*"):
            run = paragraph.add_run(token.strip("*"))
            run.italic = True
        else:
            paragraph.add_run(token)

def reformat_resume_text_for_docx(revised_resume_text):
    """
    Reformats the revised resume text to be ATS-friendly and structured.
    - Detects markdown headings indicated by "##Heading##" (with or without spaces)
    - Applies "Heading 2" style to these headings.
    - Applies "List Bullet" style for bullet items starting with "-" or "*"
    - Applies "Heading 2" style for lines starting with a numeric prefix (e.g., "1. ")
    - Leaves all other lines as regular paragraphs.
    """
    new_doc = Document()
    for line in revised_resume_text.split("\n"):
        stripped_line = line.strip()
        if not stripped_line:
            continue
        # Handle markdown-style headings (e.g., "##AHMED DOGHRI##")
        if stripped_line.startswith("##") and stripped_line.endswith("##"):
            heading_text = stripped_line.strip("#").strip()
            p = new_doc.add_paragraph(heading_text, style="Heading 2")
        # Handle numeric headings like "1. Work Experience"
        elif re.match(r'^\d+\.\s', stripped_line):
            p = new_doc.add_paragraph(stripped_line, style="Heading 2")
        # Handle bullet list items starting with "-" or "*"
        elif stripped_line.startswith("-") or stripped_line.startswith("*"):
            p = new_doc.add_paragraph(stripped_line, style="List Bullet")
        else:
            # For other lines, check for date patterns to simulate right-indented dates.
            date_pattern = r'(\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}\s*-\s*(?:Present|\d{4}))'
            date_match = re.search(date_pattern, stripped_line, re.IGNORECASE)
            if date_match:
                main_text = stripped_line[:date_match.start()].strip()
                date_text = stripped_line[date_match.start():].strip()
                p = new_doc.add_paragraph()
                p.add_run(main_text + " ")
                # Add a right-aligned tab for the date text.
                tab_stop_position = 5000  # Adjust as necessary.
                p.paragraph_format.tab_stops.add_tab_stop(tab_stop_position)
                p.add_run("\t" + date_text)
            else:
                p = new_doc.add_paragraph(stripped_line)
    return new_doc



def format_resume_with_chatgpt(resume_text):
    """
    Uses GPT‑3.5 to reformat and reorder the resume text for maximum ATS compatibility.
    Instruct the model to output plain text with clear section headings, bold/italic markers,
    and proper ordering. Do not add new content.
    """
    format_prompt_template = (
        "You are an expert resume formatter. Reformat and reorder the following resume text "
        "to maximize its compatibility with Applicant Tracking Systems (ATS). Use clear section headings, "
        "apply bold or italics where appropriate, and ensure the resume is concise and well-structured. "
        "Output the final resume text with formatting markers (e.g., use '##' for section headings and wrap "
        "important keywords with ** for bold). Do not add any content that is not already present.\n\n"
        "Resume Text:\n{resume_text}\n\n"
        "Formatted Resume Text:"
    )
    format_prompt = PromptTemplate(
        template=format_prompt_template,
        input_variables=["resume_text"]
    )
    formatter = format_prompt | ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.1)
    input_data = {"resume_text": resume_text}
    formatted_result = formatter.invoke(input=input_data)
    return formatted_result.content



def rewrite_resume(
    resume_path: str, 
    job_description: str, 
    output_path: str,
    model: str = "gpt-4o",
    temperature: float = 0.1,
    api_key: str = None
):
    """
    Rewrites a resume to better match a job description using OpenAI's API.
    
    Args:
        resume_path: Path to the original resume DOCX file
        job_description: Text of the job posting
        output_path: Path where the rewritten resume will be saved
        model: OpenAI model to use
        temperature: Creativity level (0.0 to 1.0)
        api_key: OpenAI API key
    """
    try:
        # Extract text from the resume
        doc = Document(resume_path)
        resume_text = "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
        
        # Create OpenAI client
        client = OpenAI(api_key=api_key)
        
        # Improved prompt with specific steps and formatting instructions
        prompt = f"""
        You are an expert resume writer with years of experience helping job seekers land interviews.
        
        I'll provide you with a job description and a resume. Your task is to rewrite the resume to maximize the candidate's chances of getting an interview.
        
        Follow these specific steps:
        
        STEP 1: Identify the top 6 skills/requirements from the job description that the employer values most and name them to maximize keyword matching and recruiter engagement.
        
        STEP 2: Identify relevant positions and work experiences from the original resume that match those top skills.
        
        STEP 3: Rewrite each work experience to:
        - Emphasize achievements that demonstrate the top skills
        - Use keywords from the job description
        - Quantify achievements with metrics where possible
        - Optimize for ATS (Applicant Tracking Systems)
        - Make reasonable enhancements to maximize keyword matching (without fabricating major qualifications)
        - Write the work experience in reverse chronological order, with the most recent experience first
        - Format each bullet point as: "skill: Achievement with metric" (where skill is one of the top skills in lowercase)
        
        STEP 4: Structure the resume with these exact section markers (DO NOT include these markers in your output):
        - <NAME>: For the candidate's name
        - <CONTACT>: For contact information (phone, email, LinkedIn, etc.)
        - <SUMMARY>: For professional summary
        - <SKILLS>: For skills section (arrange the 6 skills in 3 lines with 2 skills per line)
        - <EXPERIENCE>: For work experience section
        - <EDUCATION>: For education section
        - <COMPANY>: For each company name
        - <POSITION_DATE>: For job title and dates (format as "Job Title | Dates")
        - <BULLET>: For each bullet point
        
        STEP 5: Ensure the resume is comprehensive but concise:
        - Maximum 2 pages
        - Utilize the space effectively
        - Remove irrelevant information
        - Prioritize recent and relevant experiences
        - Prioritize skills that are most relevant to the job description
        - Prioritize work experiences over other sections like volunteerism and extracurricular activities
        - Prioritize longer work experiences over shorter ones, especially when there are multiple experiences around the same time period
        - Highlight promotions or achievements in the bullet points
        
        IMPORTANT: Use the section markers ONLY to indicate the structure. I will parse your response and remove these markers. The final resume should not contain any visible markers.
        
        JOB DESCRIPTION:
        {job_description}
        
        ORIGINAL RESUME:
        {resume_text}
        """
        
        # Check if using o1 or o3 models which have different API requirements
        if model.startswith('o1') or model.startswith('o3'):
            # For o1/o3 models, use a single user message without system message
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
            )
        else:
            # For standard GPT models, use system+user message format
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are an expert resume writer who helps job seekers optimize their resumes for specific job applications."},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=4000
            )
        
        # Extract the rewritten resume text
        rewritten_resume = response.choices[0].message.content.strip()
        print("--------------------------------")
        print("REWRITTEN RESUME")
        print(rewritten_resume)
        print("--------------------------------")
        
        # Create a new document with the rewritten content
        new_doc = Document()
        
        # Set document styles
        sections = new_doc.sections
        for section in sections:
            section.top_margin = 457200  # 0.5 inch
            section.bottom_margin = 457200  # 0.5 inch
            section.left_margin = 609600  # 0.67 inch
            section.right_margin = 609600  # 0.67 inch
        
        # Process the content with formatting markers
        lines = rewritten_resume.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Handle name (large and bold)
            if line.startswith('<NAME>'):
                name_text = line.replace('<NAME>', '').strip()
                name_para = new_doc.add_paragraph()
                name_run = name_para.add_run(name_text)
                name_run.bold = True
                name_run.font.size = 355600  # 14pt
                name_para.alignment = 1  # Center alignment
                
            # Handle contact information (centered, smaller font)
            elif line.startswith('<CONTACT>'):
                contact_text = line.replace('<CONTACT>', '').strip()
                contact_para = new_doc.add_paragraph()
                contact_run = contact_para.add_run(contact_text)
                contact_run.font.size = 254000  # 10pt
                contact_para.alignment = 1  # Center alignment
                
            # Handle section headings
            elif line.startswith('<SUMMARY>'):
                new_doc.add_paragraph()  # Add space before section
                heading = new_doc.add_heading('PROFESSIONAL SUMMARY', level=1)
                for run in heading.runs:
                    run.font.size = 160000  # 12pt
                    run.bold = True
                    
            elif line.startswith('<SKILLS>'):
                new_doc.add_paragraph()  # Add space before section
                heading = new_doc.add_heading('SKILLS', level=1)
                for run in heading.runs:
                    run.font.size = 160000  # 12pt
                    run.bold = True
                    
            elif line.startswith('<EXPERIENCE>'):
                new_doc.add_paragraph()  # Add space before section
                heading = new_doc.add_heading('PROFESSIONAL EXPERIENCE', level=1)
                for run in heading.runs:
                    run.font.size = 160000  # 12pt
                    run.bold = True
                    
            elif line.startswith('<EDUCATION>'):
                new_doc.add_paragraph()  # Add space before section
                heading = new_doc.add_heading('EDUCATION', level=1)
                for run in heading.runs:
                    run.font.size = 160000  # 12pt
                    run.bold = True
            
            # Handle company names (bold)
            elif line.startswith('<COMPANY>'):
                new_doc.add_paragraph()  # Add space before company
                company_text = line.replace('<COMPANY>', '').strip()
                company = new_doc.add_paragraph()
                company_run = company.add_run(company_text)
                company_run.bold = True
                company_run.font.size = 160000  # 11pt
                
            # Handle position and date (position bold, date right-aligned)
            elif line.startswith('<POSITION_DATE>'):
                position_date_text = line.replace('<POSITION_DATE>', '').strip()
                
                # Split by the pipe character if it exists
                if '|' in position_date_text:
                    position_text, date_text = position_date_text.split('|', 1)
                    position_text = position_text.strip()
                    date_text = date_text.strip()
                    
                    # Create paragraph with tab stop for right alignment
                    position_para = new_doc.add_paragraph()
                    
                    # Add position (left-aligned, bold)
                    position_run = position_para.add_run(position_text)
                    position_run.bold = True
                    position_run.font.size = 279400  # 11pt
                    
                    # Add tab and date (right-aligned)
                    position_para.add_run('\t\t\t\t\t')  # Multiple tabs for visual separation
                    date_run = position_para.add_run(date_text)
                    date_run.font.size = 279400  # 11pt
                    
                    # Set paragraph alignment to right for the date
                    position_para.paragraph_format.alignment = 3  # Right alignment
                else:
                    # If no pipe character, just add the text as is
                    position_para = new_doc.add_paragraph()
                    position_run = position_para.add_run(position_date_text)
                    position_run.bold = True
                    position_run.font.size = 279400  # 11pt
                
            # Handle bullet points
            elif line.startswith('<BULLET>'):
                bullet_text = line.replace('<BULLET>', '').strip()
                
                # Create bullet point paragraph
                bullet = new_doc.add_paragraph(style='List Bullet')
                
                # Check if the bullet point has a skill prefix (skill: text)
                if ':' in bullet_text:
                    skill, achievement = bullet_text.split(':', 1)
                    skill = skill.strip()
                    achievement = achievement.strip()
                    
                    # Add skill in bold (not capitalized)
                    skill_run = bullet.add_run(f"{skill.lower()}: ")
                    skill_run.bold = True
                    skill_run.font.size = 279400  # 11pt
                    
                    # Add achievement text
                    achievement_run = bullet.add_run(achievement)
                    achievement_run.font.size = 279400  # 11pt
                else:
                    # Just add the bullet text as is
                    bullet_run = bullet.add_run(bullet_text)
                    bullet_run.font.size = 279400  # 11pt
                
            # Handle skills section (2 skills per line)
            elif line.startswith('- ') and any(prev_line.startswith('<SKILLS>') for prev_line in lines[:lines.index(line)]):
                # Create a new paragraph for the skill
                skill_para = new_doc.add_paragraph()
                skill_para.style = 'List Bullet'
                skill_run = skill_para.add_run(line[2:])  # Remove the "- " prefix
                skill_run.font.size = 279400  # 11pt
                
            # Handle regular text (for lines without markers)
            else:
                # Skip lines that might contain visible markers
                if '**<' in line or '<NAME>' in line or '<CONTACT>' in line or line.startswith(':'):
                    continue
                    
                para = new_doc.add_paragraph()
                text_run = para.add_run(line)
                text_run.font.size = 279400  # 11pt
        
        # Save the document
        new_doc.save(output_path)
        return True
        
    except Exception as e:
        print(f"Resume rewriting failed: {e}. Falling back to original resume.")
        # If there's an error, copy the original resume to the output path
        if os.path.exists(resume_path):
            shutil.copy(resume_path, output_path)
        return False

def process_formatting(text):
    """
    Prepares text with formatting markers for processing.
    Returns a list of (text, is_bold, is_italic) tuples.
    """
    # Replace the markers with something we can parse more easily
    text = text.replace('**', '§BOLD§')
    text = text.replace('*', '§ITALIC§')
    
    # Split by formatting markers
    parts = []
    current_text = ""
    is_bold = False
    is_italic = False
    
    for char in text:
        if char == '§':
            if current_text:
                parts.append((current_text, is_bold, is_italic))
                current_text = ""
            
            # Check next few characters
            if text[text.index(char):].startswith('§BOLD§'):
                is_bold = not is_bold
                text = text[text.index(char) + 6:]  # Skip the marker
            elif text[text.index(char):].startswith('§ITALIC§'):
                is_italic = not is_italic
                text = text[text.index(char) + 8:]  # Skip the marker
        else:
            current_text += char
    
    if current_text:
        parts.append((current_text, is_bold, is_italic))
    
    return parts

def process_text_with_formatting(text, paragraph):
    """
    Adds text with proper formatting to a paragraph.
    """
    # Process bold text (between ** markers)
    bold_pattern = r'\*\*(.*?)\*\*'
    italic_pattern = r'\*(.*?)\*'
    
    # First, find all bold sections and process them
    bold_matches = re.finditer(bold_pattern, text)
    last_end = 0
    for match in bold_matches:
        # Add text before the bold section
        if match.start() > last_end:
            paragraph.add_run(text[last_end:match.start()])
        
        # Add the bold text
        bold_run = paragraph.add_run(match.group(1))
        bold_run.bold = True
        
        last_end = match.end()
    
    # Add any remaining text after the last bold section
    if last_end < len(text):
        remaining_text = text[last_end:]
        
        # Process italic text in the remaining text
        italic_matches = re.finditer(italic_pattern, remaining_text)
        last_italic_end = 0
        
        for match in italic_matches:
            # Add text before the italic section
            if match.start() > last_italic_end:
                paragraph.add_run(remaining_text[last_italic_end:match.start()])
            
            # Add the italic text
            italic_run = paragraph.add_run(match.group(1))
            italic_run.italic = True
            
            last_italic_end = match.end()
        
        # Add any remaining text after the last italic section
        if last_italic_end < len(remaining_text):
            paragraph.add_run(remaining_text[last_italic_end:])

def generate_recommendations(
    job_description: str, 
    resume_text: str,
    model: str = "gpt-4o",
    temperature: float = 0.1,
    api_key: str = None
) -> str:
    """
    Generates recommendations for improving the resume based on the job description.
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
        
        JOB DESCRIPTION:
        {job_description}
        
        RESUME:
        {resume_text}
        """
        
        # Check if using o1 or o3 models which have different API requirements
        if model.startswith('o1') or model.startswith('o3'):
            # For o1/o3 models, use a single user message without system message
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=1.0,  # o1/o3 models only support temperature=1.0
                max_completion_tokens=2000
            )
        else:
            # For standard GPT models, use system+user message format
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are an expert career coach who provides detailed, actionable advice to job seekers."},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=2000
            )
        
        # Return the recommendations
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        print(f"Recommendation generation failed: {e}")
        return "Unable to generate recommendations due to an error. Please try again later."