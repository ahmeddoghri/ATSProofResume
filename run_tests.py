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
        test_suite = test_loader.discover('tests', pattern='test_*.py')
        
        # Run the tests
        test_runner = unittest.TextTestRunner(verbosity=2)
        result = test_runner.run(test_suite)
        
        # Log test results
        logger.info(f"Tests run: {result.testsRun}")
        logger.info(f"Errors: {len(result.errors)}")
        logger.info(f"Failures: {len(result.failures)}")
        
        # Return True if all tests passed
        return result.wasSuccessful()
    except Exception as e:
        logger.error(f"Error running tests: {e}")
        return False

if __name__ == "__main__":
    # Run all tests
    success = run_all_tests()
    
    # Exit with appropriate status code
    sys.exit(0 if success else 1) 