"""
Unit tests for app utility functions.
"""
import unittest
from unittest.mock import patch, MagicMock, mock_open
import os
import tempfile
from app.utils import (
    extract_text_from_docx,
    sanitize_filename,
    format_markdown_for_text
)


class TestAppUtils(unittest.TestCase):
    """Test cases for app utility functions."""

    @patch('docx.Document')
    def test_extract_text_from_docx(self, mock_document):
        """Test extracting text from a DOCX file."""
        # Mock Document instance
        mock_doc = MagicMock()
        mock_document.return_value = mock_doc
        
        # Mock paragraphs
        mock_paragraphs = [
            MagicMock(text="Paragraph 1"),
            MagicMock(text=""),  # Empty paragraph
            MagicMock(text="Paragraph 2"),
            MagicMock(text="  "),  # Whitespace-only paragraph
            MagicMock(text="Paragraph 3")
        ]
        mock_doc.paragraphs = mock_paragraphs
        
        # Create a temporary file
        with tempfile.NamedTemporaryFile(suffix='.docx') as temp_file:
            result = extract_text_from_docx(temp_file.name)
            
            # Verify the result
            self.assertEqual(result, "Paragraph 1\nParagraph 2\nParagraph 3")
            
            # Verify Document was called with the correct path
            mock_document.assert_called_once_with(temp_file.name)
    
    def test_sanitize_filename(self):
        """Test sanitizing filenames."""
        # Test with invalid characters
        self.assertEqual(sanitize_filename("file/with\\invalid:chars"), "file_with_invalid_chars")
        
        # Test with spaces
        self.assertEqual(sanitize_filename("file with spaces"), "file_with_spaces")
        
        # Test with long filename (should truncate)
        long_name = "very" + "long" * 30
        result = sanitize_filename(long_name)
        self.assertLessEqual(len(result), 100)  # Assuming max length is 100
        self.assertTrue(result.startswith("verylong"))
    
    def test_format_markdown_for_text(self):
        """Test converting markdown to plain text formatting."""
        markdown = """
        # Heading 1
        
        ## Heading 2
        
        This is **bold** and *italic* text.
        
        - Bullet 1
        - Bullet 2
        
        1. Numbered item
        2. Another numbered item
        
        ---
        
        ```
        Code block
        ```
        """
        
        result = format_markdown_for_text(markdown)
        
        # Verify headings are converted
        self.assertIn("HEADING 1", result)
        self.assertIn("HEADING 2", result)
        
        # Verify formatting is converted
        self.assertIn("bold", result)
        self.assertIn("italic", result)
        
        # Verify lists are converted
        self.assertIn("* Bullet 1", result)
        self.assertIn("* Bullet 2", result)
        self.assertIn("1. Numbered item", result)
        self.assertIn("2. Another numbered item", result)
        
        # Verify horizontal rule is converted
        self.assertIn("-" * 60, result)


if __name__ == '__main__':
    unittest.main() 