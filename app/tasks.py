import os
import zipfile
import logging
from app.utils import extract_text_from_docx, sanitize_filename, format_markdown_for_text
from app.state import progress_status, OUTPUT_DIR
from resume.processor import ResumeProcessor
from recommendations import generate_recommendations
from interview_questions import generate_interview_questions

def process_resume_job(
    job_id: str, 
    job_data: dict, 
    resume_path: str, 
    company_dir: str,
    model: str,
    temperature: float,
    api_key: str
):
    """
    Background task that processes the resume with specified AI parameters.
    """
    try:
        progress_status[job_id] = 10
        logging.info(f"Starting job {job_id} - Progress: 10%")
        
        # Pass AI parameters to the processing functions
        formatted_resume_path = os.path.join(company_dir, "formatted_resume.docx")
        
        resume_rewriter = ResumeProcessor(api_key=api_key)
        resume_rewriter.process_resume(
            resume_path, 
            job_data.get("job_text", ""), 
            formatted_resume_path,
            model=model,
            temperature=temperature,
        )
            
        progress_status[job_id] = 60
        logging.info(f"Resume processed for job {job_id} - Progress: 60%")
        
        # Extract resume text for further processing
        resume_text = extract_text_from_docx(resume_path)
        
        # Generate recommendations
        recommendations_text = generate_recommendations(
            job_data.get("job_text", ""), 
            resume_text,
            model=model,
            temperature=temperature,
            api_key=api_key
        )
        # Format markdown for text file
        recommendations_text = format_markdown_for_text(recommendations_text)
        recommendations_path = os.path.join(company_dir, "recommendations.txt")
        with open(recommendations_path, "w", encoding="utf-8") as f:
            f.write(recommendations_text)
        progress_status[job_id] = 75
        logging.info(f"Recommendations generated for job {job_id} - Progress: 75%")
        
        # Generate interview questions
        company_name = job_data.get("company", "Unknown Company")
        job_description = job_data.get("job_text", "")
        
        # Try to generate interview questions
        try:
            questions = generate_interview_questions(
                job_description=job_description,
                resume_text=resume_text,
                company_name=company_name,
                api_key=api_key,
                model=model
            )
            
            # Format questions as text
            questions_text = "SMART INTERVIEW QUESTIONS\n"
            questions_text += "=======================\n\n"
            questions_text += "Use these questions during your interview to demonstrate your knowledge and interest.\n\n"
            
            for category, question_list in questions.items():
                questions_text += f"{category.upper()}\n"
                questions_text += "=" * len(category) + "\n"
                for i, question in enumerate(question_list, 1):
                    # Format markdown in the question
                    formatted_question = format_markdown_for_text(question)
                    questions_text += f"{i}. {formatted_question}\n"
                questions_text += "\n"
            
            # Save questions to file
            questions_path = os.path.join(company_dir, "interview_questions.txt")
            with open(questions_path, "w", encoding="utf-8") as f:
                f.write(questions_text)
                
        except Exception as e:
            logging.error(f"Error generating interview questions: {e}")
            # Create a basic questions file if generation fails
            questions_path = os.path.join(company_dir, "interview_questions.txt")
            with open(questions_path, "w", encoding="utf-8") as f:
                f.write("Interview questions could not be generated. Please try again later.")
        
        progress_status[job_id] = 85
        logging.info(f"Interview questions generated for job {job_id} - Progress: 85%")
        
        # Step 3: Bundle all outputs into a ZIP file
        job_title = sanitize_filename(job_data.get("job_title", "Job_Description"))[:50]
        company_name = sanitize_filename(job_data.get("company", "Unknown_Company"))
        zip_filename = f"{company_name}_{job_title}.zip"
        zip_filepath = os.path.join(OUTPUT_DIR, zip_filename)
        logging.info(f"Creating ZIP file at: {zip_filepath}")
        
        # Create a proper ZIP file with appropriate compression
        with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add files to the ZIP with proper relative paths
            for root, _, files in os.walk(company_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    # Create relative path for the ZIP
                    arcname = os.path.relpath(file_path, os.path.dirname(company_dir))
                    zipf.write(file_path, arcname)

        logging.info(f"ZIP file created: {zip_filepath} (exists: {os.path.exists(zip_filepath)})")
        
        progress_status[job_id] = 100
        logging.info(f"Job {job_id} completed - Progress: 100%")
        
    except Exception as e:
        logging.error(f"Error processing job {job_id}: {e}")
        progress_status[job_id] = -1  # Indicate error

