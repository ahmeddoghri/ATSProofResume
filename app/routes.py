from fastapi import APIRouter, Request, BackgroundTasks, UploadFile, File, Form, WebSocket, HTTPException
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from app.services import get_fallback_models, fetch_openai_models, clear_model_cache
from app.tasks import process_resume_job
from app.utils import sanitize_filename, format_markdown_for_text
from urllib.parse import urlparse
import os
import uuid
import shutil
import asyncio
import re
from openai import OpenAI
from .tasks import process_resume_job
from .utils import sanitize_filename
from job_scraper import JobPostingScraper
from interview_questions import generate_interview_questions
import logging

router = APIRouter()
templates = Jinja2Templates(directory="templates")
OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Define global dictionaries if needed.
progress_status = {}
jobs_db = {}



@router.get("/", response_class=HTMLResponse)
async def landing_page(request: Request):
    """Landing page for the application."""
    return templates.TemplateResponse("index.html", {"request": request})

@router.get("/favicon.ico", include_in_schema=False)
async def favicon():
    """Favicon for the application."""
    return FileResponse(os.path.join("static", "favicon.ico"))


@router.post("/upload_resume/")
async def upload_resume(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    job_link: str = Form(...),
    model: str = Form(...),
    temperature: float = Form(...),
    api_key: str = Form(...)
):
    """
    Validates the job posting URL, saves the resume and job posting data,
    and schedules a background task to process the resume.
    """
    # Initialize job scraper with user-selected model
    job_scraper = JobPostingScraper(
        model_name=model,
        temperature=temperature,
        api_key=api_key
    )
    
    # Validate job posting URL
    parsed_url = urlparse(job_link)
    if not (parsed_url.scheme and parsed_url.netloc):
        return JSONResponse(status_code=400, content={"error": "Invalid job posting URL."})
    
    # Generate a unique job ID for progress tracking
    job_id = str(uuid.uuid4())
    
    # Scrape job posting details with the configured model
    job_data = job_scraper.scrape_job_posting(job_link)
    
    # Sanitize company name and job title for file paths
    company_name = sanitize_filename(job_data["company"])
    if company_name == "Unknown_Company":
        company_name = "Generic_Company"
    
    job_title = sanitize_filename(job_data.get("job_title", "Job_Description"))[:50]
    
    company_dir = os.path.join(OUTPUT_DIR, company_name)
    os.makedirs(company_dir, exist_ok=True)
    
    # Save job posting text.
    job_posting_path = os.path.join(company_dir, f"{job_title}.txt")
    with open(job_posting_path, "w", encoding="utf-8") as f:
        f.write(job_data.get("job_text", ""))
    
    # Capture a screenshot of the job posting.
    screenshot_path = os.path.join(company_dir, "job_screenshot.png")
    job_scraper.capture_screenshot(job_link, screenshot_path)
    
    # Save the uploaded resume DOCX.
    resume_path = os.path.join(company_dir, "original_resume.docx")
    with open(resume_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Create zip filename with sanitized components
    zip_filename = f"{company_name}_{job_title}.zip"
    
    # Schedule background processing
    background_tasks.add_task(
        process_resume_job, 
        job_id, 
        job_data, 
        resume_path, 
        company_dir,
        model,
        temperature,
        api_key
    )
    
    # Return both the job ID and download URL
    return JSONResponse(content={
        "redirect_url": f"/result?job_id={job_id}&download_url=/download/{zip_filename}",
        "job_id": job_id
    })

@router.get("/result", response_class=HTMLResponse)
async def result_page(request: Request, job_id: str, download_url: str):
    """Show result page with download link and progress status."""
    return templates.TemplateResponse(
        "result.html", 
        {
            "request": request, 
            "download_url": download_url,
            "job_id": job_id
        }
    )

@router.post("/generate_questions/")
async def generate_questions(
    job_id: str = Form(...),
    model: str = Form("gpt-4o")
):
    """Generate interview questions based on job description and resume"""
    try:
        # Get job details from the database
        job = jobs_db.get(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Extract company name from job description
        company_name = ""
        job_description = job.get("job_description", "")
        resume_text = job.get("resume_text", "")
        
        # Try to extract company name from job description
        company_match = re.search(r"(?:at|for|with)\s+([A-Z][A-Za-z0-9\s&]+)(?:\.|\,|\s|$)", job_description)
        if company_match:
            company_name = company_name or company_match.group(1).strip()
        
        if not company_name:
            # Fallback: ask the model to extract the company name
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Extract the company name from this job description. Return only the company name."},
                    {"role": "user", "content": job_description[:1000]}  # Use first 1000 chars for efficiency
                ],
                temperature=0.1
            )
            company_name = response.choices[0].message.content.strip()
        
        # Generate interview questions
        questions = generate_interview_questions(
            job_description=job_description,
            resume_text=resume_text,
            company_name=company_name,
            api_key=os.getenv("OPENAI_API_KEY"),
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
        
        # Save questions to file in the company directory
        company_dir = os.path.join(OUTPUT_DIR, sanitize_filename(company_name))
        os.makedirs(company_dir, exist_ok=True)
        questions_path = os.path.join(company_dir, "interview_questions.txt")
        
        with open(questions_path, "w", encoding="utf-8") as f:
            f.write(questions_text)
        
        # Update job in database with questions
        job["interview_questions"] = questions
        job["interview_questions_text"] = questions_text
        jobs_db[job_id] = job
        
        return {"success": True, "questions": questions}
        
    except Exception as e:
        logging.error(f"Error generating interview questions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating questions: {str(e)}")


@router.get("/available_models")
async def get_available_models(api_key: str = None, force_refresh: bool = False):
    """
    Returns available OpenAI models with caching.
    If no API key is provided or there's an error, returns fallback models.
    """
    try:
        if force_refresh:
            clear_model_cache()
        if not api_key:
            return JSONResponse(content={"models": get_fallback_models()})
            
        models = await fetch_openai_models(api_key)
        return JSONResponse(content={"models": models})
        
    except Exception as e:
        print(f"Error in get_available_models: {e}")
        return JSONResponse(content={"models": get_fallback_models()})
    
@router.websocket("/ws/progress/{job_id}")
async def websocket_progress(websocket: WebSocket, job_id: str):
    """WebSocket endpoint for progress updates."""
    await websocket.accept()
    while True:
        progress = progress_status.get(job_id, 0)
        await websocket.send_text(str(progress))
        if progress >= 100:
            break
        await asyncio.sleep(1)

