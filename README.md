# ATS-Proof Resume Generator

An AI-powered tool that helps job seekers optimize their resumes for Applicant Tracking Systems (ATS) based on specific job descriptions.

## Features

- **Job Posting Analysis**: Automatically extracts key information from job postings
- **Resume Optimization**: Tailors your resume to match job requirements
- **ATS-Friendly Formatting**: Ensures your resume passes through ATS filters
- **Personalized Recommendations**: Provides specific suggestions to improve your resume
- **Interview Question Generator**: Creates custom interview questions based on the job and your resume

## Requirements

- Python 3.8 or higher
- OpenAI API key (for AI-powered features)
- Chrome/Chromium (for job posting screenshots)

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/ats-proof-resume.git
   cd ats-proof-resume
   ```

2. Run the setup script:
   ```
   chmod +x run.sh
   ./run.sh
   ```

   This will:
   - Create a virtual environment
   - Install all dependencies
   - Start the application

3. Open your browser and navigate to:
   ```
   http://localhost:8000
   ```

## Manual Setup

If you prefer to set up manually:

1. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run the application:
   ```
   uvicorn app.main:app --reload
   ```

## Usage

1. Enter your OpenAI API key (if not set as an environment variable)
2. Paste the URL of the job posting you're interested in
3. Upload your current resume (DOCX format)
4. Select the AI model and parameters
5. Click "Generate ATS-Proof Resume"
6. Download the optimized resume and recommendations

## Environment Variables

- `OPENAI_API_KEY`: Your OpenAI API key (optional, can be provided in the UI)

## Project Structure

## Testing with Docker

You can test the application in a clean Docker environment to ensure all dependencies are correctly specified:

### Using Docker Directly

1. Make sure Docker is installed on your system
2. Run the Docker test:
   ```
   ./run.sh --docker
   ```

### Using Docker Compose (Recommended)

1. Make sure Docker and Docker Compose are installed
2. Run:
   ```
   docker-compose up --build
   ```
   
This will:
- Build a Docker image with all dependencies
- Run the application in a container
- Make it available at http://localhost:8000
- Mount the output directory so you can access generated files

If the application starts successfully in Docker, your requirements.txt is complete.

## Testing Dependencies

To verify that all required packages can be imported:
