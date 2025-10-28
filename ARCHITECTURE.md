# 🏗️ TalkToWeb Architecture - Refactored Intent System

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER COMMAND                             │
│              "Search for flights from Mumbai to Delhi"           │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      run_task.py                                 │
│                   (Entry Point)                                  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                  agents/intent_parser.py                         │
│              (Compatibility Layer - Thin Wrapper)                │
│                                                                   │
│  def parse_command(command):                                     │
│      return parse_command_v2(command)  # Delegate to v2          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              agents/intent_parser_v2.py                          │
│                  (Core Orchestration)                            │
│                                                                   │
│  ┌────────────────────────────────────────────────────────┐     │
│  │ 1. parse_command(command)                              │     │
│  │    - Normalizes input                                  │     │
│  │    - Calls detect_intent()                             │     │
│  │    - Gets handler from registry                        │     │
│  │    - Returns action plan                               │     │
│  └──────────────────┬─────────────────────────────────────┘     │
│                     │                                             │
│  ┌──────────────────▼─────────────────────────────────────┐     │
│  │ 2. detect_intent(command)                              │     │
│  │    - Priority-based keyword matching                   │     │
│  │    - Extracts entities (website, query, etc.)          │     │
│  │    - Returns (intent_type, entities)                   │     │
│  └──────────────────┬─────────────────────────────────────┘     │
│                     │                                             │
└─────────────────────┼─────────────────────────────────────────────┘
                      │
        ┌─────────────┴─────────────┐
        │                           │
        ▼                           ▼
┌──────────────────┐       ┌──────────────────┐
│ intent_config.py │       │ intent_handlers  │
│  (Configuration) │       │    .py           │
│                  │       │  (Handlers)      │
│ • WEBSITE_MAP    │       │                  │
│ • ACTION_KEYWORDS│       │ • handle_search()│
│ • FIELD_SELECTORS│◄──────┤ • handle_navigate│
│ • ELEMENT_SELECTORS      │ • handle_flight()│
│ • CITY_MAPPING   │       │ • handle_play()  │
│ • WEBSITE_CONFIGS│       │ • handle_fill()  │
└──────────────────┘       │ • handle_click() │
                           │ • handle_wait()  │
                           │ • etc...         │
                           │                  │
                           │ HANDLER_REGISTRY │
                           └────────┬─────────┘
                                    │
                                    ▼
                           ┌─────────────────┐
                           │  Action Plan    │
                           │  (List[Dict])   │
                           └────────┬────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│              Automation/browser_executor.py                      │
│                  (Executes Actions)                              │
│                                                                   │
│  • Launches browser                                              │
│  • Executes each action in sequence                              │
│  • Handles special cases (flight booking)                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data Flow Example

### Example Command: "Search for flights from Mumbai to Delhi next Monday"

```
Step 1: User Input
├─ Command: "Search for flights from Mumbai to Delhi next Monday"
└─ Enters via: run_task.py

Step 2: Intent Detection (intent_parser_v2.py)
├─ Normalized: "search for flights from mumbai to delhi next monday"
├─ Keyword Match: "search" + "flight" → book_flight intent
├─ Entities Extracted: None (handled by handler)
└─ Intent: 'book_flight'

Step 3: Handler Selection
├─ Registry Lookup: HANDLER_REGISTRY['book_flight']
└─ Handler: handle_book_flight()

Step 4: Handler Execution (intent_handlers.py)
├─ Regex Match: "(.+?) to (.+?) (.+)"
├─ from_city: "mumbai" → CITY_MAPPING → "Mumbai"
├─ to_city: "delhi" → CITY_MAPPING → "Delhi"
├─ date: "next monday" → parse_date() → "2024-11-04"
└─ Action Plan:
    [
      {
        "action": "book_flight",
        "from": "Mumbai",
        "to": "Delhi",
        "date": "2024-11-04"
      }
    ]

Step 5: Browser Execution (browser_executor.py)
├─ Launches browser
├─ Calls FlightBookingHandler.search_flights()
├─ Navigates to Google Flights
├─ Fills departure city: "Mumbai"
├─ Fills destination city: "Delhi"
├─ Sets date: "2024-11-04"
└─ Searches for flights
```

---

## Component Responsibilities

### **1. intent_parser.py** (Compatibility Layer)
**Responsibility:** Maintain backward compatibility
- Thin wrapper around v2 parser
- Ensures existing code continues to work
- No business logic

### **2. intent_parser_v2.py** (Orchestrator)
**Responsibility:** Coordinate intent detection and handler execution
- Normalize input
- Detect intent using priority-based matching
- Extract entities
- Delegate to appropriate handler
- Return action plan

### **3. intent_config.py** (Configuration)
**Responsibility:** Centralize all configuration data
- Website URLs
- Action keywords
- Selectors (fields, elements)
- City name mappings
- Website-specific configs
- No logic, only data

### **4. intent_handlers.py** (Business Logic)
**Responsibility:** Implement action-specific logic
- One handler per action type
- Clean, focused functions
- Uses configuration from intent_config
- Returns structured action plans
- Registered in HANDLER_REGISTRY

### **5. browser_executor.py** (Execution Engine)
**Responsibility:** Execute browser automation
- Launches browser
- Executes actions from plan
- Handles special cases (flight booking)
- Error handling and logging

---

## Intent Detection Priority

The system uses priority-based detection to handle overlapping keywords:

```
Priority 1: Flight Booking
├─ Keywords: "book flight", "search flight", "fly from"
└─ Most specific, checked first

Priority 2: Media Playback
├─ Keywords: "play", "watch", "listen to"
└─ Specific to YouTube/media

Priority 3: Screenshot
├─ Keywords: "screenshot", "capture", "snap"
└─ Can be combined with other actions

Priority 4: Search
├─ Keywords: "search", "find", "look for"
└─ General search action

Priority 5: Navigation
├─ Keywords: "go to", "open", "visit"
└─ Simple navigation

Priority 6: Fill/Input
├─ Keywords: "fill", "enter", "input"
└─ Form interactions

Priority 7: Click
├─ Keywords: "click", "press", "tap"
└─ Element interactions

Priority 8: Press Key
├─ Keywords: "press" + "in"
└─ Keyboard actions

Priority 9: Wait
├─ Keywords: "wait", "pause", "delay"
└─ Timing control

Priority 10: Screenshot Only
└─ Fallback for standalone screenshot commands
```

---

## Handler Registry Pattern

```python
# Handlers are registered in a dictionary
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

# Dynamic dispatch based on intent
handler = HANDLER_REGISTRY.get(intent)
actions = handler(command, entities)
```

**Benefits:**
- Easy to add new handlers
- No need to modify core logic
- Testable in isolation
- Clean separation of concerns

---

## Configuration-Driven Design

### Adding a New Website

```python
# intent_config.py
WEBSITE_MAP = {
    'twitter': 'https://www.twitter.com',  # Just add this!
}
```

### Adding a New Action

```python
# Step 1: Add keywords (intent_config.py)
ACTION_KEYWORDS = {
    'check_weather': ['check weather', 'weather in'],
}

# Step 2: Add handler (intent_handlers.py)
def handle_check_weather(command, entities):
    # Implementation
    return actions

# Step 3: Register (intent_handlers.py)
HANDLER_REGISTRY = {
    'check_weather': handle_check_weather,
}

# Step 4: Add detection (intent_parser_v2.py)
if any(kw in command for kw in ACTION_KEYWORDS['check_weather']):
    return 'check_weather', entities
```

---

## Error Handling Flow

```
User Command
    ↓
parse_command()
    ├─ Empty command? → Return None
    ├─ No intent detected? → Return None
    ├─ No handler found? → Print warning, Return None
    └─ Handler error? → Catch exception, Print error, Return None
        ↓
browser_executor.py
    ├─ None action plan? → Print error, Exit
    ├─ Invalid actions? → Validation error, Exit
    └─ Execution error? → Catch, Log, Screenshot, Continue
```

---

## Testing Strategy

### Unit Tests (Per Component)
```python
# Test handlers individually
def test_handle_search():
    result = handle_search("search for python", {})
    assert result[0]['action'] == 'goto'
    assert 'google' in result[0]['value']

# Test intent detection
def test_detect_intent():
    intent, entities = detect_intent("search for python")
    assert intent == 'search'

# Test configuration
def test_website_map():
    assert 'google' in WEBSITE_MAP
    assert WEBSITE_MAP['google'].startswith('https://')
```

### Integration Tests
```python
# Test end-to-end
def test_parse_command_integration():
    result = parse_command("search for python")
    assert len(result) == 3  # goto, fill, press
    assert result[0]['action'] == 'goto'
```

---

## Performance Characteristics

| Operation | Complexity | Notes |
|-----------|-----------|-------|
| Intent Detection | O(n) | n = number of keywords |
| Handler Lookup | O(1) | Dictionary lookup |
| Action Generation | O(1) | Constant time per handler |
| Overall | O(n) | Linear in keyword count |

**Optimization:** Keywords are checked in priority order, so common intents are detected first.

---

## Extensibility Points

1. **New Websites** → Update `WEBSITE_MAP`
2. **New Actions** → Add handler + register
3. **New Selectors** → Update selector maps
4. **New Keywords** → Update `ACTION_KEYWORDS`
5. **Custom Logic** → Add to handler
6. **ML Integration** → Replace `detect_intent()`
7. **Plugin System** → Dynamic handler loading

---

## Design Principles Applied

1. **Single Responsibility** - Each component has one job
2. **Open/Closed** - Open for extension, closed for modification
3. **Dependency Inversion** - Depend on abstractions (registry)
4. **Interface Segregation** - Clean, focused interfaces
5. **DRY** - No code duplication
6. **KISS** - Keep it simple
7. **YAGNI** - You aren't gonna need it (no over-engineering)

---

## Comparison: Before vs After

### Code Organization
```
BEFORE:
intent_parser.py (250+ lines, everything in one file)

AFTER:
intent_parser.py (60 lines, compatibility layer)
intent_parser_v2.py (200 lines, orchestration)
intent_config.py (120 lines, configuration)
intent_handlers.py (350 lines, business logic)
```

### Adding New Command
```
BEFORE:
1. Find the right place in 250+ line function
2. Add elif block
3. Duplicate URL/selector logic
4. Test entire function
Time: 30+ minutes

AFTER:
1. Add keywords to config
2. Add handler function
3. Register handler
4. Add detection logic
Time: 5 minutes
```

---

## Future Architecture Enhancements

### Phase 1: Current (Complete ✅)
- Configuration-driven
- Handler-based
- Priority detection

### Phase 2: ML Integration (Future)
- Replace keyword matching with ML model
- Intent classification using transformers
- Entity extraction using NER

### Phase 3: Plugin System (Future)
- Dynamic handler loading
- User-defined commands
- Community plugins

### Phase 4: Context Awareness (Future)
- Remember previous commands
- Multi-turn conversations
- State management

---

## Conclusion

The refactored architecture provides:
- ✅ Clean separation of concerns
- ✅ Easy extensibility
- ✅ Excellent maintainability
- ✅ High testability
- ✅ Low complexity
- ✅ Professional code quality

**Result:** A production-ready, scalable intent parsing system! 🚀
