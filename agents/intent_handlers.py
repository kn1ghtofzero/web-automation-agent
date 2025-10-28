"""
Intent handlers - modular functions for each action type.
Each handler is responsible for generating the appropriate action plan.
"""

import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from .intent_config import (
    WEBSITE_MAP, FIELD_SELECTOR_MAP, ELEMENT_SELECTOR_MAP,
    CITY_MAPPING, WEBSITE_CONFIGS
)


def handle_navigate(command: str, entities: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Handle navigation commands (go to, open, visit).
    
    Args:
        command: Original command string
        entities: Extracted entities (website, url, etc.)
    
    Returns:
        List of action dictionaries
    """
    # Extract URL or website name
    url_part = command
    for keyword in ['go to', 'navigate to', 'open', 'visit']:
        url_part = url_part.replace(keyword, '')
    url_part = url_part.strip()
    
    # Check if it's a known website
    if url_part.lower() in WEBSITE_MAP:
        url = WEBSITE_MAP[url_part.lower()]
    elif url_part.startswith('http://') or url_part.startswith('https://'):
        url = url_part
    else:
        # Assume it's a domain name and add https
        url = f"https://www.{url_part}"
    
    return [{"action": "goto", "value": url}]


def handle_search(command: str, entities: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Handle search commands with optional website specification.
    
    Args:
        command: Original command string
        entities: Extracted entities (query, website, screenshot flag, etc.)
    
    Returns:
        List of action dictionaries
    """
    # Determine target website (default to Google)
    website = entities.get('website', 'google')
    take_screenshot = entities.get('screenshot', False)
    
    # Extract search query
    search_term = command
    for keyword in ['search for', 'search', 'find', 'look for', 'look up', 'on google', 'google']:
        search_term = search_term.replace(keyword, '')
    
    # Remove screenshot-related text
    if take_screenshot:
        for phrase in ['and take a screenshot', 'take a screenshot', 'screenshot']:
            search_term = search_term.replace(phrase, '')
    
    search_term = search_term.strip()
    
    # Get website config
    config = WEBSITE_CONFIGS.get(website, WEBSITE_CONFIGS['google'])
    website_url = WEBSITE_MAP.get(website, WEBSITE_MAP['google'])
    
    # Build action plan
    actions = [
        {"action": "goto", "value": website_url},
        {"action": "fill", "selector": config['search_selector'], "value": search_term},
        {"action": "press", "selector": config['search_selector'], "key": "Enter"}
    ]
    
    # Add screenshot if requested
    if take_screenshot:
        actions.append({"action": "screenshot", "filename": "search_results.png"})
    
    return actions


def handle_play(command: str, entities: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Handle media playback commands (YouTube, music, etc.).
    
    Args:
        command: Original command string
        entities: Extracted entities (query, platform, etc.)
    
    Returns:
        List of action dictionaries
    """
    # Extract search term
    search_term = command
    for keyword in ['play', 'watch', 'listen to', 'search youtube for', 'find on youtube', 'on youtube']:
        search_term = search_term.replace(keyword, '')
    search_term = search_term.strip()
    
    # Default to YouTube for now
    config = WEBSITE_CONFIGS['youtube']
    
    return [
        {"action": "goto", "value": WEBSITE_MAP['youtube']},
        {"action": "fill", "selector": config['search_selector'], "value": search_term},
        {"action": "press", "selector": config['search_selector'], "key": "Enter"},
        {"action": "wait", "timeout": 3000},
        {"action": "click", "selector": config['first_video_selector']}
    ]


def handle_fill(command: str, entities: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Handle fill/input commands.
    
    Args:
        command: Original command string
        entities: Extracted entities (field, value, etc.)
    
    Returns:
        List of action dictionaries
    """
    # Extract field and value using regex
    fill_match = re.search(r"(?:fill|enter|input|type\s+in)\s+(?:the\s+)?(.+?)\s+with\s+(.+)", command)
    
    if not fill_match:
        return []
    
    field = fill_match.group(1).strip()
    value = fill_match.group(2).strip()
    
    # Get selector from map or generate default
    selector = FIELD_SELECTOR_MAP.get(field.lower(), f"input[name='{field}'], textarea[name='{field}']")
    
    return [{"action": "fill", "selector": selector, "value": value}]


def handle_click(command: str, entities: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Handle click commands.
    
    Args:
        command: Original command string
        entities: Extracted entities (element, etc.)
    
    Returns:
        List of action dictionaries
    """
    # Handle special case: click first result
    if 'first' in command:
        return [{"action": "click_result"}]
    
    # Extract element to click
    click_match = re.search(r"(?:click|press|tap)\s+(?:the\s+)?(.+)", command)
    
    if not click_match:
        return []
    
    element = click_match.group(1).strip()
    
    # Get selector from map or generate default
    selector = ELEMENT_SELECTOR_MAP.get(element.lower(), f"button, input[type='button'], a[href*='{element}']")
    
    return [{"action": "click", "selector": selector}]


def handle_press_key(command: str, entities: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Handle keyboard press commands.
    
    Args:
        command: Original command string
        entities: Extracted entities (key, field, etc.)
    
    Returns:
        List of action dictionaries
    """
    # Extract key and field
    press_match = re.search(r"press\s+(.+?)(?:\s+in|\s+on)\s+(?:the\s+)?(.+)", command)
    
    if not press_match:
        return []
    
    key = press_match.group(1).strip()
    field = press_match.group(2).strip()
    
    # Get selector from map or generate default
    selector = FIELD_SELECTOR_MAP.get(field.lower(), f"input[name='{field}'], textarea[name='{field}']")
    
    return [{"action": "press", "selector": selector, "key": key}]


def handle_wait(command: str, entities: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Handle wait/delay commands.
    
    Args:
        command: Original command string
        entities: Extracted entities (duration, unit, etc.)
    
    Returns:
        List of action dictionaries
    """
    # Extract time value and unit
    wait_match = re.search(r"(?:wait|pause|delay)\s+(?:for\s+)?(\d+)(?:\s*(ms|milliseconds|seconds|sec|s))?", command)
    
    if not wait_match:
        return []
    
    time_value = int(wait_match.group(1))
    unit = wait_match.group(2)
    
    # Convert to milliseconds
    if unit and unit.lower().startswith('s'):
        timeout = time_value * 1000
    else:
        timeout = time_value
    
    return [{"action": "wait", "timeout": timeout}]


def handle_screenshot(command: str, entities: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Handle screenshot commands.
    
    Args:
        command: Original command string
        entities: Extracted entities (filename, etc.)
    
    Returns:
        List of action dictionaries
    """
    # Extract optional filename
    filename_match = re.search(r"(?:screenshot|capture)\s+(?:of\s+)?(.+)", command)
    
    if filename_match:
        filename = filename_match.group(1).strip()
        # Remove common words
        for word in ['and', 'take', 'a', 'the']:
            filename = filename.replace(word, '')
        filename = filename.strip()
    else:
        filename = "screenshot.png"
    
    return [{"action": "screenshot", "filename": filename}]


def handle_book_flight(command: str, entities: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Handle flight booking commands with enhanced regex and city name handling.
    
    Args:
        command: Original command string
        entities: Extracted entities (from_city, to_city, date, etc.)
    
    Returns:
        List of action dictionaries
    """
    # Multiple regex patterns for flexible matching
    flight_patterns = [
        # Pattern 1: "search for flights from X to Y on/for date"
        r"(?:search|book|find)\s+(?:for\s+)?(?:a\s+)?flights?\s+from\s+(.+?)\s+to\s+(.+?)\s+(.+)",
        # Pattern 2: "search/book/find flight from X to Y on date" (with optional "a")
        r"(?:search|book|find)(?:\s+for)?(?:\s+a)?(?:\s+flights?)?(?:\s+from)\s+(.+?)\s+to\s+(.+?)(?:\s+on\s+|\s+for\s+|\s+date\s*:?\s*)(.+)",
        # Pattern 3: "I want to fly from X to Y on date"
        r"(?:i\s+want\s+to\s+fly|i\s+need\s+a\s+flight|i\s+would\s+like\s+to\s+book)(?:\s+from)?\s+(.+?)\s+to\s+(.+?)(?:\s+on\s+|\s+for\s+|\s+date\s*:?\s*)(.+)",
        # Pattern 4: "fly/flight/trip from X to Y on date"
        r"(?:fly|flights?|trip)\s+from\s+(.+?)\s+to\s+(.+?)(?:\s+on\s+|\s+for\s+|\s+date\s*:?\s*)(.+)",
    ]
    
    for pattern in flight_patterns:
        match = re.search(pattern, command, re.IGNORECASE)
        if match:
            from_city = match.group(1).strip()
            to_city = match.group(2).strip()
            date_str = match.group(3).strip()
            
            # Clean city names
            from_city = re.sub(r'\s+', ' ', from_city).strip()
            to_city = re.sub(r'\s+', ' ', to_city).strip()
            
            # Normalize city names using mapping
            from_city = CITY_MAPPING.get(from_city.lower(), from_city)
            to_city = CITY_MAPPING.get(to_city.lower(), to_city)
            
            # Parse and format date
            formatted_date = parse_date(date_str)
            
            return [{
                "action": "book_flight",
                "from": from_city,
                "to": to_city,
                "date": formatted_date
            }]
    
    return []


def parse_date(date_str: str) -> str:
    """
    Parse various date formats and return YYYY-MM-DD format.
    
    Args:
        date_str: Date string in various formats
    
    Returns:
        Formatted date string (YYYY-MM-DD)
    """
    try:
        date_str = date_str.strip().lower()
        
        # Handle relative dates
        if date_str == 'tomorrow':
            date_obj = datetime.now() + timedelta(days=1)
        elif date_str.startswith('next '):
            day_name = date_str[5:].strip()
            weekdays = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
            
            # Find the day index
            day_idx = None
            for idx, day in enumerate(weekdays):
                if day.startswith(day_name[:3]):
                    day_idx = idx
                    break
            
            if day_idx is not None:
                days_ahead = (day_idx - datetime.now().weekday() + 7) % 7
                if days_ahead == 0:
                    days_ahead = 7
                date_obj = datetime.now() + timedelta(days=days_ahead)
            else:
                date_obj = datetime.now() + timedelta(days=7)
        else:
            # Try various date formats
            date_formats = [
                '%Y-%m-%d', '%Y/%m/%d', '%m/%d/%Y', '%d-%m-%Y',
                '%B %d, %Y', '%b %d, %Y', '%d %B %Y', '%d %b %Y',
                '%d/%m/%Y', '%m-%d-%Y'
            ]
            
            date_obj = None
            for fmt in date_formats:
                try:
                    date_obj = datetime.strptime(date_str, fmt)
                    break
                except ValueError:
                    continue
            
            if date_obj is None:
                # Fallback: 7 days from now
                date_obj = datetime.now() + timedelta(days=7)
        
        return date_obj.strftime('%Y-%m-%d')
        
    except Exception as e:
        print(f"⚠️ Error parsing date '{date_str}': {e}")
        # Return 7 days from now as fallback
        return (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')


# Handler registry - maps action types to handler functions
HANDLER_REGISTRY = {
    'navigate': handle_navigate,
    'search': handle_search,
    'play': handle_play,
    'fill': handle_fill,
    'click': handle_click,
    'press_key': handle_press_key,
    'wait': handle_wait,
    'screenshot': handle_screenshot,
    'book_flight': handle_book_flight,
}
