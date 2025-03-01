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

from openai import OpenAI
from typing import List, Dict
from functools import lru_cache
import asyncio
from datetime import datetime, timedelta
from functools import wraps
import time


app = FastAPI() 
templates = Jinja2Templates(directory="templates")
OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Global dictionary to store progress status keyed by job ID
progress_status = {}



def timed_cache(seconds: int):
    def wrapper_decorator(func):
        cache = {}
        
        async def wrapped_func(*args, **kwargs):
            key = str(args) + str(kwargs)
            now = time.time()
            
            if key in cache:
                result, timestamp = cache[key]
                if now - timestamp < seconds:
                    return result
                
            # Get new result
            result = await func(*args, **kwargs)
            cache[key] = (result, now)
            return result
            
        return wrapped_func
    return wrapper_decorator



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


def get_fallback_models() -> List[Dict]:
    """
    Returns a basic list of chat-compatible models as fallback.
    """
    return [
        {
            "id": "gpt-4.5-preview",
            "name": "gpt-4.5-preview",
            "provider": "OpenAI",
            "recommended": False,
            "category": "Advanced",
            "description": "Latest and most advanced GPT model"
        },
        {
            "id": "gpt-4o",
            "name": "gpt-4o",
            "provider": "OpenAI",
            "recommended": True,
            "category": "Advanced",
            "description": "Optimized version of GPT-4"
        },
        {
            "id": "gpt-4o-mini",
            "name": "gpt-4o-mini",
            "provider": "OpenAI",
            "recommended": False,
            "category": "Advanced",
            "description": "Lighter version of GPT-4 Optimized"
        },
        {
            "id": "gpt-4-turbo",
            "name": "gpt-4-turbo",
            "provider": "OpenAI",
            "recommended": False,
            "category": "Advanced",
            "description": "Older high intelligence GPT-4 Model"
        },
        {
            "id": "gpt-3.5-turbo",
            "name": "gpt-3.5-turbo",
            "provider": "OpenAI",
            "recommended": False,
            "category": "Standard",
            "description": "Fast and cost-effective for simpler tasks"
        }
    ]


def get_model_description(model_id: str) -> str:
    """
    Returns a description based on the model ID.
    """
    descriptions = {
        "gpt-4": "Most capable GPT-4 model for complex tasks",
        "gpt-4-turbo": "Optimized GPT-4 model for faster response times",
        "gpt-3.5-turbo": "Fast and cost-effective for most tasks",
    }
    
    # Find the matching description based on partial model ID
    for key, desc in descriptions.items():
        if key in model_id:
            return desc
    
    return "OpenAI language model"

def get_friendly_model_name(model_id: str) -> str:
    """
    Returns the original model ID without modification.
    This ensures we display exactly what the API returns.
    """
    return model_id

# Add a function to clear the cache
def clear_model_cache():
    """Clear the model cache to force a refresh"""
    fetch_openai_models.cache = {}  # Reset the cache dictionary

# Update the excluded models list to be more comprehensive
excluded_models = [
    'whisper', 'dall-e', 'tts', 'text-embedding', 'audio',
    'text-moderation', 'instruct', 'vision', 'realtime',
    'preview-2024', 'preview-2023', '-1106', '-0125', '-0613',
    '-16k', '-mini-realtime', '-realtime', '-audio'
]

# Update the fetch_openai_models function with stronger filtering
@timed_cache(seconds=3600)
async def fetch_openai_models(api_key: str) -> List[Dict]:
    """
    Fetches available models from OpenAI and returns only chat-compatible models.
    """
    try:
        client = OpenAI(api_key=api_key)
        models = client.models.list()
        
        # List of known chat-compatible model prefixes
        chat_model_prefixes = [
            'gpt-4-', 'gpt-4o', 'gpt-3.5-turbo'
        ]
        
        # Filter for chat models and format them
        chat_models = []
        seen_model_ids = set()  # Track models we've already added
        
        # First add our preferred models in the order we want
        preferred_models = [
            "gpt-4.5-preview",
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4-turbo",
            "gpt-3.5-turbo"
        ]
        
        # Add preferred models first if they exist in the API response
        model_ids = [model.id for model in models.data]
        for preferred_id in preferred_models:
            matching_ids = [mid for mid in model_ids if preferred_id in mid and 
                           not any(excluded in mid.lower() for excluded in excluded_models)]
            if matching_ids:
                # Use the most recent version if multiple matches
                model_id = sorted(matching_ids)[-1]
                
                # Use simple descriptions based on model family
                if "gpt-4.5" in model_id:
                    description = "Latest and most advanced GPT model"
                elif "gpt-4o" in model_id and "mini" in model_id:
                    description = "Lighter version of GPT-4 Optimized"
                elif "gpt-4o" in model_id:
                    description = "Optimized version of GPT-4"
                elif "gpt-4-turbo" in model_id:
                    description = "Older high intelligence GPT-4 Model"
                elif "gpt-3.5" in model_id:
                    description = "Fast and cost-effective for simpler tasks"
                else:
                    description = "OpenAI language model"
                
                model_info = {
                    "id": model_id,
                    "name": model_id,  # Use the exact model ID
                    "provider": "OpenAI",
                    "recommended": "gpt-4o" in model_id and not "mini" in model_id,
                    "category": "Advanced" if "gpt-4" in model_id else "Standard",
                    "description": description
                }
                chat_models.append(model_info)
                seen_model_ids.add(model_id)
        
        # Then add any remaining models - but be very selective
        for model in models.data:
            model_id = model.id
            
            # Skip if we've already added this model
            if model_id in seen_model_ids:
                continue
                
            # Check if this is a chat model and doesn't contain any excluded terms
            is_chat_model = any(model_id.startswith(prefix) for prefix in chat_model_prefixes)
            is_excluded = any(excluded in model_id.lower() for excluded in excluded_models)
            
            # Only include base models without special capabilities or version numbers
            if is_chat_model and not is_excluded:
                # Skip models with date suffixes if we already have a similar model
                base_model = model_id.split('-2023')[0].split('-2024')[0].split('-0')[0]
                if any(base_model in seen_id for seen_id in seen_model_ids):
                    continue
                
                # Simple description based on model family
                if "gpt-4" in model_id:
                    description = "GPT-4 model variant"
                elif "gpt-3.5" in model_id:
                    description = "GPT-3.5 model variant"
                else:
                    description = "OpenAI language model"
                
                model_info = {
                    "id": model_id,
                    "name": model_id,  # Use the exact model ID
                    "provider": "OpenAI",
                    "recommended": False,
                    "category": "Advanced" if "gpt-4" in model_id else "Standard",
                    "description": description
                }
                chat_models.append(model_info)
                seen_model_ids.add(model_id)
        
        # If no chat models found, return fallback
        if not chat_models:
            return get_fallback_models()
            
        return sorted(
            chat_models,
            key=lambda x: (
                not x["recommended"],  # Recommended models first
                x["category"] != "Advanced",  # Advanced models first
                x["name"]  # Alphabetical within same category
            )
        )
    except Exception as e:
        print(f"Error fetching OpenAI models: {e}")
        return get_fallback_models()

@app.get("/available_models")
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
    
