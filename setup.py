"""
Setup script for ATS-Proof Resume application.
"""
from setuptools import setup, find_packages

setup(
    name="ats-proof-resume",
    version="1.1.0",
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
    extras_require={
        # The audit engine needs only python-docx. Keeping it installable on
        # its own means the free, offline half of the tool carries no
        # dependency on OpenAI, Selenium, or a web server.
        "audit": ["python-docx>=0.8.11"],
    },
    entry_points={
        "console_scripts": [
            "ats=ats.cli:main",
        ],
    },
)
