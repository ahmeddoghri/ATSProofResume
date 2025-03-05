import time

def timed_cache(seconds: int):
    """Decorator to cache function results for a specified duration."""
    def wrapper_decorator(func):
        """Wrapper function to cache results."""
        cache = {}
        
        async def wrapped_func(*args, **kwargs):
            """Async wrapper function to cache results."""
            key = str(args) + str(kwargs)
            now = time.time()
            
            if key in cache:
                result, timestamp = cache[key]
                if now - timestamp < seconds:
                    return result
                
            # Get new result
            result = await func(*args, **kwargs)
            cache[key] = (result, now)
            return result
            
        return wrapped_func
    return wrapper_decorator
