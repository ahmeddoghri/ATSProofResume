from docx import Document
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

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
                modified_sentences = [sentence + ' ok' if sentence else '' for sentence in sentences]
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

# Example usage:
# process_resume("input_resume.docx", "automation", "output_resume.docx")