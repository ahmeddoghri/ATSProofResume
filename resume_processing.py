from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
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

from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT, WD_PARAGRAPH_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docx.shared import Twips
from docx.enum.style import WD_STYLE_TYPE
import os
import re
import time
import logging
from recommendations import generate_recommendations


# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def parse_date(date_str):
    """
    Parse a date string in MM/YYYY format and return a tuple (year, month) for sorting.
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

def add_section_heading(doc, text):
    """Add a section heading with consistent formatting and reduced spacing"""
    heading = doc.add_paragraph(style='Compact')
    heading.alignment = WD_ALIGN_PARAGRAPH.LEFT
    heading_run = heading.add_run(text)
    heading_run.bold = True
    heading_run.font.size = Pt(12)
    heading_run.font.name = "Calibri"
    heading_run.font.color.rgb = RGBColor(0x33, 0x33, 0x33)
    
    # Add a horizontal line below the heading
    p = heading._p
    pPr = p.get_or_add_pPr()
    pBdr = OxmlElement('w:pBdr')
    bottom = OxmlElement('w:bottom')
    bottom.set(qn('w:val'), 'single')
    bottom.set(qn('w:sz'), '6')
    bottom.set(qn('w:space'), '1')
    bottom.set(qn('w:color'), '999999')
    pBdr.append(bottom)
    pPr.append(pBdr)
    
    # Reduce space after heading
    heading.paragraph_format.space_after = Pt(3)
    
    return heading

def add_bullet_point(doc, text, indent_level=0):
    """Add a bullet point with consistent formatting and reduced spacing"""
    bullet = doc.add_paragraph(style='Compact')  # Use compact style
    bullet.paragraph_format.left_indent = Inches(0.25 + (0.25 * indent_level))
    bullet.paragraph_format.first_line_indent = Inches(-0.25)
    
    # Check if the bullet point has a skill prefix (skill: text)
    if ':' in text:
        skill, achievement = text.split(':', 1)
        skill = skill.strip()
        achievement = achievement.strip()
        
        # Add bullet character
        bullet_char = bullet.add_run("• ")
        bullet_char.font.size = Pt(11)
        bullet_char.font.name = "Calibri"
        
        # Add skill in bold (not capitalized)
        skill_run = bullet.add_run(f"{skill.lower()}: ")
        skill_run.bold = True
        skill_run.font.size = Pt(11)
        skill_run.font.name = "Calibri"
        
        # Add achievement text
        achievement_run = bullet.add_run(achievement)
        achievement_run.font.size = Pt(11)
        achievement_run.font.name = "Calibri"
    else:
        # Add bullet character
        bullet_char = bullet.add_run("• ")
        bullet_char.font.size = Pt(11)
        bullet_char.font.name = "Calibri"
        
        # Just add the bullet text as is
        bullet_run = bullet.add_run(text)
        bullet_run.font.size = Pt(11)
        bullet_run.font.name = "Calibri"
    
    # Reduce space after bullet point
    bullet.paragraph_format.space_after = Pt(2)
    
    return bullet


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
    resume_path, 
    job_description, 
    output_path, 
    model="gpt-4o", 
    temperature=0.1,
    api_key=None
):
    """
    Rewrites a resume to better match a job description.
    
    Args:
        resume_path: Path to the resume DOCX file
        job_description: Job description text
        output_path: Path to save the rewritten resume
        model: OpenAI model to use
        temperature: Temperature for generation
        api_key: OpenAI API key
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Extract text from resume
        doc = Document(resume_path)
        resume_text = "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
        
        # Create OpenAI client
        client = OpenAI(api_key=api_key)
        
        # Create the prompt
        prompt = f"""
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
        
        FORMAT YOUR RESPONSE EXACTLY AS FOLLOWS:
        
        <NAME>
        [Full Name]
        
        <CONTACT>
        [Email] | [LinkedIn] | [Phone]
        
        <SUMMARY>
        [Professional summary paragraph]
        
        <SKILLS>
        [Skill 1] | [Skill 2] | [Skill 3]
        [Skill 4] | [Skill 5] | [Skill 6]
        
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
        [Category]: [Details]
        
        IMPORTANT: 
        1. Maintain this EXACT format with section tags (<NAME>, <CONTACT>, etc.)
        2. For each bullet point, start with a relevant skill area in lowercase, followed by a colon
        3. Include 1-2 bullet points per position, focusing on the most relevant achievements
        4. Ensure all dates are in MM/YYYY format
        5. Do not add any explanatory text or notes outside this format
        """
        
        # Make the API call
        max_retries = 3
        retry_count = 0
        success = False
        
        while retry_count < max_retries and not success:
            try:
                logging.info(f"Attempt {retry_count + 1} to rewrite resume using model: {model}")
                
                # Check if using o1 or o3 models which have different API requirements
                if model.startswith('o1') or model.startswith('o3') or model.startswith('claude'):
                    # For o1/o3/claude models, use a single user message without system message
                    response = client.chat.completions.create(
                        model=model,
                        messages=[
                            {"role": "user", "content": "You are an expert resume writer who tailors resumes to job descriptions. Follow the format instructions exactly.\n\n" + prompt}
                        ]
                    )
                else:
                    # For standard GPT models, use system+user message format
                    response = client.chat.completions.create(
                        model=model,
                        messages=[
                            {"role": "system", "content": "You are an expert resume writer who tailors resumes to job descriptions. Follow the format instructions exactly."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=temperature
                    )
                
                # Get the generated resume text
                resume_text = response.choices[0].message.content.strip()
                
                # Validate the format
                if (
                    "<NAME>" in resume_text and 
                    "<CONTACT>" in resume_text and 
                    "<SUMMARY>" in resume_text and 
                    "<SKILLS>" in resume_text and 
                    "<EXPERIENCE>" in resume_text and 
                    "<COMPANY>" in resume_text and 
                    "<POSITION_DATE>" in resume_text and 
                    "<BULLET>" in resume_text
                ):
                    success = True
                    logging.info("Resume format validation successful")
                else:
                    logging.warning("Resume format validation failed, retrying...")
                    retry_count += 1
                    
            except Exception as e:
                logging.error(f"API error on attempt {retry_count + 1}: {str(e)}")
                retry_count += 1
                time.sleep(2)  # Wait before retrying
        
        if not success:
            logging.error("Failed to generate properly formatted resume after multiple attempts")
            return False
        
        # Create a new document with the rewritten resume
        new_doc = Document()
        
        # Set up document styles
        styles = new_doc.styles
        
        # Add a custom style for compact paragraphs
        if 'Compact' not in styles:
            compact_style = styles.add_style('Compact', WD_STYLE_TYPE.PARAGRAPH)
            compact_style.font.name = "Calibri"
            compact_style.font.size = Pt(11)
            compact_style.paragraph_format.space_after = Pt(2)
            compact_style.paragraph_format.space_before = Pt(2)
        
        # Set page margins
        sections = new_doc.sections
        for section in sections:
            section.top_margin = Inches(0.5)
            section.bottom_margin = Inches(0.5)
            section.left_margin = Inches(0.75)
            section.right_margin = Inches(0.75)
        
        # Parse the resume text
        lines = resume_text.strip().split('\n')
        
        # Process the resume sections
        name = ""
        contact_info = []
        summary = []
        skills = []
        
        in_name = False
        in_contact = False
        in_summary = False
        in_skills = False
        in_experience = False
        in_education = False
        in_volunteerism = False
        in_other_info = False
        
        current_company = None
        current_position = None
        current_bullets = []
        
        companies = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if line == "<NAME>":
                in_name = True
                in_contact = False
                in_summary = False
                in_skills = False
                in_experience = False
                in_education = False
                in_volunteerism = False
                in_other_info = False
                continue
                
            if line == "<CONTACT>":
                in_name = False
                in_contact = True
                in_summary = False
                in_skills = False
                in_experience = False
                in_education = False
                in_volunteerism = False
                in_other_info = False
                continue
                
            if line == "<SUMMARY>":
                in_name = False
                in_contact = False
                in_summary = True
                in_skills = False
                in_experience = False
                in_education = False
                in_volunteerism = False
                in_other_info = False
                continue
                
            if line == "<SKILLS>":
                in_name = False
                in_contact = False
                in_summary = False
                in_skills = True
                in_experience = False
                in_education = False
                in_volunteerism = False
                in_other_info = False
                continue
                
            if line == "<EXPERIENCE>":
                in_name = False
                in_contact = False
                in_summary = False
                in_skills = False
                in_experience = True
                in_education = False
                in_volunteerism = False
                in_other_info = False
                continue
                
            if line == "<EDUCATION>":
                # If we were processing a company, save it
                if current_company is not None:
                    companies.append({
                        "company": current_company,
                        "position": current_position,
                        "bullets": current_bullets
                    })
                    current_company = None
                    current_position = None
                    current_bullets = []
                
                in_name = False
                in_contact = False
                in_summary = False
                in_skills = False
                in_experience = False
                in_education = True
                in_volunteerism = False
                in_other_info = False
                continue
                
            if line == "<VOLUNTEERISM>":
                in_name = False
                in_contact = False
                in_summary = False
                in_skills = False
                in_experience = False
                in_education = False
                in_volunteerism = True
                in_other_info = False
                continue
                
            if line == "<OTHER RELEVANT INFORMATION>":
                in_name = False
                in_contact = False
                in_summary = False
                in_skills = False
                in_experience = False
                in_education = False
                in_volunteerism = False
                in_other_info = True
                continue
                
            # Process content based on current section
            if in_name:
                name = line
            elif in_contact:
                contact_info.append(line)
            elif in_summary:
                summary.append(line)
            elif in_skills:
                skills.append(line)
            elif in_experience:
                if line == "<COMPANY>":
                    # If we were processing a company, save it
                    if current_company is not None:
                        companies.append({
                            "company": current_company,
                            "position": current_position,
                            "bullets": current_bullets
                        })
                        current_company = None
                        current_position = None
                        current_bullets = []
                    continue
                    
                if line == "<POSITION_DATE>":
                    continue
                    
                if line == "<BULLET>":
                    continue
                    
                if current_company is None:
                    current_company = line
                elif current_position is None:
                    current_position = line
                else:
                    current_bullets.append(line)
        
        # Don't forget to add the last company if there is one
        if current_company is not None:
            companies.append({
                "company": current_company,
                "position": current_position,
                "bullets": current_bullets
            })
        
        # Now create the document with the parsed information
        
        # Add name as title
        name_para = new_doc.add_paragraph(style='Compact')
        name_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        name_run = name_para.add_run(name)
        name_run.bold = True
        name_run.font.size = Pt(16)
        name_run.font.name = "Calibri"
        
        # Add contact info
        contact_para = new_doc.add_paragraph(style='Compact')
        contact_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        contact_run = contact_para.add_run(" | ".join(contact_info))
        contact_run.font.size = Pt(11)
        contact_run.font.name = "Calibri"
        
        # Add summary
        if summary:
            add_section_heading(new_doc, "PROFESSIONAL SUMMARY")
            summary_para = new_doc.add_paragraph(style='Compact')
            summary_run = summary_para.add_run(" ".join(summary))
            summary_run.font.size = Pt(11)
            summary_run.font.name = "Calibri"
        
        # Add skills
        if skills:
            add_section_heading(new_doc, "SKILLS")
            for skill_line in skills:
                skill_para = new_doc.add_paragraph(style='Compact')
                skill_run = skill_para.add_run(skill_line)
                skill_run.font.size = Pt(11)
                skill_run.font.name = "Calibri"
        
        # Add experience
        if companies:
            add_section_heading(new_doc, "PROFESSIONAL EXPERIENCE")
            
            # Sort companies by date (most recent first)
            for company_data in companies:
                company = company_data["company"]
                position = company_data["position"]
                bullets = company_data["bullets"]
                
                # Add company
                company_para = new_doc.add_paragraph(style='Compact')
                company_run = company_para.add_run(company)
                company_run.bold = True
                company_run.font.size = Pt(11)
                company_run.font.name = "Calibri"
                
                # Add position
                position_para = new_doc.add_paragraph(style='Compact')
                position_para.paragraph_format.left_indent = Inches(0.25)
                position_run = position_para.add_run(position)
                position_run.italic = True
                position_run.font.size = Pt(11)
                position_run.font.name = "Calibri"
                
                # Add bullets
                for bullet in bullets:
                    add_bullet_point(new_doc, bullet)
        
        # Process remaining sections (education, volunteerism, other info)
        education_lines = []
        volunteerism_lines = []
        other_info_lines = []
        
        in_education = False
        in_volunteerism = False
        in_other_info = False
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if line == "<EDUCATION>":
                in_education = True
                in_volunteerism = False
                in_other_info = False
                continue
                
            if line == "<VOLUNTEERISM>":
                in_education = False
                in_volunteerism = True
                in_other_info = False
                continue
                
            if line == "<OTHER RELEVANT INFORMATION>":
                in_education = False
                in_volunteerism = False
                in_other_info = True
                continue
                
            if line.startswith("<"):
                in_education = False
                in_volunteerism = False
                in_other_info = False
                continue
                
            if in_education:
                education_lines.append(line)
            elif in_volunteerism:
                volunteerism_lines.append(line)
            elif in_other_info:
                other_info_lines.append(line)
        
        # Add education section
        if education_lines:
            add_section_heading(new_doc, "EDUCATION")
            
            i = 0
            while i < len(education_lines):
                # Process each education entry (typically 3 lines per entry)
                if i + 2 < len(education_lines):
                    # University and location
                    edu_para = new_doc.add_paragraph(style='Compact')
                    edu_run = edu_para.add_run(education_lines[i])
                    edu_run.bold = True
                    edu_run.font.size = Pt(11)
                    edu_run.font.name = "Calibri"
                    
                    # Degree
                    degree_para = new_doc.add_paragraph(style='Compact')
                    degree_para.paragraph_format.left_indent = Inches(0.25)
                    degree_run = degree_para.add_run(education_lines[i+1])
                    degree_run.font.size = Pt(11)
                    degree_run.font.name = "Calibri"
                    
                    # GPA and dates
                    gpa_para = new_doc.add_paragraph(style='Compact')
                    gpa_para.paragraph_format.left_indent = Inches(0.25)
                    gpa_run = gpa_para.add_run(education_lines[i+2])
                    gpa_run.font.size = Pt(11)
                    gpa_run.font.name = "Calibri"
                    
                    i += 3
                else:
                    # Handle any remaining lines
                    edu_para = new_doc.add_paragraph(style='Compact')
                    edu_run = edu_para.add_run(education_lines[i])
                    edu_run.font.size = Pt(11)
                    edu_run.font.name = "Calibri"
                    i += 1
        
        # Add volunteerism section
        if volunteerism_lines:
            add_section_heading(new_doc, "VOLUNTEERISM")
            
            i = 0
            while i < len(volunteerism_lines):
                # Process each volunteerism entry (typically 2 lines per entry)
                if i + 1 < len(volunteerism_lines):
                    # Organization and dates
                    vol_para = new_doc.add_paragraph(style='Compact')
                    vol_run = vol_para.add_run(volunteerism_lines[i])
                    vol_run.bold = True
                    vol_run.font.size = Pt(11)
                    vol_run.font.name = "Calibri"
                    
                    # Description
                    desc_para = new_doc.add_paragraph(style='Compact')
                    desc_para.paragraph_format.left_indent = Inches(0.25)
                    desc_run = desc_para.add_run(volunteerism_lines[i+1])
                    desc_run.font.size = Pt(11)
                    desc_run.font.name = "Calibri"
                    
                    i += 2
                else:
                    # Handle any remaining lines
                    vol_para = new_doc.add_paragraph(style='Compact')
                    vol_run = vol_para.add_run(volunteerism_lines[i])
                    vol_run.font.size = Pt(11)
                    vol_run.font.name = "Calibri"
                    i += 1
        
        # Add other relevant information section
        if other_info_lines:
            add_section_heading(new_doc, "OTHER RELEVANT INFORMATION")
            
            for line in other_info_lines:
                if ":" in line:
                    # This line has a category and details
                    category, details = line.split(":", 1)
                    para = new_doc.add_paragraph(style='Compact')
                    para.paragraph_format.left_indent = Inches(0.25)
                    
                    # Add bullet
                    bullet_run = para.add_run("• ")
                    bullet_run.font.size = Pt(11)
                    bullet_run.font.name = "Calibri"
                    
                    # Add category in bold
                    cat_run = para.add_run(category.strip() + ": ")
                    cat_run.bold = True
                    cat_run.font.size = Pt(11)
                    cat_run.font.name = "Calibri"
                    
                    # Add details
                    details_run = para.add_run(details.strip())
                    details_run.font.size = Pt(11)
                    details_run.font.name = "Calibri"
                else:
                    # Just a regular line
                    para = new_doc.add_paragraph(style='Compact')
                    para.paragraph_format.left_indent = Inches(0.25)
                    
                    # Add bullet
                    bullet_run = para.add_run("• ")
                    bullet_run.font.size = Pt(11)
                    bullet_run.font.name = "Calibri"
                    
                    # Add text
                    text_run = para.add_run(line.strip())
                    text_run.font.size = Pt(11)
                    text_run.font.name = "Calibri"
        
        # Save the document
        new_doc.save(output_path)
        return True
        
    except Exception as e:
        logging.error(f"Resume rewriting failed: {e}. Falling back to original resume.")
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