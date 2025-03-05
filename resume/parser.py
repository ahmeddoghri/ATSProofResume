"""
Handles parsing and extracting information from resumes
"""
import logging


class ResumeParser:
    """Handles parsing and extracting information from resumes"""
    
    @staticmethod
    def parse_date(date_str):
        """
        Parse a date string in MM/YYYY format and return a tuple (year, month) for sorting.
        
        Args:
            date_str: A date string in MM/YYYY format
            
        Returns:
            tuple: (year, month) for sorting purposes
        """
        try:
            if '/' in date_str:
                month, year = date_str.strip().split('/')
                return (int(year), int(month))
            else:
                # Handle case where only year is provided
                return (int(date_str.strip()), 1)
        except (ValueError, IndexError):
            # Return a default value for unparseable dates
            logging.warning(f"Could not parse date: {date_str}")
            return (0, 0)
