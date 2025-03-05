"""
Test script to verify that all required packages can be imported.
"""
import importlib
import sys
import os

def test_imports(skip_app_modules=False):
    """Test that all required packages can be imported."""
    required_packages = [
        # Web Framework
        "fastapi",
        "uvicorn",
        "jinja2",
        
        # AI and NLP
        "openai",
        "langchain",
        "langchain_openai",
        
        # Document Processing
        "docx",
        "markdown",
        
        # Web Scraping
        "requests",
        "bs4",
        "selenium",
        "webdriver_manager",
        
        # Utilities
        "dotenv",
        "pydantic",
    ]
    
    # Add application modules only if not skipping them
    if not skip_app_modules:
        app_modules = [
            # Application modules
            "app",
            "resume",
            "job_scraper",
            "recommendations",
            "interview_questions"
        ]
        required_packages.extend(app_modules)
    
    # Special case for python-multipart which doesn't have a direct import
    try:
        # Just check if the module exists
        import multipart
        print(f"✅ Successfully verified python-multipart")
    except ImportError as e:
        print(f"❌ Failed to verify python-multipart: {e}")
    
    missing_packages = []
    
    for package in required_packages:
        try:
            importlib.import_module(package)
            print(f"✅ Successfully imported {package}")
        except ImportError as e:
            missing_packages.append((package, str(e)))
            print(f"❌ Failed to import {package}: {e}")
    
    if missing_packages:
        print("\n❌ The following packages could not be imported:")
        for package, error in missing_packages:
            print(f"  - {package}: {error}")
        return False
    else:
        print("\n✅ All packages imported successfully!")
        return True

if __name__ == "__main__":
    # Check if we should skip app modules (useful for Docker build)
    skip_app = os.environ.get("SKIP_APP_MODULES", "").lower() in ("true", "1", "yes")
    success = test_imports(skip_app_modules=skip_app)
    sys.exit(0 if success else 1) 