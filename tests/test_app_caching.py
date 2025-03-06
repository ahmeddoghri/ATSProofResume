"""
Unit tests for the app caching module.
"""
import unittest
from unittest.mock import AsyncMock, patch
import asyncio
import time
from app.caching import timed_cache


class TestAppCaching(unittest.TestCase):
    """Test cases for app caching."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a mock function to cache
        self.mock_func = AsyncMock()
        self.mock_func.return_value = "test_result"
        
        # Apply the cache decorator
        self.cached_func = timed_cache(seconds=1)(self.mock_func)
    
    def test_cache_decorator(self):
        """Test the timed cache decorator."""
        # Run the test in an event loop
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._test_cache_async())
    
    async def _test_cache_async(self):
        """Async test for the cache decorator."""
        # First call should execute the function
        result1 = await self.cached_func("arg1", kwarg1="value1")
        self.assertEqual(result1, "test_result")
        self.mock_func.assert_called_once_with("arg1", kwarg1="value1")
        
        # Reset the mock to verify it's not called again
        self.mock_func.reset_mock()
        
        # Second call with same args should use cached result
        result2 = await self.cached_func("arg1", kwarg1="value1")
        self.assertEqual(result2, "test_result")
        self.mock_func.assert_not_called()
        
        # Call with different args should execute the function
        result3 = await self.cached_func("arg2", kwarg1="value1")
        self.assertEqual(result3, "test_result")
        self.mock_func.assert_called_once_with("arg2", kwarg1="value1")
        
        # Wait for cache to expire
        await asyncio.sleep(1.1)
        
        # Call again should execute the function
        self.mock_func.reset_mock()
        result4 = await self.cached_func("arg1", kwarg1="value1")
        self.assertEqual(result4, "test_result")
        self.mock_func.assert_called_once_with("arg1", kwarg1="value1")


if __name__ == '__main__':
    unittest.main() 