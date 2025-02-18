from fastapi import FastAPI, UploadFile, File, Form, Request, WebSocket, BackgroundTasks
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

def process_resume_job(job_id: str, job_data: dict, resume_path: str, company_dir: str):
    """
    Background task that processes the resume:
      - Rewrites the resume using GPT‑3.5.
      - Generates recommendations.
      - Bundles outputs into a ZIP file.
    Updates the progress_status global at key milestones.
    """
    try:
        progress_status[job_id] = 10
        
        # (Job data was scraped in the upload step.)
        progress_status[job_id] = 30
        
        # (Assume job posting text and screenshot were already saved.)
        progress_status[job_id] = 50
        
        # Step 1: Rewrite the resume.
        formatted_resume_path = os.path.join(company_dir, "formatted_resume.docx")
        rewrite_resume(resume_path, job_data.get("job_text", ""), formatted_resume_path)
        progress_status[job_id] = 70
        
        # Step 2: Generate recommendations based on the job posting and original resume.
        recommendations_text = generate_recommendations(
            job_data.get("job_text", ""), 
            _extract_text_from_docx(resume_path)
        )
        recommendations_path = os.path.join(company_dir, "recommendations.txt")
        with open(recommendations_path, "w", encoding="utf-8") as f:
            f.write(recommendations_text)
        progress_status[job_id] = 85
        
        # Step 3: Bundle all outputs into a ZIP file.
        job_title = job_data.get("job_title", "Job_Description").replace(" ", "_")[:50]
        zip_filename = f"{os.path.basename(company_dir)}_{job_title}.zip"
        zip_filepath = os.path.join(OUTPUT_DIR, zip_filename)
        with zipfile.ZipFile(zip_filepath, "w") as zipf:
            job_posting_path = os.path.join(company_dir, f"{job_title}.txt")
            screenshot_path = os.path.join(company_dir, "job_screenshot.png")
            zipf.write(job_posting_path, os.path.basename(job_posting_path))
            zipf.write(screenshot_path, os.path.basename(screenshot_path))
            zipf.write(resume_path, os.path.basename(resume_path))
            zipf.write(formatted_resume_path, os.path.basename(formatted_resume_path))
            zipf.write(recommendations_path, os.path.basename(recommendations_path))
        progress_status[job_id] = 100
    except Exception as e:
        print(f"Error processing job {job_id}: {e}")
        progress_status[job_id] = 100

@app.get("/", response_class=HTMLResponse)
async def landing_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse(os.path.join("static", "favicon.ico"))

@app.post("/upload_resume/")
async def upload_resume(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    job_link: str = Form(...)
):
    """
    Validates the job posting URL, saves the resume and job posting data,
    and schedules a background task to process the resume.
    Returns a unique job_id and a redirect URL to the result page,
    where the user can choose to download the processed resume or try again.
    """
    # Validate job posting URL
    parsed_url = urlparse(job_link)
    if not (parsed_url.scheme and parsed_url.netloc):
        return JSONResponse(status_code=400, content={"error": "Invalid job posting URL."})
    
    # Generate a unique job ID for progress tracking.
    job_id = str(uuid.uuid4())
    
    # Scrape job posting details.
    job_data = job_scraper.scrape_job_posting(job_link)
    company_name = job_data["company"].replace(" ", "_")
    if company_name == "Unknown_Company":
        company_name = "Generic_Company"
    
    company_dir = os.path.join(OUTPUT_DIR, company_name)
    os.makedirs(company_dir, exist_ok=True)
    
    # Save job posting text.
    job_title = job_data.get("job_title", "Job_Description").replace(" ", "_")[:50]
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
    
    # Schedule background processing.
    background_tasks.add_task(process_resume_job, job_id, job_data, resume_path, company_dir)
    
    # Construct a redirect URL to the result page.
    redirect_url = f"/result?download_url=/download/{company_name}_{job_title}.zip"
    
    return JSONResponse(content={"redirect_url": redirect_url, "job_id": job_id})

@app.get("/result", response_class=HTMLResponse)
async def result_page(request: Request, download_url: str):
    return templates.TemplateResponse("result.html", {"request": request, "download_url": download_url})

@app.get("/download/{zip_filename}")
async def download_zip(zip_filename: str):
    zip_filepath = os.path.join(OUTPUT_DIR, zip_filename)
    return FileResponse(zip_filepath, filename=zip_filename)