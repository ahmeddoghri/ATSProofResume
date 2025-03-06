"""
Unit tests for the resume package initialization.
"""
import unittest
import resume


class TestResumeInit(unittest.TestCase):
    """Test cases for resume package initialization."""

    def test_package_imports(self):
        """Test that the package imports correctly."""
        # Verify the package can be imported
        self.assertIsNotNone(resume)
        
        # If the package exports specific modules or classes, test those
        if hasattr(resume, 'ResumeProcessor'):
            self.assertIsNotNone(resume.ResumeProcessor)
        
        if hasattr(resume, 'ResumeWriter'):
            self.assertIsNotNone(resume.ResumeWriter)
        
        if hasattr(resume, 'ResumeParser'):
            self.assertIsNotNone(resume.ResumeParser)


if __name__ == '__main__':
    unittest.main() 