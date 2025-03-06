"""
Test runner for all unit tests.
"""
import unittest
import sys
import os
import logging

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_all_tests():
    """Run all unit tests and return success status."""
    # Discover and run all tests
    test_loader = unittest.TestLoader()
    
    # Try to discover tests
    try:
        # First run the core tests that don't depend on web frameworks
        core_test_suite = test_loader.discover('tests', pattern='test_resume_*.py')
        
        # Run the core tests
        test_runner = unittest.TextTestRunner(verbosity=2)
        core_result = test_runner.run(core_test_suite)
        
        # Log core test results
        logger.info(f"Core tests run: {core_result.testsRun}")
        logger.info(f"Core errors: {len(core_result.errors)}")
        logger.info(f"Core failures: {len(core_result.failures)}")
        
        # Try to run the web-dependent tests if dependencies are available
        try:
            # Check if required packages are installed
            import multipart
            import webdriver_manager
            import pytest
            
            # Run the remaining tests
            web_test_suite = test_loader.discover('tests', pattern='test_app_*.py')
            web_result = test_runner.run(web_test_suite)
            
            # Log web test results
            logger.info(f"Web tests run: {web_result.testsRun}")
            logger.info(f"Web errors: {len(web_result.errors)}")
            logger.info(f"Web failures: {len(web_result.failures)}")
            
            # Combine results
            total_tests = core_result.testsRun + web_result.testsRun
            total_errors = len(core_result.errors) + len(web_result.errors)
            total_failures = len(core_result.failures) + len(web_result.failures)
            
            logger.info(f"Total tests run: {total_tests}")
            logger.info(f"Total errors: {total_errors}")
            logger.info(f"Total failures: {total_failures}")
            
            return total_errors == 0 and total_failures == 0
            
        except ImportError as e:
            logger.warning(f"Skipping web-dependent tests due to missing dependencies: {e}")
            return core_result.wasSuccessful()
            
    except Exception as e:
        logger.error(f"Error running tests: {e}")
        return False

if __name__ == "__main__":
    # Run all tests
    success = run_all_tests()
    
    # Exit with appropriate status code
    sys.exit(0 if success else 1) 