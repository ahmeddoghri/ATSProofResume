"""
This is the main file for the application.
It is used to run the application.
"""
from app import app  # app is created in app/__init__.py

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
