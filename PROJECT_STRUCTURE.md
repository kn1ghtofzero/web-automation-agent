# TalkToWeb Project Structure

## Essential Files (Keep)

### Core Application
- `run_task.py` - Main entry point for running browser automation tasks
- `requirements.txt` - Python dependencies
- `.env` - Environment variables (user-specific, keep private)
- `.env.example` - Template for environment variables
- `README.md` - Project documentation

### Agents Module
- `agents/intent_parser.py` - Natural language command parser
- `agents/models.py` - Pydantic models for action validation
- `agents/__init__.py` - Module initialization

### Automation Module
- `Automation/browser_executor.py` - Browser automation execution engine
- `Automation/make_my_trip.py` - Flight booking handler (specialized)
- `Automation/__init__.py` - Module initialization

### Tests
- `tests/test_models.py` - Unit tests for action models
- `tests/test_browser_automation.py` - Integration tests for browser actions
- `tests/test_scenarios.py` - Real-world workflow tests
- `pytest.ini` - Pytest configuration

### Development
- `.venv/` - Virtual environment (auto-generated)
- `__pycache__/` - Python cache (auto-generated)
- `.pytest_cache/` - Pytest cache (auto-generated)
- `browser_profiles/` - Browser profile data (auto-generated)

## Removed Files (Cleanup)

### Temporary/Test Files
- `quick_test.py` - Temporary test script
- `test_all_functions.py` - Temporary comprehensive test
- `demonstrate.py` - Temporary demonstration script

### Backup Files
- `.env.bak` - Backup of environment file
- `make_my_trip.py.bak` - Backup of flight booking module

### Debug/Error Files
- `browser_state.json` - Browser state snapshot
- `destination_error.png` - Error screenshot
- `destination_input_not_found.png` - Error screenshot
- `flight_search_error.png` - Error screenshot
- `no_flights_found.png` - Error screenshot

### Unused Configuration
- `package.json` - Node.js package file (not needed)
- `package-lock.json` - Node.js lock file (not needed)
- `WARP.md` - Extra documentation file

### Empty Directories
- `apps/` - Empty directory
- `configs/` - Empty directory
- `data/` - Empty directory
- `notebooks/` - Empty directory
- `prompts/` - Empty directory
- `node_modules/` - Empty directory

## Current Clean Structure

```
TalkToWeb/
├── .env                          # Environment variables
├── .env.example                  # Environment template
├── README.md                     # Documentation
├── requirements.txt              # Dependencies
├── run_task.py                   # Main entry point
├── pytest.ini                    # Test configuration
│
├── agents/                       # Intent parsing & models
│   ├── __init__.py
│   ├── intent_parser.py
│   └── models.py
│
├── Automation/                   # Browser automation
│   ├── __init__.py
│   ├── browser_executor.py
│   └── make_my_trip.py
│
├── tests/                        # Test suite
│   ├── test_models.py
│   ├── test_browser_automation.py
│   └── test_scenarios.py
│
├── .venv/                        # Virtual environment
├── .pytest_cache/                # Pytest cache
└── browser_profiles/             # Browser data
```

## Total Files: 15 essential files + 3 test files = 18 core files
