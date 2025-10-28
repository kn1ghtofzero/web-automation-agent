"""
Integration tests for browser automation actions.
Tests all actions except flight booking as requested.
"""
import pytest
import asyncio
import os
import tempfile
from playwright.async_api import async_playwright
from agents.models import validate_actions


class TestBrowserAutomation:
    """Integration tests for browser automation functionality."""

    @pytest.fixture
    async def browser_context(self):
        """Create a browser context for testing."""
        async with async_playwright() as p:
            # Use a temporary directory for user data to avoid conflicts
            with tempfile.TemporaryDirectory() as temp_dir:
                context = await p.chromium.launch_persistent_context(
                    user_data_dir=temp_dir,
                    headless=True,  # Run headless for tests
                    args=['--no-sandbox', '--disable-dev-shm-usage']
                )
                yield context
                await context.close()

    @pytest.fixture
    async def page(self, browser_context):
        """Get a page from the browser context."""
        page = await browser_context.new_page()
        yield page
        await page.close()

    async def execute_test_actions(self, actions_data, page):
        """Execute actions using the browser_executor module."""
        from Automation.browser_executor import execute_actions
        # Override the input() call to avoid hanging in tests
        import Automation.browser_executor as executor_module
        original_input = executor_module.input
        executor_module.input = lambda: None  # Simulate Enter key press

        try:
            await execute_actions(actions_data)
        finally:
            executor_module.input = original_input

    @pytest.mark.asyncio
    async def test_goto_action(self, page):
        """Test navigation to a website."""
        actions = [{"action": "goto", "value": "https://httpbin.org/html"}]

        # Should not raise an exception
        await self.execute_test_actions(actions, page)

        # Verify we navigated correctly
        assert page.url.startswith("https://httpbin.org")

    @pytest.mark.asyncio
    async def test_fill_and_press_action(self, page):
        """Test filling a form field and pressing a key."""
        actions = [
            {"action": "goto", "value": "https://httpbin.org/forms/post"},
            {"action": "fill", "selector": "input[name='custname']", "value": "Test User"},
            {"action": "press", "selector": "input[name='custname']", "key": "Tab"}
        ]

        await self.execute_test_actions(actions, page)

        # Verify the field was filled
        value = await page.input_value("input[name='custname']")
        assert value == "Test User"

    @pytest.mark.asyncio
    async def test_click_action(self, page):
        """Test clicking elements."""
        actions = [
            {"action": "goto", "value": "https://httpbin.org/html"},
            {"action": "click", "selector": "a[href='/html']"}  # Click a link
        ]

        await self.execute_test_actions(actions, page)

        # Verify navigation occurred (should still be on same page or redirected)
        assert "httpbin.org" in page.url

    @pytest.mark.asyncio
    async def test_screenshot_action(self, page):
        """Test taking screenshots."""
        actions = [
            {"action": "goto", "value": "https://httpbin.org/html"},
            {"action": "screenshot", "filename": "test_screenshot"}
        ]

        await self.execute_test_actions(actions, page)

        # Verify screenshot file was created
        assert os.path.exists("screenshots/test_screenshot.png")

        # Clean up
        if os.path.exists("screenshots/test_screenshot.png"):
            os.remove("screenshots/test_screenshot.png")

    @pytest.mark.asyncio
    async def test_wait_action(self, page):
        """Test wait functionality."""
        actions = [
            {"action": "goto", "value": "https://httpbin.org/html"},
            {"action": "wait", "timeout": 500}  # Wait 500ms
        ]

        await self.execute_test_actions(actions, page)

        # Should complete without errors
        assert "httpbin.org" in page.url

    @pytest.mark.asyncio
    async def test_click_result_action(self, page):
        """Test clicking search results (Google search)."""
        actions = [
            {"action": "goto", "value": "https://www.google.com"},
            {"action": "fill", "selector": "textarea[name='q']", "value": "httpbin"},
            {"action": "press", "selector": "textarea[name='q']", "key": "Enter"},
            {"action": "wait", "timeout": 2000},  # Wait for search results
            {"action": "click_result"}  # Click first result
        ]

        await self.execute_test_actions(actions, page)

        # Should have navigated away from Google or to a result
        assert page.url != "https://www.google.com/"

    @pytest.mark.asyncio
    async def test_multiple_actions_sequence(self, page):
        """Test a complex sequence of actions."""
        actions = [
            {"action": "goto", "value": "https://httpbin.org/forms/post"},
            {"action": "fill", "selector": "input[name='custname']", "value": "Integration Test"},
            {"action": "fill", "selector": "input[name='custtel']", "value": "1234567890"},
            {"action": "fill", "selector": "input[name='custemail']", "value": "test@example.com"},
            {"action": "press", "selector": "input[name='custemail']", "key": "Enter"},
            {"action": "wait", "timeout": 1000},
            {"action": "screenshot", "filename": "integration_test"}
        ]

        await self.execute_test_actions(actions, page)

        # Verify form fields were filled
        name_value = await page.input_value("input[name='custname']")
        tel_value = await page.input_value("input[name='custtel']")
        email_value = await page.input_value("input[name='custemail']")

        assert name_value == "Integration Test"
        assert tel_value == "1234567890"
        assert email_value == "test@example.com"

        # Verify screenshot was taken
        assert os.path.exists("screenshots/integration_test.png")

        # Clean up
        if os.path.exists("screenshots/integration_test.png"):
            os.remove("screenshots/integration_test.png")

    @pytest.mark.asyncio
    async def test_youtube_navigation_and_consent(self, page):
        """Test YouTube navigation with consent handling."""
        actions = [
            {"action": "goto", "value": "https://www.youtube.com"},
            {"action": "wait", "timeout": 3000}
        ]

        await self.execute_test_actions(actions, page)

        # Should be on YouTube
        assert "youtube.com" in page.url

    @pytest.mark.asyncio
    async def test_error_handling_invalid_selector(self, page):
        """Test error handling for invalid selectors."""
        actions = [
            {"action": "goto", "value": "https://httpbin.org/html"},
            {"action": "fill", "selector": "input.invalid-selector", "value": "test"}
        ]

        # Should handle the error gracefully (not crash)
        await self.execute_test_actions(actions, page)

        # Should still be on the page
        assert "httpbin.org" in page.url

    @pytest.mark.asyncio
    async def test_all_actions_validation(self):
        """Test that all non-flight actions can be validated."""
        # Test all actions except book_flight
        all_actions = [
            {"action": "goto", "value": "https://example.com"},
            {"action": "fill", "selector": "input.test", "value": "test"},
            {"action": "click", "selector": "button.test"},
            {"action": "press", "selector": "input.test", "key": "Enter"},
            {"action": "click_result"},
            {"action": "screenshot", "filename": "test"},
            {"action": "wait", "timeout": 1000}
        ]

        # Should validate successfully
        validated = validate_actions(all_actions)
        assert len(validated) == 7

        # Check action types
        action_types = [action.action for action in validated]
        expected_types = ["goto", "fill", "click", "press", "click_result", "screenshot", "wait"]
        assert action_types == expected_types

    @pytest.mark.asyncio
    async def test_action_sequence_with_errors(self, page):
        """Test that errors in one action don't prevent others from running."""
        actions = [
            {"action": "goto", "value": "https://httpbin.org/html"},
            {"action": "fill", "selector": "input.invalid", "value": "should fail"},
            {"action": "screenshot", "filename": "error_recovery_test"}
        ]

        await self.execute_test_actions(actions, page)

        # Should still be on the page and screenshot should be taken
        assert "httpbin.org" in page.url
        assert os.path.exists("screenshots/error_recovery_test.png")

        # Clean up
        if os.path.exists("screenshots/error_recovery_test.png"):
            os.remove("screenshots/error_recovery_test.png")
