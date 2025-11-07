import asyncio
import os
import re
import tempfile
from datetime import datetime
from typing import List, Dict, Any

from dotenv import load_dotenv
from playwright.async_api import async_playwright, Page, expect

from agents.models import validate_actions, Action
from .make_my_trip import FlightBookingHandler


async def execute_actions(actions_data: List[Dict[str, Any]]) -> None:
    """
    Execute a list of browser automation actions.
    
    Args:
        actions_data: List of action dictionaries to execute
        
    Raises:
        ValueError: If actions are invalid
        Exception: If execution fails
    """
    # Load environment variables first
    load_dotenv()
    
    # Validate actions using our Pydantic models
    try:
        actions = validate_actions(actions_data)
    except ValueError as e:
        print(f"❌ Invalid action plan: {str(e)}")
        return

    async with async_playwright() as p:
        print("🔄 Initializing Playwright...")
        
        # Create a temporary directory for user data if none specified
        user_data_dir = os.getenv('BROWSER_USER_DATA_DIR')
        if not user_data_dir or user_data_dir.strip() == '':
            print("⚠️ No BROWSER_USER_DATA_DIR set, using a fresh browser profile.")
            # Create a unique profile directory to avoid conflicts
            import uuid
            unique_id = str(uuid.uuid4())[:8]
            profiles_dir = os.path.join(os.path.dirname(__file__), "..", "browser_profiles")
            os.makedirs(profiles_dir, exist_ok=True)
            user_data_dir = os.path.join(profiles_dir, f"temp_profile_{unique_id}")
        
        try:
            print("🚀 Launching browser...")
            # Use persistent context with user data directory to maintain login state
            browser_context = await p.chromium.launch_persistent_context(
                user_data_dir=user_data_dir,
                headless=False,
                args=['--start-maximized'],
                channel="chrome",  # Use installed Chrome
                viewport=None  # Use maximized window size
            )
            print("✅ Browser launched successfully!")
        except Exception as e:
            print(f"❌ Error launching browser: {str(e)}")
            raise
        

        # Get the first page in the context or create a new one
        page = await browser_context.new_page()
        
        # Create flight booking handler
        flight_handler = FlightBookingHandler(page)

        try:
            for action in actions:
                try:
                    if action.action == "goto":
                        print(f"🌍 Navigating to {action.value}")
                        await page.goto(action.value, wait_until='domcontentloaded')
                        
                        # Handle YouTube consent and search results
                        if "youtube.com" in action.value:
                            try:
                                # Wait for page load
                                await page.wait_for_load_state("domcontentloaded")
                                await page.wait_for_load_state("networkidle")
                                
                                # Handle consent if present
                                try:
                                    consent = page.locator('button:has-text("Accept all")')
                                    if await consent.is_visible():
                                        await consent.click()
                                        await page.wait_for_timeout(1000)
                                except Exception:
                                    pass  # Consent dialog might not appear
                                
                                # If it's the main page, wait for search box
                                if action.value == "https://www.youtube.com":
                                    search_selectors = ['input#search', 'input[name="search_query"]']
                                    for selector in search_selectors:
                                        try:
                                            await page.wait_for_selector(selector, state='visible', timeout=3000)
                                            break
                                        except Exception:
                                            continue
                            except Exception as e:
                                print(f"Note: YouTube page handling: {e}")
                                
                    elif action.action == "fill":
                        print(f"⌨️ Filling {action.selector} with '{action.value}'")
                        locator = page.locator(action.selector)
                        await expect(locator).to_be_visible(timeout=10000)
                        await locator.fill(action.value)

                    elif action.action == "click":
                        print(f"🖱️ Clicking {action.selector}")
                        
                        # Special handling for YouTube video clicks
                        if "youtube.com" in await page.url() and ("ytd-video-renderer" in action.selector or "video-title" in action.selector):
                            try:
                                # Handle possible consent banners broadly
                                try:
                                    consent_buttons = page.locator("button:has-text('Accept all'), button:has-text('I agree'), button:has-text('Accept'), #introAgreeButton")
                                    if await consent_buttons.first.is_visible():
                                        await consent_buttons.first.click()
                                        await page.wait_for_timeout(1000)
                                except Exception:
                                    pass

                                # Wait for network to be idle to ensure results are loaded
                                print("⏳ Waiting for search results to load...")
                                await page.wait_for_load_state("networkidle", timeout=20000)
                                
                                # Results on YouTube can be dynamic; wait for results containers
                                containers = [
                                    "#contents ytd-video-renderer",
                                    "ytd-search #contents ytd-video-renderer",
                                    "ytd-two-column-search-results-renderer #contents ytd-video-renderer",
                                    "#contents ytd-rich-item-renderer",
                                ]
                                found_container = False
                                for container in containers:
                                    try:
                                        await page.wait_for_selector(container, state="visible", timeout=20000)
                                        found_container = True
                                        print(f"✅ Found results container: {container}")
                                        break
                                    except Exception:
                                        continue
                                if not found_container:
                                    print("❌ YouTube results did not load in time")
                                    raise Exception("YouTube search results not found")
                                
                                # Wait a bit more for dynamic content to settle
                                await page.wait_for_timeout(2000)
                                
                                # Iterate visible results, skip ads and shorts, click first real video
                                clicked = False
                                try:
                                    results = page.locator("ytd-video-renderer")
                                    count = await results.count()
                                    print(f"📋 Found {count} video results")
                                    
                                    for idx in range(count):
                                        item = results.nth(idx)
                                        
                                        # Wait for item to be visible
                                        try:
                                            await item.wait_for(state="visible", timeout=5000)
                                        except Exception:
                                            continue
                                        
                                        # Detect ad markers within this item
                                        ad_marker = item.locator(
                                            "ytd-badge-supported-renderer:has-text('Ad'), "
                                            "#badge:has-text('Ad'), "
                                            "[aria-label='Ad'], "
                                            "ytd-ad-slot-renderer, "
                                            "ytd-display-ad-renderer"
                                        )
                                        try:
                                            if await ad_marker.first.is_visible(timeout=1000):
                                                print(f"⏭️ Skipping ad at index {idx}")
                                                continue
                                        except Exception:
                                            pass

                                        # Prefer title link to ensure watch page
                                        link = item.locator("a#video-title[href*='watch']:not([href*='shorts'])").first
                                        try:
                                            if await link.is_visible(timeout=2000):
                                                await link.scroll_into_view_if_needed()
                                                # Wait for element to be stable before clicking
                                                await page.wait_for_timeout(500)
                                                await link.click()
                                                print(f"✅ Clicked first non-ad video at index {idx}")
                                                clicked = True
                                                break
                                        except Exception:
                                            pass

                                        # Fallback to thumbnail link
                                        thumb = item.locator("ytd-thumbnail a[href*='watch']:not([href*='shorts'])").first
                                        try:
                                            if await thumb.is_visible(timeout=2000):
                                                await thumb.scroll_into_view_if_needed()
                                                await page.wait_for_timeout(500)
                                                await thumb.click()
                                                print(f"✅ Clicked thumbnail of first non-ad video at index {idx}")
                                                clicked = True
                                                break
                                        except Exception:
                                            pass
                                            
                                except Exception as e:
                                    print(f"⚠️ Error while iterating YouTube results: {e}")
                                    
                                if not clicked:
                                    # Fallback: focus first renderer and press Enter
                                    try:
                                        candidate = page.locator("ytd-video-renderer").first
                                        await candidate.scroll_into_view_if_needed()
                                        await candidate.focus()
                                        await page.keyboard.press("Enter")
                                        print("↩️ Pressed Enter on first video renderer")
                                        clicked = True
                                    except Exception:
                                        print("❌ Could not find any clickable YouTube video element")
                                        raise Exception("Failed to click any video")
                                
                                if clicked:
                                    # Wait for navigation to watch page
                                    try:
                                        await page.wait_for_url(lambda url: "watch?v=" in url, timeout=20000)
                                        print("✅ Successfully navigated to video page")
                                    except Exception:
                                        print("⚠️ Video may have opened, but URL check timed out")
                                        
                            except Exception as e:
                                print(f"❌ Failed to click YouTube video: {str(e)}")
                                raise
                        else:
                            # Normal click handling
                            locator = page.locator(action.selector)
                            await expect(locator).to_be_visible(timeout=10000)
                            await locator.click()

                    elif action.action == "press":
                        print(f"🔑 Pressing {action.key} on {action.selector}")
                        locator = page.locator(action.selector)
                        await expect(locator).to_be_visible(timeout=10000)
                        await locator.press(action.key)

                    elif action.action == "click_result":
                        print("🔍 Clicking first search result")
                        await page.wait_for_selector("div.g a", state='visible', timeout=10000)
                        await page.click("div.g a")

                    elif action.action == "screenshot":
                        print(f"📸 Taking screenshot: {action.filename}")
                        # Ensure screenshots directory exists
                        os.makedirs("screenshots", exist_ok=True)
                        filepath = os.path.join("screenshots", action.filename)
                        await page.screenshot(path=filepath, full_page=True)
                        print(f"✅ Saved screenshot to {filepath}")

                    elif action.action == "book_flight":
                        print(f"✈️ Booking flight: {action.from_} → {action.to} on {action.date}")
                        if await flight_handler.handle_booking(action.from_, action.to, action.date):
                            print("✅ Flight search completed!")
                        else:
                            print("⚠️ Flight booking flow completed with warnings")

                    elif action.action == "wait":
                        timeout = getattr(action, 'timeout', 1000)  # Default to 1 second if not specified
                        print(f"⏳ Waiting for {timeout}ms...")
                        await page.wait_for_timeout(timeout)

                    else:
                        print(f"⚠️ Unknown action: {action.action}")

                    # Small delay for reliability
                    # await page.wait_for_timeout(1000)

                except Exception as e:
                    print(f"❌ Error executing {action.action}: {str(e)}")
                    # Continue with next action instead of failing completely
                    # continue
                    

            # Keep browser open until user presses Enter
            print("\n✅ Actions completed! Press Enter to close the browser...")
            input()  # Wait for user input before closing
            
        finally:
            try:
                await browser_context.close()
            except Exception as e:
                print(f"Note: Browser closing: {str(e)}")


if __name__ == "__main__":
    # Test plan for quick testing
    test_plan = [
        {"action": "goto", "value": "https://www.wikipedia.org"},
        {"action": "fill", "selector": "#searchInput", "value": "Playwright"},
        {"action": "press", "selector": "#searchInput", "key": "Enter"},
        {"action": "screenshot", "filename": "wikipedia_search_results.png"}
    ]
    
    asyncio.run(execute_actions(test_plan))