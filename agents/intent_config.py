"""
Configuration file for intent parsing - centralized mappings for websites, selectors, and actions.
This makes the system easily extensible without modifying core logic.
"""

# Website URL mappings - add new websites here
WEBSITE_MAP = {
    'google': 'https://www.google.com',
    'google.com': 'https://www.google.com',
    'youtube': 'https://www.youtube.com',
    'youtube.com': 'https://www.youtube.com',
    'github': 'https://www.github.com',
    'github.com': 'https://www.github.com',
    'stackoverflow': 'https://stackoverflow.com',
    'stackoverflow.com': 'https://stackoverflow.com',
    'reddit': 'https://www.reddit.com',
    'reddit.com': 'https://www.reddit.com',
    'wikipedia': 'https://www.wikipedia.org',
    'wikipedia.org': 'https://www.wikipedia.org',
    'amazon': 'https://www.amazon.in',
    'amazon.in': 'https://www.amazon.in',
    'amazon.com': 'https://www.amazon.com',
    'twitter': 'https://www.twitter.com',
    'twitter.com': 'https://www.twitter.com',
    'linkedin': 'https://www.linkedin.com',
    'linkedin.com': 'https://www.linkedin.com',
    'facebook': 'https://www.facebook.com',
    'facebook.com': 'https://www.facebook.com',
}

# Common field selectors - add new field types here
FIELD_SELECTOR_MAP = {
    'search box': "input[name='q'], textarea[name='q'], input[type='search']",
    'search field': "input[name='q'], textarea[name='q'], input[type='search']",
    'email': "input[type='email']",
    'password': "input[type='password']",
    'username': "input[name='username'], input[name='user']",
    'name': "input[name='name'], input[name='fullname']",
}

# Common element selectors - add new element types here
ELEMENT_SELECTOR_MAP = {
    'submit button': "input[type='submit'], button[type='submit'], button.submit",
    'search button': "input[type='submit'], button[type='submit'], button.search",
    'login button': "input[type='submit'], button[type='submit'], button.login",
    'first result': "div.g a",  # Google search result
    'first link': "a:first-of-type",
    'button': "button",
}

# City name variations for flight booking - add new cities here
CITY_MAPPING = {
    'nyc': 'New York',
    'new york city': 'New York',
    'sf': 'San Francisco',
    'san fran': 'San Francisco',
    'sfo': 'San Francisco',
    'la': 'Los Angeles',
    'lax': 'Los Angeles',
    'chi': 'Chicago',
    'ord': 'Chicago',
    'dc': 'Washington DC',
    'washington d.c.': 'Washington DC',
    'mumbai': 'Mumbai',
    'bombay': 'Mumbai',
    'bom': 'Mumbai',
    'delhi': 'Delhi',
    'del': 'Delhi',
    'new delhi': 'Delhi',
    'bengaluru': 'Bengaluru',
    'bangalore': 'Bengaluru',
    'blr': 'Bengaluru',
    'chennai': 'Chennai',
    'madras': 'Chennai',
    'maa': 'Chennai',
    'kolkata': 'Kolkata',
    'calcutta': 'Kolkata',
    'ccu': 'Kolkata',
    'london': 'London',
    'lon': 'London',
    'lhr': 'London',
    'paris': 'Paris',
    'cdg': 'Paris',
    'miami': 'Miami',
    'mia': 'Miami',
}

# Website-specific configurations for complex actions
WEBSITE_CONFIGS = {
    'youtube': {
        'search_selector': "input[name='search_query']",
        'first_video_selector': "ytd-video-renderer a#video-title[href*='watch']:not([href*='shorts'])",
    },
    'google': {
        'search_selector': "textarea[name='q']",
    },
    'wikipedia': {
        'search_selector': "#searchInput",
    },
    'wikipedia.org': {
        'search_selector': "#searchInput",
    },
    'amazon': {
        'search_selector': "input[name='field-keywords']",
    },
}

# Action keywords mapping - defines which keywords trigger which action types
ACTION_KEYWORDS = {
    'navigate': ['go to', 'navigate to', 'open', 'visit'],
    'search': ['search', 'find', 'look for', 'look up'],
    'fill': ['fill', 'enter', 'input', 'type in'],
    'click': ['click', 'press', 'tap'],
    'wait': ['wait', 'pause', 'delay'],
    'screenshot': ['screenshot', 'capture', 'take a picture', 'snap'],
    'book_flight': ['book flight', 'book a flight', 'search flight', 'find flight', 'fly from'],
    'play': ['play', 'watch', 'listen to'],
}
