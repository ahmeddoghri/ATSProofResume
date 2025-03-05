"""
init file for the app
"""
from fastapi import FastAPI
from .routes import router as api_router

app = FastAPI()
app.include_router(api_router)