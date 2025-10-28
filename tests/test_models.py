"""
Tests for action validation models.
"""
import pytest
from agents.models import (
    validate_actions,
    GotoAction,
    FillAction,
    ClickAction,
    PressAction,
    ClickResultAction,
    ScreenshotAction,
    BookFlightAction,
    WaitAction
)

def test_valid_goto_action():
    action = {
        "action": "goto",
        "value": "https://www.google.com"
    }
    validated = validate_actions([action])
    assert len(validated) == 1
    assert isinstance(validated[0], GotoAction)
    assert validated[0].value == "https://www.google.com"

def test_invalid_goto_url():
    action = {
        "action": "goto",
        "value": "invalid-url"
    }
    with pytest.raises(ValueError, match="URL must start with http"):
        validate_actions([action])

def test_valid_fill_action():
    action = {
        "action": "fill",
        "selector": "input[name='q']",
        "value": "test query"
    }
    validated = validate_actions([action])
    assert len(validated) == 1
    assert isinstance(validated[0], FillAction)
    assert validated[0].selector == "input[name='q']"
    assert validated[0].value == "test query"

def test_valid_click_action():
    action = {
        "action": "click",
        "selector": "button.submit"
    }
    validated = validate_actions([action])
    assert len(validated) == 1
    assert isinstance(validated[0], ClickAction)
    assert validated[0].selector == "button.submit"

def test_valid_press_action():
    action = {
        "action": "press",
        "selector": "input.search",
        "key": "Enter"
    }
    validated = validate_actions([action])
    assert len(validated) == 1
    assert isinstance(validated[0], PressAction)
    assert validated[0].key == "Enter"

def test_valid_screenshot_action():
    action = {
        "action": "screenshot",
        "filename": "test.png"
    }
    validated = validate_actions([action])
    assert len(validated) == 1
    assert isinstance(validated[0], ScreenshotAction)
    assert validated[0].filename == "test.png"

def test_screenshot_filename_extension():
    action = {
        "action": "screenshot",
        "filename": "test"  # No extension
    }
    validated = validate_actions([action])
    assert validated[0].filename == "test.png"  # Extension added

def test_invalid_screenshot_filename():
    action = {
        "action": "screenshot",
        "filename": "test/invalid/path.png"
    }
    with pytest.raises(ValueError, match="invalid characters"):
        validate_actions([action])

def test_valid_book_flight():
    action = {
        "action": "book_flight",
        "from": "Mumbai",
        "to": "Delhi",
        "date": "2025-10-28"
    }
    validated = validate_actions([action])
    assert len(validated) == 1
    assert isinstance(validated[0], BookFlightAction)
    assert validated[0].from_ == "Mumbai"
    assert validated[0].to == "Delhi"
    assert validated[0].date == "2025-10-28"

def test_invalid_flight_date():
    action = {
        "action": "book_flight",
        "from": "Mumbai",
        "to": "Delhi",
        "date": "invalid-date"
    }
    with pytest.raises(ValueError, match="Date must be in YYYY-MM-DD format"):
        validate_actions([action])

def test_multiple_actions():
    actions = [
        {"action": "goto", "value": "https://www.google.com"},
        {"action": "fill", "selector": "input[name='q']", "value": "test"},
        {"action": "press", "selector": "input[name='q']", "key": "Enter"}
    ]
    validated = validate_actions(actions)
    assert len(validated) == 3
    assert isinstance(validated[0], GotoAction)
    assert isinstance(validated[1], FillAction)
    assert isinstance(validated[2], PressAction)

def test_unknown_action():
    action = {
        "action": "invalid_action",
        "value": "test"
    }
    with pytest.raises(ValueError, match="Unknown action type"):
        validate_actions([action])

def test_valid_click_result_action():
    action = {
        "action": "click_result"
    }
    validated = validate_actions([action])
    assert len(validated) == 1
    assert isinstance(validated[0], ClickResultAction)

def test_valid_wait_action():
    action = {
        "action": "wait",
        "timeout": 2000
    }
    validated = validate_actions([action])
    assert len(validated) == 1
    assert isinstance(validated[0], WaitAction)
    assert validated[0].timeout == 2000

def test_wait_action_default_timeout():
    action = {
        "action": "wait"
    }
    validated = validate_actions([action])
    assert validated[0].timeout == 1000  # Default timeout