"""
Real-world test scenarios for browser automation.
These tests simulate actual user workflows using multiple actions.
"""
import pytest
import asyncio
import os
import tempfile
from playwright.async_api import async_playwright


class TestScenarios:
    """Test scenarios that simulate real user workflows."""

    @pytest.fixture
    async def browser_context(self):
        """Create a browser context for testing."""
        async with async_playwright() as p:
            with tempfile.TemporaryDirectory() as temp_dir:
                context = await p.chromium.launch_persistent_context(
                    user_data_dir=temp_dir,
                    headless=True,
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
        import Automation.browser_executor as executor_module
        original_input = executor_module.input
        executor_module.input = lambda: None

        try:
            await execute_actions(actions_data)
        finally:
            executor_module.input = original_input

    @pytest.mark.asyncio
    async def test_google_search_workflow(self, page):
        """Test a complete Google search workflow."""
        actions = [
            {"action": "goto", "value": "https://www.google.com"},
            {"action": "fill", "selector": "textarea[name='q']", "value": "pytest documentation"},
            {"action": "press", "selector": "textarea[name='q']", "key": "Enter"},
            {"action": "wait", "timeout": 3000},
            {"action": "screenshot", "filename": "google_search_results"},
            {"action": "click_result"}
        ]

        await self.execute_test_actions(actions, page)

        # Should have navigated to a search result
        assert "google.com" not in page.url or "search" in page.url

        # Clean up screenshot
        if os.path.exists("screenshots/google_search_results.png"):
            os.remove("screenshots/google_search_results.png")

    @pytest.mark.asyncio
    async def test_form_filling_workflow(self, page):
        """Test filling out a complex form."""
        actions = [
            {"action": "goto", "value": "https://httpbin.org/forms/post"},
            {"action": "fill", "selector": "input[name='custname']", "value": "John Doe"},
            {"action": "fill", "selector": "input[name='custtel']", "value": "+1-555-123-4567"},
            {"action": "fill", "selector": "input[name='custemail']", "value": "john.doe@example.com"},
            {"action": "fill", "selector": "textarea[name='comments']", "value": "This is a test submission from automated testing."},
            {"action": "press", "selector": "textarea[name='comments']", "key": "Tab"},
            {"action": "wait", "timeout": 1000},
            {"action": "screenshot", "filename": "filled_form"}
        ]

        await self.execute_test_actions(actions, page)

        # Verify all fields were filled
        name = await page.input_value("input[name='custname']")
        tel = await page.input_value("input[name='custtel']")
        email = await page.input_value("input[name='custemail']")
        comments = await page.input_value("textarea[name='comments']")

        assert name == "John Doe"
        assert tel == "+1-555-123-4567"
        assert email == "john.doe@example.com"
        assert comments == "This is a test submission from automated testing."

        # Clean up screenshot
        if os.path.exists("screenshots/filled_form.png"):
            os.remove("screenshots/filled_form.png")

    @pytest.mark.asyncio
    async def test_news_article_workflow(self, page):
        """Test navigating to a news site and interacting with content."""
        actions = [
            {"action": "goto", "value": "https://httpbin.org/html"},  # Using httpbin as a safe test site
            {"action": "click", "selector": "a[href='/html']"},
            {"action": "wait", "timeout": 2000},
            {"action": "screenshot", "filename": "news_article_view"}
        ]

        await self.execute_test_actions(actions, page)

        # Should still be on httpbin
        assert "httpbin.org" in page.url

        # Clean up screenshot
        if os.path.exists("screenshots/news_article_view.png"):
            os.remove("screenshots/news_article_view.png")

    @pytest.mark.asyncio
    async def test_ecommerce_browsing_workflow(self, page):
        """Test browsing an e-commerce style site."""
        actions = [
            {"action": "goto", "value": "https://httpbin.org/html"},
            {"action": "fill", "selector": "input[name='q']", "value": "laptop"},  # Search for products
            {"action": "press", "selector": "input[name='q']", "key": "Enter"},
            {"action": "wait", "timeout": 2000},
            {"action": "screenshot", "filename": "product_search"}
        ]

        await self.execute_test_actions(actions, page)

        # Should still be on httpbin
        assert "httpbin.org" in page.url

        # Clean up screenshot
        if os.path.exists("screenshots/product_search.png"):
            os.remove("screenshots/product_search.png")

    @pytest.mark.asyncio
    async def test_social_media_interaction_workflow(self, page):
        """Test social media style interactions."""
        actions = [
            {"action": "goto", "value": "https://httpbin.org/forms/post"},
            {"action": "fill", "selector": "textarea[name='comments']", "value": "Great content! Thanks for sharing."},
            {"action": "press", "selector": "textarea[name='comments']", "key": "Tab"},
            {"action": "wait", "timeout": 1000},
            {"action": "screenshot", "filename": "social_interaction"}
        ]

        await self.execute_test_actions(actions, page)

        # Verify comment was entered
        comment = await page.input_value("textarea[name='comments']")
        assert comment == "Great content! Thanks for sharing."

        # Clean up screenshot
        if os.path.exists("screenshots/social_interaction.png"):
            os.remove("screenshots/social_interaction.png")

    @pytest.mark.asyncio
    async def test_documentation_research_workflow(self, page):
        """Test researching documentation workflow."""
        actions = [
            {"action": "goto", "value": "https://httpbin.org/html"},
            {"action": "fill", "selector": "input[name='q']", "value": "API documentation"},
            {"action": "press", "selector": "input[name='q']", "key": "Enter"},
            {"action": "wait", "timeout": 2000},
            {"action": "screenshot", "filename": "api_docs_search"}
        ]

        await self.execute_test_actions(actions, page)

        # Should still be on httpbin
        assert "httpbin.org" in page.url

        # Clean up screenshot
        if os.path.exists("screenshots/api_docs_search.png"):
            os.remove("screenshots/api_docs_search.png")

    @pytest.mark.asyncio
    async def test_error_recovery_workflow(self, page):
        """Test workflow that includes error recovery."""
        actions = [
            {"action": "goto", "value": "https://httpbin.org/html"},
            {"action": "fill", "selector": "input.nonexistent", "value": "should fail"},  # This will error
            {"action": "fill", "selector": "input[name='q']", "value": "error recovery test"},  # This should still work
            {"action": "press", "selector": "input[name='q']", "key": "Enter"},
            {"action": "wait", "timeout": 1000},
            {"action": "screenshot", "filename": "error_recovery"}
        ]

        await self.execute_test_actions(actions, page)

        # Should still be on httpbin and screenshot should be taken
        assert "httpbin.org" in page.url

        # Verify the working field was filled
        search_value = await page.input_value("input[name='q']")
        assert search_value == "error recovery test"

        # Clean up screenshot
        if os.path.exists("screenshots/error_recovery.png"):
            os.remove("screenshots/error_recovery.png")

    @pytest.mark.asyncio
    async def test_performance_test_workflow(self, page):
        """Test workflow for performance considerations."""
        import time

        start_time = time.time()

        actions = [
            {"action": "goto", "value": "https://httpbin.org/html"},
            {"action": "fill", "selector": "input[name='q']", "value": "performance test"},
            {"action": "press", "selector": "input[name='q']", "key": "Enter"},
            {"action": "wait", "timeout": 2000},
            {"action": "fill", "selector": "input[name='q']", "value": "another search"},
            {"action": "press", "selector": "input[name='q']", "key": "Enter"},
            {"action": "wait", "timeout": 2000},
            {"action": "screenshot", "filename": "performance_test"}
        ]

        await self.execute_test_actions(actions, page)

        end_time = time.time()
        duration = end_time - start_time

        # Should complete within reasonable time (less than 30 seconds for this simple test)
        assert duration < 30, f"Test took too long: {duration} seconds"

        # Should still be on httpbin
        assert "httpbin.org" in page.url

        # Clean up screenshot
        if os.path.exists("screenshots/performance_test.png"):
            os.remove("screenshots/performance_test.png")
