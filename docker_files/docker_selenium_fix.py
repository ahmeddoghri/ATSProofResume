"""
Fix script for Selenium in Docker environment.
"""
import os
import sys
import subprocess
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_selenium_in_docker():
    """
    Configure Selenium to work properly in Docker environment.
    """
    # Check if we're in Docker - look for indicators like /usr/bin/chromium
    # rather than relying solely on an environment variable
    if os.path.exists('/usr/bin/chromium') and os.path.exists('/usr/bin/chromedriver'):
        logger.info("Detected Docker environment, applying Selenium fixes")
        # Set the environment variable for other parts of the application
        os.environ['DOCKER_ENV'] = 'true'
    else:
        logger.info("Not running in Docker, skipping Selenium fixes")
        return True
    
    # Verify ChromeDriver is installed and executable
    chromedriver_path = '/usr/bin/chromedriver'
    if not os.path.exists(chromedriver_path):
        logger.error(f"ChromeDriver not found at {chromedriver_path}")
        return False
    
    # Make sure ChromeDriver is executable
    try:
        os.chmod(chromedriver_path, 0o755)
        logger.info(f"Set executable permissions on {chromedriver_path}")
    except Exception as e:
        logger.error(f"Failed to set permissions on ChromeDriver: {e}")
        # Continue anyway, it might already be executable
    
    # Verify Chrome/Chromium is installed
    chrome_path = '/usr/bin/chromium'
    if not os.path.exists(chrome_path):
        logger.error(f"Chromium not found at {chrome_path}")
        return False
    
    # Test ChromeDriver
    try:
        result = subprocess.run(
            [chromedriver_path, '--version'], 
            capture_output=True, 
            text=True, 
            timeout=5
        )
        logger.info(f"ChromeDriver version: {result.stdout.strip()}")
    except Exception as e:
        logger.error(f"Failed to get ChromeDriver version: {e}")
        # This is a warning but not a failure
    
    logger.info("Selenium Docker fixes applied successfully")
    return True

if __name__ == "__main__":
    success = fix_selenium_in_docker()
    sys.exit(0 if success else 1)