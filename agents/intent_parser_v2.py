"""
Refactored Intent Parser - Clean, extensible, and maintainable.

This module provides a unified intent parsing system that:
1. Uses keyword-action mapping instead of nested if-elif chains
2. Delegates to specialized handlers for each action type
3. Extracts entities (websites, queries, etc.) dynamically
4. Supports easy extension via configuration files

Architecture:
    Command → Intent Detection → Entity Extraction → Handler → Action Plan
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from .intent_config import ACTION_KEYWORDS, WEBSITE_MAP
from .intent_handlers import HANDLER_REGISTRY


def parse_command(command: str) -> Optional[List[Dict[str, Any]]]:
    """
    Main entry point for parsing natural language commands into action plans.
    
    This function:
    1. Detects the primary intent (action type)
    2. Extracts relevant entities from the command
    3. Delegates to the appropriate handler
    4. Returns a structured action plan
    
    Args:
        command: Natural language command string
    
    Returns:
        List of action dictionaries, or None if command cannot be parsed
    
    Example:
        >>> parse_command("search for Python tutorials")
        [{"action": "goto", "value": "https://www.google.com"}, ...]
    """
    if not command or not command.strip():
        return None
    
    # Normalize command
    command_lower = command.lower().strip()
    
    # Detect intent and extract entities
    intent, entities = detect_intent(command_lower)
    
    if not intent:
        return None
    
    # Get the appropriate handler
    handler = HANDLER_REGISTRY.get(intent)
    
    if not handler:
        print(f"⚠️ No handler found for intent: {intent}")
        return None
    
    # Generate action plan using the handler
    try:
        actions = handler(command_lower, entities)
        return actions if actions else None
    except Exception as e:
        print(f"❌ Error in handler for '{intent}': {e}")
        return None


def detect_intent(command: str) -> Tuple[Optional[str], Dict[str, Any]]:
    """
    Detect the primary intent and extract relevant entities from the command.
    
    This function uses a priority-based approach:
    1. Check for specific intents first (flight booking, media playback)
    2. Then check for general intents (search, navigate, etc.)
    
    Args:
        command: Normalized command string (lowercase)
    
    Returns:
        Tuple of (intent_type, entities_dict)
    """
    entities = {}
    
    # Priority 1: Flight booking (most specific - check before general search)
    # Check for flight-specific keywords like "flight", "fly", "from...to" pattern
    if any(keyword in command for keyword in ACTION_KEYWORDS['book_flight']):
        return 'book_flight', entities
    
    # Also check for "from...to" pattern which indicates flight booking
    if ('from' in command and 'to' in command) and any(word in command for word in ['flight', 'fly', 'trip']):
        return 'book_flight', entities
    
    # Priority 2: Media playback (YouTube, music, etc.)
    if any(keyword in command for keyword in ACTION_KEYWORDS['play']):
        if 'youtube' in command or 'video' in command:
            entities['platform'] = 'youtube'
        return 'play', entities
    
    # Priority 3: Screenshot (can be combined with other actions)
    has_screenshot = any(keyword in command for keyword in ACTION_KEYWORDS['screenshot'])
    if has_screenshot:
        entities['screenshot'] = True
    
    # Priority 4: Search (check if it's a search command, but not flight-related)
    if any(keyword in command for keyword in ACTION_KEYWORDS['search']):
        # Extract website if specified
        website = extract_website(command)
        if website:
            entities['website'] = website
        
        # If screenshot is also mentioned, it's a search with screenshot
        if has_screenshot:
            return 'search', entities
        
        # Regular search
        return 'search', entities
    
    # Priority 5: Navigation (go to, open, visit)
    if any(keyword in command for keyword in ACTION_KEYWORDS['navigate']):
        website = extract_website(command)
        if website:
            entities['website'] = website
        return 'navigate', entities
    
    # Priority 6: Fill/Input (but not if it's part of search command)
    if any(keyword in command for keyword in ACTION_KEYWORDS['fill']) and 'with' in command:
        return 'fill', entities
    
    # Priority 7: Click
    if any(keyword in command for keyword in ACTION_KEYWORDS['click']):
        return 'click', entities
    
    # Priority 8: Press key
    if 'press' in command and 'in' in command:
        return 'press_key', entities
    
    # Priority 9: Wait
    if any(keyword in command for keyword in ACTION_KEYWORDS['wait']):
        return 'wait', entities
    
    # Priority 10: Screenshot only (if not already handled)
    if has_screenshot:
        return 'screenshot', entities
    
    # No intent detected
    return None, {}


def extract_website(command: str) -> Optional[str]:
    """
    Extract website name from command if present.
    
    Args:
        command: Command string
    
    Returns:
        Website name if found, None otherwise
    """
    for website in WEBSITE_MAP.keys():
        if website in command:
            return website
    return None


def extract_query(command: str, keywords_to_remove: List[str]) -> str:
    """
    Extract search query or text by removing command keywords.
    
    Args:
        command: Command string
        keywords_to_remove: List of keywords to remove
    
    Returns:
        Extracted query string
    """
    query = command
    for keyword in keywords_to_remove:
        query = query.replace(keyword, '')
    return query.strip()


# Backward compatibility - keep the old function name
def parse_command_legacy(command: str) -> Optional[List[Dict[str, Any]]]:
    """
    Legacy function for backward compatibility.
    Simply calls the new parse_command function.
    """
    return parse_command(command)


if __name__ == "__main__":
    """Test the refactored intent parser with various commands."""
    import json
    
    test_commands = [
        # Navigation
        "go to github.com",
        "open google",
        "visit stackoverflow",
        
        # Search
        "search for Python tutorials",
        "find machine learning courses",
        "search for AI and take a screenshot",
        
        # Flight booking
        "book a flight from Mumbai to Delhi next Monday",
        "search for flights from NYC to London tomorrow",
        "I want to fly from San Francisco to Paris on 2024-12-25",
        
        # Media
        "play Python programming tutorial",
        "watch funny cat videos on youtube",
        
        # Form interactions
        "fill the search box with machine learning",
        "click the submit button",
        "press Enter in the search field",
        
        # Utilities
        "take a screenshot",
        "wait 3 seconds",
        "click first result",
    ]
    
    print("=" * 80)
    print("TESTING REFACTORED INTENT PARSER")
    print("=" * 80)
    
    for test_command in test_commands:
        print(f"\n📝 Command: {test_command}")
        result = parse_command(test_command)
        
        if result:
            print(f"✅ Parsed successfully:")
            print(json.dumps(result, indent=2))
        else:
            print("❌ Could not parse command")
        print("-" * 80)
