from openai import OpenAI
from typing import List

from openai import OpenAI
from typing import List, Dict
from app.caching import timed_cache


def get_fallback_models():
    """Returns a list of fallback models if API key is not provided or there's an error."""
    return [
        {
            "id": "o1-mini",
            "name": "O1-Mini",
            "description": "Efficient reasoning model for most tasks",
            "category": "Reasoning",
            "recommended": True  # Set as recommended/default
        },
        {
            "id": "o1-preview",
            "name": "O1 Preview",
            "description": "Advanced reasoning model with step-by-step thinking",
            "category": "Reasoning",
            "recommended": False
        },
        {
            "id": "o1",
            "name": "O1",
            "description": "Full reasoning model for complex tasks",
            "category": "Reasoning",
            "recommended": False
        },
        {
            "id": "o3-mini",
            "name": "O3-Mini",
            "description": "Compact reasoning model with strong capabilities",
            "category": "Reasoning",
            "recommended": False
        },
        {
            "id": "gpt-4o",
            "name": "GPT-4o",
            "description": "Latest and most advanced GPT model",
            "category": "Advanced",
            "recommended": False  # No longer the default
        }
    ]


def get_model_description(model_id: str) -> str:
    """
    Returns a description based on the model ID.
    """
    descriptions = {
        "gpt-4": "Most capable GPT-4 model for complex tasks",
        "gpt-4-turbo": "Optimized GPT-4 model for faster response times",
        "gpt-3.5-turbo": "Fast and cost-effective for most tasks",
    }
    
    # Find the matching description based on partial model ID
    for key, desc in descriptions.items():
        if key in model_id:
            return desc
    
    return "OpenAI language model"

def get_friendly_model_name(model_id: str) -> str:
    """
    Returns the original model ID without modification.
    This ensures we display exactly what the API returns.
    """
    return model_id

# Add a function to clear the cache
def clear_model_cache():
    """Clear the model cache to force a refresh"""
    fetch_openai_models.cache = {}  # Reset the cache dictionary

# Update the excluded_models list to ensure reasoning models aren't filtered out
excluded_models = [
    'whisper', 'dall-e', 'tts', 'text-embedding', 'audio',
    'text-moderation', 'instruct', 'vision', 'realtime',
    'preview-2024', 'preview-2023', '-1106', '-0125', '-0613',
    '-16k', '-mini-realtime', '-realtime', '-audio'
]

# Update the fetch_openai_models function to deduplicate models
@timed_cache(seconds=300)
async def fetch_openai_models(api_key: str) -> List[Dict]:
    """
    Fetches available OpenAI models with caching.
    Returns a list of model info dictionaries.
    """
    try:
        # List of model types to exclude
        excluded_models = [
            'whisper', 'dall-e', 'tts', 'text-embedding', 'audio',
            'text-moderation', 'instruct', 'vision', 'realtime',
            'preview-2024', 'preview-2023', '-1106', '-0125', '-0613',
            '-16k', '-mini-realtime', '-realtime', '-audio'
        ]
        
        client = OpenAI(api_key=api_key)
        models = client.models.list()
        
        # List of known chat-compatible model prefixes
        chat_model_prefixes = [
            'gpt-4-', 'gpt-4o', 'gpt-3.5-turbo', 'o1-', 'o3-'
        ]
        
        # Filter for chat models and format them
        chat_models = []
        
        # Track the latest version of each base model
        latest_models = {}
        
        # First, group models by their base name and find the latest version
        for model in models.data:
            model_id = model.id
            
            # Check if this is a chat model and doesn't contain any excluded terms
            is_chat_model = any(model_id.startswith(prefix) for prefix in chat_model_prefixes)
            is_excluded = any(excluded in model_id.lower() for excluded in excluded_models)
            
            if is_chat_model and not is_excluded:
                # Extract the base model name (without date/version)
                if '-20' in model_id:  # Has a date like -2023-xx-xx
                    base_name = model_id.split('-20')[0]
                else:
                    # For models without dates, use the full name as base
                    base_name = model_id
                
                # Special handling for o1-preview and similar models
                if base_name == 'o1-preview' or base_name == 'o3-preview':
                    base_name = base_name  # Keep as is
                
                # For mini models, keep the mini suffix
                if '-mini' in base_name:
                    base_name = base_name
                
                # Store this as the latest version if it's newer or first seen
                if base_name not in latest_models or model_id > latest_models[base_name]:
                    latest_models[base_name] = model_id
        
        # Now process our preferred models in order
        preferred_models = [
            'o1-mini',      # Default reasoning model
            'o1-preview',   # Advanced reasoning model
            'o1',           # Full reasoning model
            'o3-mini',      # Compact reasoning model
            'o3-preview',   # Preview reasoning model
            'o3',           # Full reasoning model
            'gpt-4o',       # Advanced GPT model
            'gpt-4o-mini',  # Compact GPT-4 model
            'gpt-4-turbo',  # High-performance GPT model
            'gpt-4',        # Standard GPT-4 model
            'gpt-3.5-turbo' # Fast GPT model
        ]
        
        # Add models in our preferred order, using the latest version of each
        seen_model_ids = set()
        for preferred_base in preferred_models:
            matching_base = next((base for base in latest_models.keys() 
                                if base == preferred_base or base.startswith(preferred_base)), None)
            
            if matching_base and latest_models[matching_base] not in seen_model_ids:
                model_id = latest_models[matching_base]
                
                # Use simple descriptions based on model family
                if "o1-mini" in model_id:
                    description = "Efficient reasoning model for most tasks"
                elif "o1-preview" in model_id:
                    description = "Advanced reasoning model with step-by-step thinking"
                elif "o1" in model_id:
                    description = "Full reasoning model for complex tasks"
                elif "o3-mini" in model_id:
                    description = "Compact reasoning model with strong capabilities"
                elif "o3-preview" in model_id:
                    description = "Advanced reasoning model with enhanced capabilities"
                elif "o3" in model_id:
                    description = "Powerful reasoning model for complex tasks"
                elif "gpt-4.5" in model_id:
                    description = "Latest and most advanced GPT model"
                elif "gpt-4o" in model_id and "mini" in model_id:
                    description = "Lighter version of GPT-4 Optimized"
                elif "gpt-4o" in model_id:
                    description = "Optimized version of GPT-4"
                elif "gpt-4-turbo" in model_id:
                    description = "Older high intelligence GPT-4 Model"
                elif "gpt-3.5" in model_id:
                    description = "Fast and cost-effective for simpler tasks"
                else:
                    description = "OpenAI language model"
                
                model_info = {
                    "id": model_id,
                    "name": model_id,  # Use the exact model ID
                    "provider": "OpenAI",
                    "recommended": "o1-mini" in model_id,  # Set o1-mini as recommended
                    "category": get_model_category(model_id),
                    "description": description
                }
                chat_models.append(model_info)
                seen_model_ids.add(model_id)
        
        # Add any remaining models from latest_models that weren't in our preferred list
        for base_name, model_id in latest_models.items():
            if model_id not in seen_model_ids:
                # Simple description based on model family
                if "gpt-4" in model_id:
                    description = "GPT-4 model variant"
                elif "gpt-3.5" in model_id:
                    description = "GPT-3.5 model variant"
                else:
                    description = "OpenAI language model"
                
                model_info = {
                    "id": model_id,
                    "name": model_id,  # Use the exact model ID
                    "provider": "OpenAI",
                    "recommended": False,
                    "category": get_model_category(model_id),
                    "description": description
                }
                chat_models.append(model_info)
                seen_model_ids.add(model_id)
        
        # If no chat models found, return fallback
        if not chat_models:
            return get_fallback_models()
            
        return sorted(
            chat_models,
            key=lambda x: (
                not x["recommended"],  # Recommended models first
                x["category"] != "Reasoning",  # Reasoning models first
                x["category"] != "Advanced",  # Then Advanced models
                x["name"]  # Alphabetical within same category
            )
        )
    except Exception as e:
        print(f"Error fetching OpenAI models: {e}")
        return get_fallback_models()



def get_model_category(model_id):
    """Categorizes models into different groups for UI display"""
    if model_id.startswith('o1') or model_id.startswith('o3'):
        return "Reasoning"  
    elif any(model_id.startswith(prefix) for prefix in ['gpt-4-', 'gpt-4o']):
        return "Advanced"
    elif model_id.startswith('gpt-3.5'):
        return "Standard"
    else:
        return "Other"


