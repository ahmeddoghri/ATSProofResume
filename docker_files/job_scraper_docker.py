"""
This is a Docker-compatible version of the job_scraper.py file.
It will be used if the automatic patching fails.
"""
import os
import sys
import re
import time
from PIL import Image, ImageDraw
import logging

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
    
    # Replace the capture_screenshot method with our full-page version
    screenshot_pattern = re.compile(r'def capture_screenshot.*?pass\n', re.DOTALL)
    match = screenshot_pattern.search(content)
    
    if match:
        method_text = match.group(0)
        
        # Create a new version of the method with full-page screenshot capability
        new_method = '''def capture_screenshot(self, url, output_path):
    """
    Captures a full-page screenshot of the job posting page.
    Scrolls to capture all content and falls back to a placeholder if WebDriver is not available.
    """
    try:
        # Use webdriver_manager to automatically download and manage ChromeDriver
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        # For Docker environment
        service = Service(executable_path='/usr/bin/chromedriver')
        
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.get(url)
        
        # Wait for page to load
        time.sleep(3)
        
        # Get the dimensions of the page
        total_width = driver.execute_script("return document.body.offsetWidth")
        total_height = driver.execute_script("return document.body.scrollHeight")
        
        # Set window size to capture everything
        driver.set_window_size(total_width, total_height)
        
        # Scroll through the page to ensure all lazy-loaded content is loaded
        current_height = 0
        while current_height < total_height:
            driver.execute_script(f"window.scrollTo(0, {current_height});")
            current_height += 500  # Scroll by 500px each time
            time.sleep(0.2)  # Small delay to allow content to load
        
        # Scroll back to top
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(0.5)
        
        # Take the screenshot
        driver.save_screenshot(output_path)
        driver.quit()
        logging.info(f"Full page screenshot captured and saved to {output_path}")
        
    except Exception as e:
        logging.error(f"Failed to capture screenshot: {str(e)}")
        # Create a placeholder image or skip screenshot
        try:
            # Create a simple placeholder image
            img = Image.new('RGB', (800, 400), color=(245, 247, 250))
            d = ImageDraw.Draw(img)
            d.text((400, 200), "Screenshot Unavailable", fill=(100, 100, 100), anchor="mm")
            img.save(output_path)
            logging.info(f"Created placeholder image at {output_path}")
        except Exception as img_error:
            logging.error(f"Could not create placeholder image: {str(img_error)}")
            # If we can't even create a placeholder, just skip this step
            pass
'''
        
        # Replace the method
        content = content.replace(method_text, new_method)
        
        with open(job_scraper_path, "w") as f:
            f.write(content)
        
        print(f"Successfully updated {job_scraper_path} with full-page screenshot capability")
        return True
    
    return False

if __name__ == "__main__":
    success = create_docker_compatible_job_scraper()
    sys.exit(0 if success else 1) 