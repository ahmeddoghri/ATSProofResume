"""
This is a Docker-compatible version of the job_scraper.py file.
It will be used if the automatic patching fails.
"""
import os
import sys

def create_docker_compatible_job_scraper():
    """
    Create a Docker-compatible version of job_scraper.py if needed.
    """
    job_scraper_path = "job_scraper.py"
    
    if not os.path.exists(job_scraper_path):
        print(f"Error: {job_scraper_path} not found")
        return False
    
    with open(job_scraper_path, "r") as f:
        content = f.read()
    
    # Check if the file already has the Service import
    if "from selenium.webdriver.chrome.service import Service" not in content:
        # Add the import
        content = content.replace(
            "from selenium import webdriver",
            "from selenium import webdriver\nfrom selenium.webdriver.chrome.service import Service"
        )
    
    # Check if the file already has the Service usage
    if "service = Service(executable_path='/usr/bin/chromedriver')" not in content:
        # Find the capture_screenshot method
        if "def capture_screenshot" in content:
            # Replace any existing Chrome driver initialization
            content = content.replace(
                "driver = webdriver.Chrome(options=chrome_options)",
                "service = Service(executable_path='/usr/bin/chromedriver')\n        driver = webdriver.Chrome(service=service, options=chrome_options)"
            )
    
    # Write the updated content back to the file
    with open(job_scraper_path, "w") as f:
        f.write(content)
    
    print(f"Successfully updated {job_scraper_path} for Docker compatibility")
    return True

if __name__ == "__main__":
    success = create_docker_compatible_job_scraper()
    sys.exit(0 if success else 1) 