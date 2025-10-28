"""
Pydantic models for validating browser automation actions.
"""
from typing import List, Literal, Optional
from datetime import date
from pydantic import BaseModel, Field, validator
import re

class BaseAction(BaseModel):
    """Base model for all actions with common fields."""
    action: str = Field(..., description="The type of action to perform")

class GotoAction(BaseAction):
    """Navigate to a URL."""
    action: Literal["goto"]
    value: str = Field(..., description="The URL to navigate to")

    @validator('value')
    def validate_url(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        return v

class FillAction(BaseAction):
    """Fill a form field."""
    action: Literal["fill"]
    selector: str = Field(..., description="CSS selector for the input field")
    value: str = Field(..., description="Text to enter in the field")

class ClickAction(BaseAction):
    """Click an element."""
    action: Literal["click"]
    selector: str = Field(..., description="CSS selector for the element to click")

class PressAction(BaseAction):
    """Press a key on an element."""
    action: Literal["press"]
    selector: str = Field(..., description="CSS selector for the target element")
    key: str = Field(..., description="Key to press (e.g., 'Enter', 'Tab')")

class ClickResultAction(BaseAction):
    """Click the first search result."""
    action: Literal["click_result"]

class ScreenshotAction(BaseAction):
    """Take a screenshot of the page."""
    action: Literal["screenshot"]
    filename: str = Field(..., description="Name of the file to save screenshot as")

    @validator('filename')
    def validate_filename(cls, v):
        if not v.endswith('.png'):
            v = f"{v}.png"
        if not re.match(r'^[\w\-. ]+$', v):
            raise ValueError('Filename contains invalid characters')
        return v

class BookFlightAction(BaseAction):
    """Search for flights on MakeMyTrip."""
    action: Literal["book_flight"]
    from_: str = Field(..., alias="from", description="Departure city")
    to: str = Field(..., description="Destination city")
    date: str = Field(..., description="Travel date (YYYY-MM-DD)")

    @validator('date')
    def validate_date(cls, v):
        try:
            # This will raise ValueError if date is not in YYYY-MM-DD format
            date.fromisoformat(v)
            return v
        except ValueError:
            raise ValueError('Date must be in YYYY-MM-DD format')

class WaitAction(BaseAction):
    """Wait for a specified amount of time."""
    action: Literal["wait"]
    timeout: int = Field(1000, description="Time to wait in milliseconds")

Action = GotoAction | FillAction | ClickAction | PressAction | ClickResultAction | ScreenshotAction | BookFlightAction | WaitAction

def validate_actions(actions_data: List[dict]) -> List[Action]:
    """
    Validate a list of action dictionaries against our models.
    
    Args:
        actions_data: List of dictionaries representing actions
        
    Returns:
        List of validated Action models
        
    Raises:
        ValueError: If any action is invalid
    """
    validated_actions = []
    
    for i, action_data in enumerate(actions_data):
        action_type = action_data.get('action')
        if not action_type:
            raise ValueError(f"Action at index {i} missing 'action' field")
            
        # Map action type to model
        action_models = {
            'goto': GotoAction,
            'fill': FillAction,
            'click': ClickAction,
            'press': PressAction,
            'click_result': ClickResultAction,
            'screenshot': ScreenshotAction,
            'book_flight': BookFlightAction,
            'wait': WaitAction
        }
        
        model = action_models.get(action_type)
        if not model:
            raise ValueError(f"Unknown action type '{action_type}' at index {i}")
            
        try:
            validated = model(**action_data)
            validated_actions.append(validated)
        except Exception as e:
            raise ValueError(f"Invalid {action_type} action at index {i}: {str(e)}")
    
    return validated_actions