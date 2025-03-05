"""
Main entry point for the ATS-Proof Resume application.
"""
from fastapi import FastAPI
from .routes import router as api_router
import logging
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("app.log")
    ]
)

# Create output directory
from .state import OUTPUT_DIR
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Create FastAPI app
app = FastAPI(
    title="ATS-Proof Resume Generator",
    description="An AI-powered tool that helps job seekers optimize their resumes for Applicant Tracking Systems (ATS)",
    version="1.0.0"
)

# Include API routes
app.include_router(api_router)

# Add startup event
@app.on_event("startup")
async def startup_event():
    logging.info("Application startup")

# Add shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    logging.info("Application shutdown") 