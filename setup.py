"""
Setup script for ATS-Proof Resume application.
"""
from setuptools import setup, find_packages

setup(
    name="ats-proof-resume",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "uvicorn",
        "python-multipart",
        "openai",
        "python-docx",
        "requests",
        "beautifulsoup4",
        "selenium",
        "webdriver-manager",
        "pytest",
        "httpx",
    ],
) 