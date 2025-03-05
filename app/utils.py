import re
from docx import Document


def extract_text_from_docx(docx_path: str) -> str:
    """Helper function to extract text from a DOCX file."""
    doc = Document(docx_path)
    return "\n".join([para.text for para in doc.paragraphs if para.text.strip()])


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename by removing or replacing invalid characters.
    """
    # Replace commas, spaces and other special chars with underscores
    sanitized = re.sub(r'[,\s]+', '_', filename)
    # Remove any other non-alphanumeric characters except underscores and dots
    sanitized = re.sub(r'[^\w\-\.]', '', sanitized)
    # Ensure the filename doesn't exceed a reasonable length
    return sanitized[:100]


def format_markdown_for_text(content):
    """
    Convert markdown formatting to plain text formatting that looks good in .txt files
    """
    # Replace markdown headings with ASCII-style headings
    content = re.sub(r'###\s+(.*)', r'\n\1\n' + '-' * 40, content)
    content = re.sub(r'##\s+(.*)', r'\n\1\n' + '=' * 40, content)
    content = re.sub(r'#\s+(.*)', r'\n\1\n' + '=' * 60, content)
    
    # Replace bold with UPPERCASE
    content = re.sub(r'\*\*(.*?)\*\*', lambda m: m.group(1).upper(), content)
    
    # Replace italic with _underscores_
    content = re.sub(r'\*(.*?)\*', r'_\1_', content)
    
    # Replace markdown bullet points with ASCII bullet points
    content = re.sub(r'^\s*-\s+', '• ', content, flags=re.MULTILINE)
    
    # Replace markdown horizontal rules
    content = re.sub(r'---+', '=' * 60, content)
    
    return content