"""
init file for the app
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

app = FastAPI()
app.include_router(api_router)