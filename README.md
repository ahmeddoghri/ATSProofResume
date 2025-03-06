# ATS-Proof Resume Generator

**Transform your job application game. Forever.**

An AI-powered tool that doesn't just optimize your resume—it weaponizes it against Applicant Tracking Systems (ATS) to ensure you get past the digital gatekeepers and into human hands.

> "The difference between a good resume and a great one isn't just content—it's strategic alignment with what machines and humans are looking for."

## What This Tool Actually Does

- **Job Posting Analysis**: Extracts the critical signals from job descriptions that most candidates miss
- **Resume Optimization**: Restructures your experience to mirror exactly what employers want to see
- **ATS-Friendly Formatting**: Implements the hidden formatting rules that make your resume machine-readable
- **Personalized Recommendations**: Provides tactical suggestions that close the gap between you and the ideal candidate
- **Interview Question Generator**: Creates custom questions that let you control the conversation during interviews

## The Technical Requirements

- Python 3.8 or higher
- OpenAI API key (for the AI-powered features)
- Chrome/Chromium (for capturing job posting screenshots)

## Installation Options

### Option 1: One-Command Setup (Recommended)

The fastest path from zero to running:

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

### Option 2: Manual Setup

If you prefer control over each step:

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

### Option 3: Docker Deployment

For a completely isolated, reproducible environment:

1. Make sure Docker and Docker Compose are installed
2. Build and run with Docker Compose:
   ```
   docker-compose up --build
   ```

This setup includes:
- A Selenium container for handling web scraping
- The main application container
- Proper networking between containers
- Volume mounting for the output directory

### Option 4: Docker with ARM64 Architecture (M1/M2 Macs)

If you're running on an ARM-based machine like an M1/M2 Mac:

1. The Docker setup is configured to handle ARM64 architecture automatically
2. The application uses a remote Selenium WebDriver to avoid compatibility issues
3. No additional configuration is needed - just run:
   ```
   docker-compose up --build
   ```

## How to Actually Use This Tool

1. Enter your OpenAI API key (if not set as an environment variable)
2. Paste the URL of the job posting you're targeting
3. Upload your current resume (DOCX format only)
4. Select the AI model and parameters (see model recommendations below)
5. Click "Generate ATS-Proof Resume"
6. Download your weaponized resume package

## Model Selection Guide

The choice of LLM model significantly impacts your results. After extensive testing:

- **o1-mini**: Offers the best balance of performance and cost. Handles complex resume restructuring with excellent accuracy.
- **gpt-4o**: Provides slightly more creative rewrites but at higher cost.
- **gpt-3.5-turbo**: Acceptable for basic resumes but may struggle with complex career histories.

**Important**: The application currently processes your entire resume in a single LLM call. This approach works well with modern models but may hit token limits with extremely lengthy resumes.

## XML Format Requirements

The system relies on a specific XML-like format for processing resumes. The LLM is instructed to output in this format, but occasionally issues may occur.

Example of Correct Format:
```xml
<resume>
  <header>
    <name>John Smith</name>
    <contact>
      <email>john.smith@example.com</email>
      <phone>(555) 123-4567</phone>
      <location>San Francisco, CA</location>
      <linkedin>linkedin.com/in/johnsmith</linkedin>
    </contact>
  </header>
  <summary>
    Experienced software engineer with 5+ years specializing in cloud infrastructure and distributed systems...
  </summary>
  <experience>
    <job>
      <title>Senior Software Engineer</title>
      <company>Tech Innovations Inc.</company>
      <date>January 2020 - Present</date>
      <achievements>
        <item>Redesigned microservice architecture reducing latency by 40%</item>
        <item>Led team of 5 engineers in developing new payment processing system</item>
        <!-- Additional achievements -->
      </achievements>
    </job>
    <!-- Additional jobs -->
  </experience>
  <!-- Additional sections -->
</resume>
```

### Troubleshooting Format Issues:

If you encounter format problems:
- Try a different model (o1-mini tends to follow formatting instructions most consistently)
- Reduce the temperature setting to 0.1-0.3 for more deterministic outputs
- Ensure your original resume is properly formatted in the DOCX file
- Check the application logs for specific error messages

## Environment Variables

- `OPENAI_API_KEY`: Your OpenAI API key (optional, can be provided in the UI)
- `SELENIUM_REMOTE_URL`: URL for remote Selenium WebDriver (used in Docker setup)
- `SE_DISABLE_MANAGER`: Disables Selenium Manager to use system-installed ChromeDriver

## Advanced Usage: Running Options Explained

The `run.sh` script provides several execution modes:

### Standard Mode
```
./run.sh
```

Creates a Python virtual environment, installs dependencies, and runs the application locally.

### Testing Mode
```
./run.sh --test
```

Verifies all dependencies are correctly installed without starting the application.

### Docker Mode
```
./run.sh --docker
```

Builds and runs the application in a Docker container, providing complete isolation from your system.

### Help Mode
```
./run.sh --help
```

Displays available options and usage information.

## Troubleshooting Docker Issues

### ARM64 Architecture (M1/M2 Macs)

The application is configured to work on ARM64 architecture using:
- A Selenium container specifically designed for ARM64
- Remote WebDriver configuration to avoid compatibility issues
- Platform-specific settings in docker-compose.yml

### Chrome/Selenium Issues

If you encounter Chrome or Selenium-related errors:
1. Make sure both containers are running: `docker-compose ps`
2. Check the Selenium container logs: `docker-compose logs selenium`
3. Verify the SELENIUM_REMOTE_URL environment variable is set correctly
4. Try rebuilding both containers: `docker-compose down && docker-compose up --build`

### Resume Processing Errors

If you see "Resume rewriting failed" errors:
1. Check that your OpenAI API key is valid and has sufficient credits
2. Verify your resume is in a valid DOCX format
3. Try a different model or reduce the temperature setting
4. Check the application logs for detailed error messages

## Troubleshooting Chrome/Selenium Issues in Docker

### DevToolsActivePort File Error

If you see an error like this in your logs:
```
Failed to capture screenshot: Message: unknown error: Chrome failed to start: exited abnormally.
(unknown error: DevToolsActivePort file doesn't exist)
(The process started from chrome location /usr/bin/chromium is no longer running, so ChromeDriver is assuming that Chrome has crashed.)
```

This is a common issue when running Chrome in Docker containers. Here's how to fix it:

#### Solution 1: Update Chrome Options

Modify the `job_scraper.py` file to add these additional Chrome options:

```python
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument("--disable-dev-tools")
chrome_options.add_argument("--remote-debugging-port=9222")
```

#### Solution 2: Use the Selenium Container

The application is configured to use a separate Selenium container when running with Docker Compose. Make sure:

1. Both containers are running:
   ```bash
   docker-compose ps
   ```

2. The environment variable is set correctly in docker-compose.yml:
   ```yaml
   environment:
     - SELENIUM_REMOTE_URL=http://selenium:4444/wd/hub
   ```

3. The Selenium container has enough shared memory:
   ```yaml
   shm_size: 2g
   ```

#### Solution 3: Rebuild with Updated Docker Configuration

If you've made changes to fix the issue:

```bash
docker-compose down
docker-compose up --build
```

#### Solution 4: Check for ARM64 Compatibility

If you're running on an ARM-based system (like M1/M2 Mac):

1. Make sure you're using the ARM-compatible Selenium image:
   ```yaml
   selenium:
     image: seleniarm/standalone-chromium:latest
   ```

2. Set the platform for your app container:
   ```yaml
   app:
     platform: linux/amd64
   ```

The application is designed to fall back to creating a placeholder image when screenshot capture fails, so your resume processing should still work even if screenshots cannot be captured.

## The Philosophy Behind This Tool

Most resume tools focus on cosmetic improvements. This one doesn't.

This tool operates on the principle that modern job applications are a two-audience game: you need to satisfy both the algorithm and the human. By analyzing the specific language patterns in job descriptions and restructuring your experience to match, you're not just "keyword stuffing"—you're translating your value into the exact dialect the employer speaks.

The difference is subtle but critical.

## Course Connection

This tool was developed as part of the "Modern Job Application Mastery" course. For a complete walkthrough of how to maximize your results with this tool and the broader strategies for modern job hunting, visit coursename.com.

## Final Thoughts

Your resume isn't just a document—it's the most important piece of marketing you'll ever create for yourself.

Use this tool not as a magic bullet, but as a strategic advantage in a game where most people don't even know the rules. The difference between getting filtered out and getting called back often comes down to how well you speak the language of both the machines and the humans who make hiring decisions.

---

## For Developers: Project Structure

```
ats-proof-resume/
├── app/                  # Main application code
│   ├── __init__.py
│   ├── main.py           # FastAPI application entry point
│   ├── routes.py         # API endpoints
│   ├── state.py          # Application state management
│   └── tasks.py          # Background processing tasks
├── resume/               # Resume processing logic
│   ├── __init__.py
│   └── processor.py      # AI-powered resume optimization
├── job_scraper.py        # Job posting scraping functionality
├── interview_questions.py # Interview question generation
├── recommendations.py    # Personalized recommendation generation
├── Dockerfile            # Main Docker configuration
├── Dockerfile.selenium   # Selenium-specific Docker configuration
├── docker-compose.yml    # Multi-container Docker setup
├── docker_fix.py         # Docker compatibility script for ARM64
├── requirements.txt      # Python dependencies
├── run.sh                # Main execution script
├── test_deps.py          # Dependency testing script
└── test_imports.py       # Import verification script
```

## Contributing

Contributions that push the boundaries of what's possible in modern job applications are welcome. Before submitting a PR:

- Ensure your code follows the project's style guidelines
- Add tests for new functionality
- Update documentation to reflect your changes

## License

This project is licensed under the MIT License - see the LICENSE file for details.
