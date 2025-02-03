import pdfplumber
import fitz  # PyMuPDF for PDF generation
import re

def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF file."""
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    return text.strip()

def match_resume_to_job(resume_text, job_description):
    """Extracts relevant experience based on job description."""
    
    # Extract skills from job description (basic keyword match)
    job_keywords = set(re.findall(r"\b\w+\b", job_description.lower()))

    # Filter resume sections that contain job-related keywords
    relevant_sections = [
        section for section in resume_text.split("\n\n")
        if any(word in section.lower() for word in job_keywords)
    ]
    
    return "\n\n".join(relevant_sections)

def generate_pdf(content, output_path):
    """Generates a formatted PDF from text."""
    doc = fitz.open()
    page = doc.new_page()

    # Add text to PDF
    text_rect = fitz.Rect(50, 50, 550, 750)  # Margin settings
    page.insert_textbox(text_rect, content, fontsize=11)

    doc.save(output_path)

def process_resume(resume_path, job_description, output_path):
    """Formats the resume to highlight key job-related experiences."""
    
    resume_text = extract_text_from_pdf(resume_path)
    formatted_text = match_resume_to_job(resume_text, job_description)
    
    generate_pdf(formatted_text, output_path)