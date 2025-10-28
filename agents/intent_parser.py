"""
Intent Parser - Refactored for extensibility and maintainability.

This module has been refactored to use a clean, modular architecture:
- Configuration-driven (intent_config.py)
- Handler-based processing (intent_handlers.py)
- Extensible without modifying core logic

The old nested if-elif structure has been replaced with:
1. Keyword-action mapping system
2. Modular handler functions
3. Centralized configuration

To add new commands:
1. Add keywords to intent_config.py (ACTION_KEYWORDS)
2. Add handler function to intent_handlers.py
3. Register handler in HANDLER_REGISTRY

No changes needed to this file!
"""

import json
from typing import List, Dict, Any, Optional

# Import the refactored parser
try:
    from .intent_parser_v2 import parse_command as parse_command_v2
    USE_V2 = True
except ImportError:
    USE_V2 = False
    print("⚠️ Could not import refactored parser, using fallback")


def parse_command(command: str) -> Optional[List[Dict[str, Any]]]:
    """
    Parse natural language commands into browser automation actions.
    
    This is the main entry point that maintains backward compatibility
    while using the new refactored architecture.
    
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
    
    # Use the refactored v2 parser if available
    if USE_V2:
        return parse_command_v2(command)
    
    # Fallback: return None if v2 is not available
    print(f"❌ Cannot parse command: {command}")
    return None


if __name__ == "__main__":
    # Test different command types
    test_commands = [
        "go to github.com",
        "navigate to google",
        "open stackoverflow.com",
        "search for Python documentation",
        "search for AI and take a screenshot",
        "fill the search box with machine learning",
        "click the submit button",
        "press Enter in the search field",
        "take a screenshot",
        "wait 3 seconds",
        "click first result"
    ]

    for test_command in test_commands:
        print(f"\nTesting: {test_command}")
        result = parse_command(test_command)
        print(f"Result: {json.dumps(result, indent=2)}")