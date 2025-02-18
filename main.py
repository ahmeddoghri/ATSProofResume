from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
import os
import shutil
import zipfile
from fastapi.templating import Jinja2Templates
from job_scraper import JobPostingScraper  # Updated import
from resume_processing import rewrite_resume  # remains unchanged
from urllib.parse import urlparse

app = FastAPI()
templates = Jinja2Templates(directory="templates")
OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

job_scraper = JobPostingScraper()

@app.get("/", response_class=HTMLResponse)
async def landing_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse(os.path.join("static", "favicon.ico"))

@app.post("/upload_resume/")
async def upload_resume(
    request: Request,
    file: UploadFile = File(...),
    job_link: str = Form(...)
):
    """
    Handles resume upload and job link submission.
    Uses JobPostingScraper to extract company, job title, and job text, and captures a screenshot.
    Then processes the resume with GPT‑3.5 rewriting and bundles all outputs.
    """
    
    parsed_url = urlparse(job_link)
    if not (parsed_url.scheme and parsed_url.netloc):
        return JSONResponse(status_code=400, content={"error": "Invalid job posting URL."})

    job_data = job_scraper.scrape_job_posting(job_link)
    company_name = job_data["company"].replace(" ", "_")
    if company_name == "Unknown_Company":
        company_name = "Generic_Company"

    company_dir = os.path.join(OUTPUT_DIR, company_name)
    os.makedirs(company_dir, exist_ok=True)

    job_title = job_data.get("job_title", "Job_Description").replace(" ", "_")[:50]
    job_posting_path = os.path.join(company_dir, f"{job_title}.txt")
    with open(job_posting_path, "w", encoding="utf-8") as f:
        f.write(job_data.get("job_text", ""))

    screenshot_path = os.path.join(company_dir, "job_screenshot.png")
    job_scraper.capture_screenshot(job_link, screenshot_path)

    resume_path = os.path.join(company_dir, "original_resume.docx")
    with open(resume_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    formatted_resume_path = os.path.join(company_dir, "formatted_resume.docx")
    rewrite_resume(resume_path, job_data.get("job_text", ""), formatted_resume_path)

    zip_filename = f"{company_name}_{job_title}.zip"
    zip_filepath = os.path.join(OUTPUT_DIR, zip_filename)
    with zipfile.ZipFile(zip_filepath, "w") as zipf:
        zipf.write(job_posting_path, os.path.basename(job_posting_path))
        zipf.write(screenshot_path, os.path.basename(screenshot_path))
        zipf.write(resume_path, os.path.basename(resume_path))
        zipf.write(formatted_resume_path, os.path.basename(formatted_resume_path))

    return JSONResponse(content={"redirect_url": f"/result?download_url=/download/{zip_filename}"})

@app.get("/result", response_class=HTMLResponse)
async def result_page(request: Request, download_url: str):
    return templates.TemplateResponse("result.html", {"request": request, "download_url": download_url})

@app.get("/download/{zip_filename}")
async def download_zip(zip_filename: str):
    zip_filepath = os.path.join(OUTPUT_DIR, zip_filename)
    return FileResponse(zip_filepath, filename=zip_filename)