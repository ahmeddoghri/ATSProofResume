"""
This script patches the job_scraper.py file to work in Docker on ARM64 architecture.
"""
import os
import sys
import re

def patch_job_scraper():
    """
    Patch the job_scraper.py file to use the system-installed ChromeDriver.
    """
    job_scraper_path = "job_scraper.py"
    
    if not os.path.exists(job_scraper_path):
        print(f"Error: {job_scraper_path} not found")
        return False
    
    with open(job_scraper_path, "r") as f:
        content = f.read()
    
    # Check if the file is already patched
    if "service = Service(executable_path='/usr/bin/chromedriver')" in content:
        print(f"File {job_scraper_path} is already patched. No changes needed.")
        return True
    
    # Check if we're running in Docker
    if os.environ.get("SE_DISABLE_MANAGER") == "true":
        # Add import for Service if not already present
        if "from selenium.webdriver.chrome.service import Service" not in content:
            content = content.replace(
                "from selenium import webdriver",
                "from selenium import webdriver\nfrom selenium.webdriver.chrome.service import Service"
            )
        
        # Try different patterns for the Chrome driver initialization
        patterns = [
            r'(\s+)driver = webdriver\.Chrome\(options=chrome_options\)',
            r'(\s+)driver = webdriver\.Chrome\(\)',
            r'(\s+)driver = webdriver\.Chrome\(.*\)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                indentation = match.group(1)  # Capture the whitespace/indentation
                old_line = match.group(0)     # The entire matched line
                
                # Create the replacement with the same indentation
                new_lines = f"{indentation}service = Service(executable_path='/usr/bin/chromedriver')\n{indentation}driver = webdriver.Chrome(service=service, options=chrome_options)"
                
                # Replace while preserving indentation
                content = content.replace(old_line, new_lines)
                
                with open(job_scraper_path, "w") as f:
                    f.write(content)
                
                print(f"Successfully patched {job_scraper_path} for Docker with proper indentation")
                return True
        
        print(f"Could not find the Chrome driver initialization line in {job_scraper_path}")
        print("Creating a backup of the original file and writing a new version...")
        
        # If we can't find the pattern, create a backup and write a new version
        with open(f"{job_scraper_path}.bak", "w") as f:
            f.write(content)
        
        # Try to find the capture_screenshot method and replace it entirely
        screenshot_pattern = re.compile(r'def capture_screenshot.*?driver\.quit\(\)', re.DOTALL)
        match = screenshot_pattern.search(content)
        
        if match:
            method_text = match.group(0)
            indentation = re.match(r'^(\s*)', method_text).group(1)
            
            # Create a new version of the method with the correct Service usage
            new_method = f'''def capture_screenshot(self, url: str, output_path: str) -> None:
    """
    Captures a screenshot of a given URL.
    
    Args:
        url: URL to capture
        output_path: Path to save the screenshot
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    service = Service(executable_path='/usr/bin/chromedriver')
    driver = webdriver.Chrome(service=service, options=chrome_options)
    try:
        driver.get(url)
        driver.implicitly_wait(5)
        total_width = driver.execute_script("return document.body.scrollWidth")
        total_height = driver.execute_script("return document.body.scrollHeight")
        driver.set_window_size(total_width, total_height)
        driver.implicitly_wait(2)
        driver.save_screenshot(output_path)
    except Exception as e:
        self.logger.error(f"Screenshot capture failed: {{e}}")
        # Optionally, you can create a placeholder image here
    finally:
        driver.quit()'''
            
            # Replace the method
            content = content.replace(method_text, new_method)
            
            with open(job_scraper_path, "w") as f:
                f.write(content)
            
            print(f"Successfully replaced the capture_screenshot method in {job_scraper_path}")
            return True
        else:
            print(f"Could not find the capture_screenshot method in {job_scraper_path}")
            return False
    
    return False

if __name__ == "__main__":
    success = patch_job_scraper()
    sys.exit(0 if success else 1) 