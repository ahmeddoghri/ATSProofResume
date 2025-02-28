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
    formatter = format_prompt | ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.7)
    input_data = {"resume_text": resume_text}
    formatted_result = formatter.invoke(input=input_data)
    return formatted_result.content



def rewrite_resume(
    input_path: str, 
    job_description: str, 
    output_path: str, 
    model: str = "gpt-4-turbo-preview",
    temperature: float = 0.7,
    api_key: str = None
):
    """
    Rewrites the resume using the specified OpenAI model and parameters.
    """
    try:
        # Load resume text from the DOCX file
        doc = Document(input_path)
        resume_text = "\n".join([para.text for para in doc.paragraphs if para.text.strip()])

        # Define the prompt template with instructions for both required and optional sections.
        prompt_template = (
            "You are a career expert and resume optimization specialist. Your task is to rewrite the given resume so that it aligns perfectly with the job posting, increases keyword match for Applicant Tracking Systems (ATS), and maximizes the candidate's chance of securing an interview. The final resume must be concise, optimized for quick scanning, and no longer than two pages.\n\n"
            "Please address the following resume sections and requirements. Note: Sections marked as REQUIRED must be present and optimized. For sections marked as OPTIONAL, do not add them if the original resume does not contain any information for that section.\n\n"
            "1. **Contact Information** (REQUIRED):\n"
            "   - Verify that the name, phone number, email address, and location (city and state) are clear and professional.\n\n"
            "2. **Resume Summary/Objective** (REQUIRED):\n"
            "   - Enhance the professional summary or objective to concisely reflect the candidate's strengths and career goals in relation to the job posting.\n\n"
            "3. **Work Experience** (REQUIRED):\n"
            "   - Assess the employment history and professional experience. Emphasize promotions, career progression, quantifiable achievements, and alignment with the job responsibilities.\n\n"
            "4. **Education** (REQUIRED):\n"
            "   - Summarize the academic background, including degrees and certifications, clearly and succinctly.\n\n"
            "5. **Skills** (REQUIRED):\n"
            "   - Highlight key skills relevant to the job. Update terminology if the job posting emphasizes specific technologies (e.g., replace GCP with AWS) and include adjacent or related skills mentioned in the posting.\n\n"
            "6. **Certifications and Licenses** (OPTIONAL):\n"
            "   - If present, list only those certifications and licenses that are directly relevant.\n\n"
            "7. **Professional Affiliations** (OPTIONAL):\n"
            "   - If present, mention memberships in professional organizations that enhance the candidate's profile.\n\n"
            "8. **Volunteer Experience** (OPTIONAL):\n"
            "   - If present, include any volunteer work that supports the candidate's qualifications.\n\n"
            "9. **Projects** (OPTIONAL):\n"
            "   - If present, feature significant projects that demonstrate relevant skills and achievements.\n\n"
            "10. **Publications or Presentations** (OPTIONAL):\n"
            "    - If present, add any published works or presentations that contribute to the candidate's professional image.\n\n"
            "11. **Additional Information** (OPTIONAL):\n"
            "    - If present, briefly include extra details such as languages spoken or interests relevant to the job.\n\n"
            "Additional requirements:\n"
            "- Ensure the final resume is concise and optimized for quick scanning, minimizing wordiness while retaining critical details.\n"
            "- Clearly highlight any career promotions and progression in previous roles.\n"
            "- Do not add any optional section if the original resume does not contain it.\n"
            "- Replace or update keywords as needed: for example, if the job posting specifies AWS but the original resume mentions GCP, modify it to AWS and include related technologies from the posting.\n"
            "- Output only the rewritten resume test without any additional text.\n"
            "- Respect the same order of sections as the original resume.\n"
            "- If the job posting does not directly align with the candidate's background, reformat and optimize the resume by emphasizing transferable skills, key accomplishments, and overall strengths to create a more compelling presentation.\n"
            "- The final rewritten resume must fit within two pages.\n\n"
            "Job Posting:\n{job_posting}\n\n"
            "Original Resume:\n{resume_text}\n\n"
            "Rewritten Resume:"
        )
        prompt = PromptTemplate(
            template=prompt_template,
            input_variables=["job_posting", "resume_text"]
        )

        # Initialize the GPT‑3.5 chat model via LangChain using the updated import.
        llm = ChatOpenAI(
            model_name=model,
            temperature=temperature,
            openai_api_key=api_key
        )

        # Create a runnable sequence using the pipe operator.
        runnable = prompt | llm

        # Instead of formatting the prompt manually, pass a mapping.
        input_data = {"job_posting": job_description, "resume_text": resume_text}
        result = runnable.invoke(input=input_data)
        revised_resume_text = result.content  # Extract the revised text

        # Now, call the new formatting function to get the final ATS-friendly resume text.
        final_resume_text = format_resume_with_chatgpt(revised_resume_text)

        # Generate the final DOCX document using the formatted text.
        new_doc = reformat_resume_text_for_docx(final_resume_text)
        new_doc.save(output_path)
    except Exception as e:
        # Log the error if needed
        print(f"Resume rewriting failed: {e}. Falling back to original resume.")
        # Fallback: copy the original file to the output
        shutil.copy(input_path, output_path)
        
        
def generate_recommendations(
    job_posting: str, 
    resume_text: str,
    model: str = "gpt-4-turbo-preview",
    temperature: float = 0.7,
    api_key: str = None
) -> str:
    """
    Generates recommendations using the specified OpenAI model and parameters.
    """
    prompt_template = (
        "You are a career advisor. Based on the following job posting and resume, "
        "generate a list of bullet point recommendations to improve the resume. "
        "Include suggestions for missed keywords, skills to emphasize, and actionable improvements to maximize callback chances.\n\n"
        "Job Posting:\n{job_posting}\n\n"
        "Resume:\n{resume_text}\n\n"
        "Recommendations (each starting with a dash '-'):"
    )
    prompt = PromptTemplate(
        template=prompt_template,
        input_variables=["job_posting", "resume_text"]
    )
    llm = ChatOpenAI(
        model_name=model,
        temperature=temperature,
        openai_api_key=api_key
    )
    runnable = prompt | llm
    input_data = {"job_posting": job_posting, "resume_text": resume_text}
    result = runnable.invoke(input=input_data)
    return result.content