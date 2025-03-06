"""
Unit tests for the app state module.
"""
import unittest
import os
from app.state import progress_status, jobs_db, OUTPUT_DIR


class TestAppState(unittest.TestCase):
    """Test cases for app state."""

    def test_state_initialization(self):
        """Test that state variables are properly initialized."""
        # Verify progress_status is an empty dict
        self.assertIsInstance(progress_status, dict)
        self.assertEqual(len(progress_status), 0)
        
        # Verify jobs_db is an empty dict
        self.assertIsInstance(jobs_db, dict)
        self.assertEqual(len(jobs_db), 0)
        
        # Verify OUTPUT_DIR is a string
        self.assertIsInstance(OUTPUT_DIR, str)
        self.assertEqual(OUTPUT_DIR, "output")


if __name__ == '__main__':
    unittest.main() 