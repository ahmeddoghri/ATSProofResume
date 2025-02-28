from fastapi import FastAPI, UploadFile, File, Form, Request, WebSocket, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
import os
import shutil
import zipfile
import uuid
import asyncio
from urllib.parse import urlparse
from docx import Document
from job_scraper import JobPostingScraper  # Updated import
from resume_processing import rewrite_resume, generate_recommendations
import re
from openai import OpenAI
from typing import List

app = FastAPI() 
templates = Jinja2Templates(directory="templates")
OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

job_scraper = JobPostingScraper()

# Global dictionary to store progress status keyed by job ID
progress_status = {}

@app.websocket("/ws/progress/{job_id}")
async def websocket_progress(websocket: WebSocket, job_id: str):
    await websocket.accept()
    while True:
        progress = progress_status.get(job_id, 0)
        await websocket.send_text(str(progress))
        if progress >= 100:
            break
        await asyncio.sleep(1)

def _extract_text_from_docx(docx_path: str) -> str:
    """Helper function to extract text from a DOCX file."""
    doc = Document(docx_path)
    return "\n".join([para.text for para in doc.paragraphs if para.text.strip()])

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
        
        # Pass AI parameters to the processing functions
        formatted_resume_path = os.path.join(company_dir, "formatted_resume.docx")
        rewrite_resume(
            resume_path, 
            job_data.get("job_text", ""), 
            formatted_resume_path,
            model=model,
            temperature=temperature,
            api_key=api_key
        )
        progress_status[job_id] = 70
        
        recommendations_text = generate_recommendations(
            job_data.get("job_text", ""), 
            _extract_text_from_docx(resume_path),
            model=model,
            temperature=temperature,
            api_key=api_key
        )
        recommendations_path = os.path.join(company_dir, "recommendations.txt")
        with open(recommendations_path, "w", encoding="utf-8") as f:
            f.write(recommendations_text)
        progress_status[job_id] = 85
        
        # Step 3: Bundle all outputs into a ZIP file
        job_title = sanitize_filename(job_data.get("job_title", "Job_Description"))[:50]
        company_name = sanitize_filename(job_data.get("company", "Unknown_Company"))
        zip_filename = f"{company_name}_{job_title}.zip"
        zip_filepath = os.path.join(OUTPUT_DIR, zip_filename)
        
        with zipfile.ZipFile(zip_filepath, "w") as zipf:
            # Add all files to the ZIP
            files_to_zip = {
                "job_posting.txt": os.path.join(company_dir, f"{job_title}.txt"),
                "job_screenshot.png": os.path.join(company_dir, "job_screenshot.png"),
                "original_resume.docx": resume_path,
                "formatted_resume.docx": formatted_resume_path,
                "recommendations.txt": recommendations_path
            }
            
            for arc_name, file_path in files_to_zip.items():
                if os.path.exists(file_path):
                    zipf.write(file_path, arc_name)
                
        progress_status[job_id] = 100
        
    except Exception as e:
        print(f"Error processing job {job_id}: {e}")
        progress_status[job_id] = -1  # Indicate error

@app.get("/", response_class=HTMLResponse)
async def landing_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse(os.path.join("static", "favicon.ico"))

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

@app.post("/upload_resume/")
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
    # Validate job posting URL
    parsed_url = urlparse(job_link)
    if not (parsed_url.scheme and parsed_url.netloc):
        return JSONResponse(status_code=400, content={"error": "Invalid job posting URL."})
    
    # Generate a unique job ID for progress tracking
    job_id = str(uuid.uuid4())
    
    # Scrape job posting details
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

@app.get("/result", response_class=HTMLResponse)
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

@app.get("/check_progress/{job_id}")
async def check_progress(job_id: str):
    """Check if the file processing is complete."""
    progress = progress_status.get(job_id, 0)
    return JSONResponse(content={"progress": progress})

@app.get("/download/{zip_filename}")
async def download_zip(zip_filename: str):
    """Download the processed resume package."""
    zip_filepath = os.path.join(OUTPUT_DIR, zip_filename)
    
    # Wait for up to 30 seconds for the file to be created
    for _ in range(30):
        if os.path.exists(zip_filepath):
            return FileResponse(zip_filepath, filename=zip_filename)
        await asyncio.sleep(1)
    
    raise HTTPException(
        status_code=404,
        detail="File not found. Please ensure the file was generated successfully."
    )

@app.get("/available_models")
async def get_available_models():
    """
    Returns a curated list of primary OpenAI models.
    """
    try:
        # Define main OpenAI model categories based on latest documentation
        main_models = [
            {
                "id": "gpt-4.5-preview",
                "name": "GPT-4.5 Preview",
                "provider": "OpenAI",
                "recommended": False,
                "category": "Advanced",
                "description": "Latest and most advanced GPT model"
            },
            {
                "id": "gpt-4o",
                "name": "GPT-4 Optimized",
                "provider": "OpenAI",
                "recommended": True,
                "category": "Advanced",
                "description": "Optimized version of GPT-4"
            },
            {
                "id": "gpt-4o-mini",
                "name": "GPT-4o Mini",
                "provider": "OpenAI",
                "recommended": False,
                "category": "Advanced",
                "description": "Lighter version of GPT-4 Optimized"
            },
            {
                "id": "gpt-3.5-turbo-0125",
                "name": "GPT-3.5 Turbo",
                "provider": "OpenAI",
                "recommended": False,
                "category": "Standard",
                "description": "Fast and cost-effective for simpler tasks"
            }
        ]

        # Sort models by category and recommendation status
        sorted_models = sorted(
            main_models,
            key=lambda x: (
                not x["recommended"],  # Recommended models first
                x["category"] != "Advanced",  # Advanced models first
                x["name"]  # Alphabetical within same category
            )
        )
        
        return JSONResponse(content={"models": sorted_models})
    except Exception as e:
        print(f"Error organizing models: {e}")
        # Fallback to basic models
        default_models = [
            {
                "id": "gpt-4.5-preview",
                "name": "GPT-4.5 Preview",
                "provider": "OpenAI",
                "recommended": False,
                "category": "Advanced",
                "description": "Latest and most advanced GPT model"
            },
            {
                "id": "gpt-4o",
                "name": "GPT-4 Optimized",
                "provider": "OpenAI",
                "recommended": True,
                "category": "Advanced",
                "description": "Optimized version of GPT-4"
            },
            {
                "id": "gpt-4o-mini",
                "name": "GPT-4o Mini",
                "provider": "OpenAI",
                "recommended": False,
                "category": "Advanced",
                "description": "Lighter version of GPT-4 Optimized"
            },
            {
                "id": "gpt-3.5-turbo-0125",
                "name": "GPT-3.5 Turbo",
                "provider": "OpenAI",
                "recommended": False,
                "category": "Standard",
                "description": "Fast and cost-effective for simpler tasks"
            }
        ]
        return JSONResponse(content={"models": default_models})