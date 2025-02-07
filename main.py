from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
import os
import shutil
import zipfile
from fastapi.templating import Jinja2Templates
from job_scraper import scrape_job_posting
from resume_processing import process_resume  # updated to process .docx

app = FastAPI()

# Setup templates for HTML rendering
templates = Jinja2Templates(directory="templates")

# Output directory for processed files
OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

@app.get("/", response_class=HTMLResponse)
async def landing_page(request: Request):
    """Serve the HTML landing page."""
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
    Handles resume upload (now expected to be a .docx file) and job link submission,
    processes the resume by appending 'ok' to each sentence, and sends back a JSON
    redirect URL.
    """
    # Scrape job posting
    job_data = scrape_job_posting(job_link)
    company_name = job_data["company"].replace(" ", "_")  # Sanitize folder name

    if company_name == "Unknown_Company":
        company_name = "Generic_Company"

    # Create folder for company
    company_dir = os.path.join(OUTPUT_DIR, company_name)
    os.makedirs(company_dir, exist_ok=True)

    # Extract job title from job posting text
    job_title = "Job_Description"
    for line in job_data["content"].split("\n"):
        if "title" in line.lower():
            job_title = line.strip().replace(" ", "_")[:50]  # Limit length
            break

    # Save job posting text file
    job_posting_path = os.path.join(company_dir, f"{job_title}.txt")
    with open(job_posting_path, "w", encoding="utf-8") as f:
        f.write(job_data["content"])

    # Save the original resume as a DOCX file
    resume_path = os.path.join(company_dir, "original_resume.docx")
    with open(resume_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Process the resume (append " ok" to each sentence while preserving formatting)
    formatted_resume_path = os.path.join(company_dir, "formatted_resume.docx")
    process_resume(resume_path, job_data["content"], formatted_resume_path)

    # Create a zip file containing the job posting, the original DOCX, and the processed DOCX
    zip_filename = f"{company_name}_{job_title}.zip"
    zip_filepath = os.path.join(OUTPUT_DIR, zip_filename)
    with zipfile.ZipFile(zip_filepath, "w") as zipf:
        zipf.write(job_posting_path, os.path.basename(job_posting_path))
        zipf.write(resume_path, os.path.basename(resume_path))
        zipf.write(formatted_resume_path, os.path.basename(formatted_resume_path))

    # Return JSON response with redirect URL to the result page
    return JSONResponse(content={"redirect_url": f"/result?download_url=/download/{zip_filename}"})

@app.get("/result", response_class=HTMLResponse)
async def result_page(request: Request, download_url: str):
    """Serve the result page with a download button."""
    return templates.TemplateResponse("result.html", {"request": request, "download_url": download_url})

@app.get("/download/{zip_filename}")
async def download_zip(zip_filename: str):
    """Provides the generated zip file for download."""
    zip_filepath = os.path.join(OUTPUT_DIR, zip_filename)
    return FileResponse(zip_filepath, filename=zip_filename)