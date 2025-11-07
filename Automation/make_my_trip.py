"""
Flight booking automation handlers using Google Flights with improved location handling.
"""
import re
import os
from datetime import datetime
from playwright.async_api import Page, TimeoutError as PlaywrightTimeout, expect
from typing import Optional
from dotenv import load_dotenv

class FlightBookingHandler:
    def __init__(self, page: Page):
        self.page = page

    async def search_flights(self, from_city: str, to_city: str, travel_date: str) -> bool:
        """
        Search for flights using Google Flights with improved location handling.
        Navigates DIRECTLY to Google Flights to avoid captcha on google.com.
        
        Args:
            from_city: Departure city
            to_city: Destination city
            travel_date: Date in YYYY-MM-DD format
            
        Returns:
            bool: True if flights were found, False otherwise
        """
        try:
            print(f"\n{'='*60}")
            print(f"✈️  FLIGHT SEARCH: {from_city} → {to_city} on {travel_date}")
            print(f"{'='*60}\n")
            
            # Navigate DIRECTLY to Google Flights
            print("🌐 Navigating to Google Flights...")
            await self.page.goto("https://www.google.com/travel/flights", wait_until='domcontentloaded', timeout=30000)
            
            # Wait for the page to be interactive
            print("⏳ Waiting for page to load completely...")
            await self.page.wait_for_load_state('networkidle')
            await self.page.wait_for_timeout(2000)
            
            # Handle any popups or consent dialogs
            print("🔍 Checking for popups/dialogs...")
            try:
                dismiss_buttons = [
                    self.page.get_by_text("Dismiss", exact=False),
                    self.page.get_by_text("Accept all", exact=False),
                    self.page.get_by_text("I agree", exact=False),
                    self.page.locator('button[aria-label*="Dismiss" i]'),
                    self.page.locator('button[jsname*="close"]')
                ]
                
                for btn in dismiss_buttons:
                    try:
                        if await btn.is_visible(timeout=2000):
                            await btn.click()
                            print("✅ Dismissed popup")
                            await self.page.wait_for_timeout(1000)
                            break
                    except Exception:
                        continue
            except Exception as e:
                print(f"ℹ️  No popups to dismiss")
            
            # Set departure city
            print(f"\n🔷 Step 1: Setting departure city")
            await self._set_departure_city(from_city)
            
            # Set destination city
            print(f"\n🔷 Step 2: Setting destination city")
            await self._set_destination_city(to_city)
            
            # Set departure date
            print(f"\n🔷 Step 3: Setting departure date")
            await self._set_date(travel_date)

            # Close the modal/dialog if it's still open
            print(f"\n🔷 Step 4: Closing search form modal")
            await self._close_search_modal()

            # Click search button
            print(f"\n🔷 Step 5: Clicking search button")
            await self._click_search_button()

            # Wait for results
            print(f"\n🔷 Step 6: Waiting for flight results")
            flights_found = await self._wait_for_results()
            
            print(f"\n{'='*60}")
            if flights_found:
                print("✅ SUCCESS: Found available flights!")
            else:
                print("⚠️  WARNING: No flights found for the selected criteria")
            print(f"{'='*60}\n")
            
            return flights_found
            
        except Exception as e:
            print(f"❌ Error searching flights: {str(e)}")
            # Take a screenshot when an error occurs
            try:
                screenshot_path = "flight_search_error.png"
                await self.page.screenshot(path=screenshot_path, full_page=True)
                print(f"📸 Screenshot saved as: {screenshot_path}")
            except Exception as screenshot_error:
                print(f"⚠️ Could not take screenshot: {str(screenshot_error)}")
            return False

    async def _close_search_modal(self) -> bool:
        """
        Close the search modal/dialog if it's open.
        
        Returns:
            bool: True if modal was closed or already closed, False otherwise
        """
        try:
            print("🔍 Looking for modal close button...")
            
            # Look for the "Done" button in the modal
            done_button_selectors = [
                self.page.get_by_text("Done", exact=False),
                self.page.locator('button[aria-label*="Done" i]'),
                self.page.locator('button:has-text("Done")'),
                self.page.locator('[role="button"]:has-text("Done")'),
            ]
            
            for done_btn in done_button_selectors:
                try:
                    if await done_btn.is_visible(timeout=2000):
                        await done_btn.click()
                        print("✅ Clicked Done button to close modal")
                        await self.page.wait_for_timeout(1000)
                        return True
                except Exception:
                    continue
            
            # If no Done button, look for dialog close buttons
            close_button_selectors = [
                self.page.locator('button[aria-label*="Close" i]'),
                self.page.locator('[role="dialog"] button:last-child'),
            ]
            
            for close_btn in close_button_selectors:
                try:
                    if await close_btn.is_visible(timeout=2000):
                        await close_btn.click()
                        print("✅ Clicked close button")
                        await self.page.wait_for_timeout(1000)
                        return True
                except Exception:
                    continue
            
            print("ℹ️  No modal to close")
            return True
            
        except Exception as e:
            print(f"⚠️ Error closing modal: {str(e)}")
            return False
    
    async def _dismiss_dialogs(self) -> None:
        """Dismiss any dialogs or popups that might be blocking interaction."""
        try:
            # Common selectors for dialogs, popups, and overlays
            dialog_selectors = [
                'button[aria-label*="Close"]',
                'button[aria-label*="Dismiss"]',
                'button:has-text("Dismiss")',
                'button:has-text("Close")',
                'button:has-text("Got it")',
                'button:has-text("I understand")',
                '.close-button',
                '.dismiss-button',
                '.close',
                '.dismiss',
                '[role="dialog"] button:last-child',
                '.modal-close',
                '.overlay-close'
            ]
            
            # Try to find and close any dialogs
            for selector in dialog_selectors:
                try:
                    dialog_button = self.page.locator(selector).first
                    if await dialog_button.count() > 0 and await dialog_button.is_visible():
                        await dialog_button.click()
                        print(f"✓ Dismissed dialog with selector: {selector}")
                        await self.page.wait_for_timeout(1000)
                except Exception as e:
                    continue
                    
            # Also try to press Escape key in case there's a modal that can be dismissed
            await self.page.keyboard.press('Escape')
            await self.page.wait_for_timeout(500)
            
        except Exception as e:
            print(f"⚠️ Error dismissing dialogs: {str(e)}")
    
    async def _set_departure_city(self, from_city: str) -> bool:
        """Set the departure city using robust locators and explicit waits."""
        try:
            print(f"🌍 Setting departure city to: {from_city}")
            
            # Try to find the "Where from?" input field using robust locators
            print("🔍 Looking for departure input field...")
            
            # Try multiple robust locator strategies with strict mode handling
            departure_input = None
            
            # Strategy 1: Use get_by_label with filter for visibility and enabled state
            try:
                # Get the first visible and enabled input
                departure_input = self.page.get_by_label("Where from?", exact=False).first
                await expect(departure_input).to_be_visible(timeout=10000)
                await expect(departure_input).to_be_enabled(timeout=10000)
                print("✅ Found departure input using get_by_label")
            except Exception as e:
                print(f"⚠️ get_by_label failed: {str(e)}")
                
                # Strategy 2: Use CSS selector with aria-label, filtered for active state
                try:
                    # Look for the active input field
                    departure_input = self.page.locator('[aria-label*="Where from?" i][role="combobox"]').first
                    # Or try without role filter
                    if not await departure_input.is_visible(timeout=1000):
                        departure_input = self.page.locator('[aria-label*="Where from?" i]').filter(has_not=self.page.locator('[aria-label*="Where to?" i]')).first
                    await expect(departure_input).to_be_visible(timeout=10000)
                    await expect(departure_input).to_be_enabled(timeout=10000)
                    print("✅ Found departure input using CSS selector")
                except Exception as e2:
                    print(f"⚠️ CSS selector failed: {str(e2)}")
                    
                    # Strategy 3: Use get_by_placeholder as last resort
                    try:
                        departure_input = self.page.get_by_placeholder("Where from?", exact=False).first
                        await expect(departure_input).to_be_visible(timeout=10000)
                        await expect(departure_input).to_be_enabled(timeout=10000)
                        print("✅ Found departure input using get_by_placeholder")
                    except Exception as e3:
                        print(f"❌ All locators failed: {str(e3)}")
                        await self.page.screenshot(path='departure_input_not_found.png')
                        raise Exception("Could not find departure city input field")
            
            # Scroll into view to ensure it's visible
            print("📜 Scrolling departure input into view...")
            await departure_input.scroll_into_view_if_needed()
            
            # Clear any existing value
            print("🧹 Clearing departure field...")
            await departure_input.click()
            await departure_input.fill('')
            
            # Type the city name
            print(f"⌨️ Typing city name: {from_city}")
            await departure_input.type(from_city, delay=100)
            
            # Wait for suggestions to appear - use contextual locator
            print("⏳ Waiting for autocomplete suggestions...")
            # Wait for network activity to settle after typing
            await self.page.wait_for_load_state('networkidle', timeout=5000)
            await self.page.wait_for_timeout(500)
            
            # Find the suggestions listbox that is contextually related to this input
            suggestions = await self._get_contextual_suggestions(departure_input)
            
            try:
                await expect(suggestions).to_be_visible(timeout=5000)
                print("✅ Suggestions appeared")
                
                # Wait for suggestion options to appear
                await expect(suggestions.locator('[role="option"]').first).to_be_visible(timeout=5000)
                
                # Try to find and select the matching suggestion
                city_found = await self._select_city_from_suggestions(from_city, suggestions)
                
                if city_found:
                    print(f"✅ Successfully selected departure city: {from_city}")
                else:
                    print(f"⚠️ Could not find exact match, selecting first option...")
                    # Select the first suggestion as fallback
                    first_option = suggestions.locator('[role="option"]').first
                    await first_option.click()
                    await self.page.wait_for_timeout(1000)
                
                # Verify the selection was successful with an assertion
                await self.page.wait_for_timeout(1000)  # Wait for UI to update
                try:
                    city_core = re.escape(from_city.split(',')[0].split('(')[0].strip())
                    await expect(departure_input).to_have_value(re.compile(city_core, re.IGNORECASE), timeout=5000)
                    print("✅ Verified departure city updated correctly")
                except Exception:
                    input_value = await departure_input.input_value()
                    print(f"⚠️ Departure value after selection: '{input_value}' (could not assert)")
                
            except Exception as e:
                print(f"⚠️ Suggestions handling failed: {str(e)}")
                # Screenshot for debugging
                await self.page.screenshot(path='no_suggestions_departure.png')
                # Try pressing Enter anyway
                await self.page.keyboard.press('Enter')
                await self.page.wait_for_timeout(1000)
            
            return True
            
        except Exception as e:
            print(f"❌ Error setting departure city: {str(e)}")
            await self.page.screenshot(path='departure_error.png', full_page=True)
            print("📸 Screenshot saved: departure_error.png")
            raise
            
    async def _set_destination_city(self, to_city: str) -> bool:
        """Set the destination city using robust locators and explicit waits."""
        try:
            print(f"🌍 Setting destination city to: {to_city}")
            
            # Try to find the "Where to?" input field using robust locators
            print("🔍 Looking for destination input field...")
            
            # Try multiple robust locator strategies with strict mode handling
            destination_input = None
            
            # Strategy 1: Use get_by_label with filter for visibility and enabled state
            try:
                # Get the first visible and enabled input
                destination_input = self.page.get_by_label("Where to?", exact=False).first
                await expect(destination_input).to_be_visible(timeout=10000)
                await expect(destination_input).to_be_enabled(timeout=10000)
                print("✅ Found destination input using get_by_label")
            except Exception as e:
                print(f"⚠️ get_by_label failed: {str(e)}")
                
                # Strategy 2: Use CSS selector with aria-label, filtered for active state
                try:
                    # Look for the active input field - filter out "Where from?" fields
                    destination_input = self.page.locator('[aria-label*="Where to?" i][role="combobox"]').first
                    # Or try with filter to exclude departure field
                    if not await destination_input.is_visible(timeout=1000):
                        destination_input = self.page.locator('[aria-label*="Where to?" i]').filter(has_not=self.page.locator('[aria-label*="Where from?" i]')).first
                    await expect(destination_input).to_be_visible(timeout=10000)
                    await expect(destination_input).to_be_enabled(timeout=10000)
                    print("✅ Found destination input using CSS selector")
                except Exception as e2:
                    print(f"⚠️ CSS selector failed: {str(e2)}")
                    
                    # Strategy 3: Use get_by_placeholder as last resort
                    try:
                        destination_input = self.page.get_by_placeholder("Where to?", exact=False).first
                        await expect(destination_input).to_be_visible(timeout=10000)
                        await expect(destination_input).to_be_enabled(timeout=10000)
                        print("✅ Found destination input using get_by_placeholder")
                    except Exception as e3:
                        print(f"❌ All locators failed: {str(e3)}")
                        await self.page.screenshot(path='destination_input_not_found.png')
                        raise Exception("Could not find destination city input field")
            
            # Scroll into view to ensure it's visible
            print("📜 Scrolling destination input into view...")
            await destination_input.scroll_into_view_if_needed()
            
            # Clear any existing value
            print("🧹 Clearing destination field...")
            await destination_input.click()
            await destination_input.fill('')
            
            # Type the city name
            print(f"⌨️ Typing city name: {to_city}")
            await destination_input.type(to_city, delay=100)
            
            # Wait for suggestions to appear - use contextual locator
            print("⏳ Waiting for autocomplete suggestions...")
            # Wait for network activity to settle after typing
            await self.page.wait_for_load_state('networkidle', timeout=5000)
            await self.page.wait_for_timeout(500)
            
            # Find the suggestions listbox that is contextually related to this input
            suggestions = await self._get_contextual_suggestions(destination_input)
            
            try:
                await expect(suggestions).to_be_visible(timeout=5000)
                print("✅ Suggestions appeared")
                
                # Wait for suggestion options to appear
                await expect(suggestions.locator('[role="option"]').first).to_be_visible(timeout=5000)
                
                # Try to find and select the matching suggestion
                city_found = await self._select_city_from_suggestions(to_city, suggestions)
                
                if city_found:
                    print(f"✅ Successfully selected destination city: {to_city}")
                else:
                    print(f"⚠️ Could not find exact match, selecting first option...")
                    # Select the first suggestion as fallback
                    first_option = suggestions.locator('[role="option"]').first
                    await first_option.click()
                    await self.page.wait_for_timeout(1000)
                
                # Verify the selection was successful with an assertion
                await self.page.wait_for_timeout(1000)  # Wait for UI to update
                try:
                    city_core = re.escape(to_city.split(',')[0].split('(')[0].strip())
                    await expect(destination_input).to_have_value(re.compile(city_core, re.IGNORECASE), timeout=5000)
                    print("✅ Verified destination city updated correctly")
                except Exception:
                    input_value = await destination_input.input_value()
                    print(f"⚠️ Destination value after selection: '{input_value}' (could not assert)")
            
            except Exception as e:
                print(f"⚠️ Suggestions handling failed: {str(e)}")
                # Screenshot for debugging
                await self.page.screenshot(path='no_suggestions_destination.png')
                # Try pressing Enter anyway
                await self.page.keyboard.press('Enter')
                await self.page.wait_for_timeout(1000)
            
            return True
            
        except Exception as e:
            print(f"❌ Error setting destination city: {str(e)}")
            await self.page.screenshot(path='destination_error.png', full_page=True)
            print("📸 Screenshot saved: destination_error.png")
            raise

    async def _get_contextual_suggestions(self, input_field) -> str:
        """
        Get a contextual locator for suggestions that are related to a specific input field.
        
        Args:
            input_field: The locator for the input field
            
        Returns:
            A locator for the suggestions listbox near this input
        """
        # Try to find the nearest listbox to this input field
        # Strategy: Look for listbox elements, but scope them to be near the input
        # The suggestions appear in a listbox that is typically a sibling or in a nearby container
        
        # 1) Use ARIA relationships if available (most robust)
        try:
            controls_id = None
            try:
                controls_id = self.page.sync_info()  # dummy to ensure page available
            except Exception:
                pass
            controls_id = None
            try:
                controls_id = await input_field.get_attribute('aria-controls')
            except Exception:
                controls_id = None
            if not controls_id:
                try:
                    controls_id = await input_field.get_attribute('aria-owns')
                except Exception:
                    controls_id = None
            if controls_id:
                candidate = self.page.locator(f"#{controls_id}")
                return candidate
        except Exception:
            pass

        # 2) Fallback: visible listbox with options
        try:
            visible_listboxes = self.page.locator('[role="listbox"]').filter(has=self.page.locator('[role="option"]'))
            return visible_listboxes.first
        except Exception:
            # Last resort: any listbox
            return self.page.locator('[role="listbox"]').first
    
    async def _select_city_from_suggestions(self, city_name: str, suggestions_container) -> bool:
        """
        Select the matching city from the autocomplete suggestions.
        
        Args:
            city_name: The city name to find
            suggestions_container: The locator for the suggestions listbox
            
        Returns:
            bool: True if a matching city was found and selected
        """
        try:
            print(f"🔍 Searching for city matching: {city_name}")
            
            # Get all suggestion options
            options = suggestions_container.locator('[role="option"]')
            count = await options.count()
            print(f"📋 Found {count} suggestions")
            
            # Normalize city name for matching
            city_lower = city_name.lower().strip()
            # Try multiple patterns to match
            patterns = [
                city_lower,  # Full match
                city_lower.split(',')[0].strip(),  # Just city name
                city_lower.split('(')[0].strip(),  # Remove airport code
                city_lower.split()[0]  # First word
            ]
            
            # Try each suggestion
            for i in range(min(count, 10)):  # Check first 10 suggestions
                try:
                    option = options.nth(i)
                    if not await option.is_visible():
                        continue
                    
                    text = await option.text_content()
                    if not text:
                        continue
                    
                    text_lower = text.strip().lower()
                    print(f"  [{i+1}] {text}")
                    
                    # Check if any pattern matches
                    for pattern in patterns:
                        if pattern and pattern in text_lower:
                            print(f"✅ Found match: {text}")
                            await option.click()
                            await self.page.wait_for_timeout(500)
                            return True
                            
                except Exception as e:
                    print(f"⚠️ Error checking option {i+1}: {str(e)}")
                    continue
            
            print("❌ No matching city found in suggestions")
            return False
            
        except Exception as e:
            print(f"❌ Error selecting city from suggestions: {str(e)}")
            return False
    
    async def _set_date(self, date_str: str) -> bool:
        """
        Set the departure date with improved reliability.
        
        Args:
            date_str: Date in YYYY-MM-DD format
            
        Returns:
            bool: True if date was set successfully
        """
        try:
            print(f"📅 Setting departure date to: {date_str}")
            
            # Parse date for different format needs
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            formatted_date = date_obj.strftime("%m/%d/%Y")  # MM/DD/YYYY format
            day = str(date_obj.day)
            month_num = str(date_obj.month)
            year = str(date_obj.year)
            month_name = date_obj.strftime("%B")
            
            # Google Flights specific selectors
            date_input_selectors = [
                '[aria-label="Departure date"]',
                '[placeholder*="Departure date"]',
                '[aria-label="Departure"]',
                'input[type="text"][aria-label*="Departure"]',
                '[role="textbox"][aria-label*="Departure"]'
            ]
            
            print("🔍 Looking for date input...")
            
            # First try: Direct input of the date
            for selector in date_input_selectors:
                try:
                    date_input = self.page.locator(selector).first
                    if await date_input.is_visible():
                        print(f"✓ Found date input with selector: {selector}")
                        
                        # Clear any overlays first
                        await self._dismiss_dialogs()
                        await self.page.wait_for_timeout(500)
                        
                        # Click to focus and clear the field
                        await date_input.click()
                        await date_input.fill("")
                        await self.page.wait_for_timeout(500)
                        
                        # Try typing the date with keyboard
                        for char in formatted_date:
                            await date_input.type(char, delay=100)
                        await self.page.wait_for_timeout(500)
                        await self.page.keyboard.press("Enter")
                        await self.page.wait_for_timeout(1000)
                        
                        # Check if the date was accepted
                        input_value = await date_input.input_value()
                        if formatted_date in input_value or date_str in input_value:
                            print(f"✓ Date set successfully via direct input: {formatted_date}")
                            return True
                            
                        # If direct input didn't work, try opening the calendar
                        await date_input.click()
                        await self.page.wait_for_timeout(1000)
                        
                        # Wait for calendar to be visible
                        calendar = self.page.locator('[role="dialog"], [role="application"]').filter(has=self.page.locator('[role="grid"]'))
                        await calendar.wait_for(timeout=5000)
                        
                        # Navigate to correct month if needed
                        current_month = self.page.locator('[aria-live="polite"], [jsname="lmcIF"]').first
                        current_text = await current_month.text_content() or ""
                        target_month = f"{month_name} {year}"
                        
                        print(f"Navigating to month: {target_month}")
                        while target_month not in current_text:
                            if date_obj > datetime.now():
                                await self.page.locator('button[aria-label*="Next month"], [jsname="VOEIyf"]').click()
                            else:
                                await self.page.locator('button[aria-label*="Previous month"], [jsname="Bg6qfe"]').click()
                            await self.page.wait_for_timeout(500)
                            current_text = await current_month.text_content() or ""
                        
                        # Try to click the date using various selectors
                        date_selectors = [
                            f'[jsname="gHtaPd"]:has-text("{day}")',  # Google Flights specific
                            f'[aria-label*="{month_num}/{day}/{year}"]',
                            f'td[role="gridcell"]:has-text("{day}")',
                            f'button:has-text("{day}")',
                            f'[data-value="{date_str}"]',
                            f'[data-date="{date_str}"]',
                            f'[jsname*="date"][aria-label*="{day}"]'
                        ]
                        
                        # Try each calendar selector
                        for cal_selector in calendar_selectors:
                            try:
                                date_cell = self.page.locator(cal_selector).first
                                if await date_cell.is_visible():
                                    await date_cell.click()
                                    print(f"✓ Selected date: {formatted_full}")
                                    await self.page.wait_for_timeout(1000)
                                    return True
                            except Exception as e:
                                continue
                                
                except Exception:
                    continue
            
            # If direct selection fails, try navigating to the month
            month_year_selectors = [
                '[aria-label*="Month"]',
                '[class*="month-picker"]',
                '[aria-label*="Select date"]',
                '[class*="calendar-header"]'
            ]
            
            for selector in month_year_selectors:
                try:
                    header = self.page.locator(selector).first
                    if await header.is_visible():
                        # Get current displayed month/year
                        current_text = await header.text_content()
                        if current_text:
                            # Navigate to correct month if needed
                            while not any(m in current_text.lower() for m in [date_obj.strftime("%B").lower(), date_obj.strftime("%b").lower()]):
                                next_button = self.page.locator('[aria-label*="Next month"]').first
                                prev_button = self.page.locator('[aria-label*="Previous month"]').first
                                
                                if date_obj.month > datetime.now().month:
                                    if await next_button.is_visible():
                                        await next_button.click()
                                else:
                                    if await prev_button.is_visible():
                                        await prev_button.click()
                                        
                                await self.page.wait_for_timeout(500)
                                current_text = await header.text_content()
                                
                            # Try to click the day again
                            day_selectors = [
                                f'td[role="gridcell"]:has-text("{day}")',
                                f'button:has-text("{day}")'
                            ]
                            
                            for day_selector in day_selectors:
                                try:
                                    day_cell = self.page.locator(day_selector).first
                                    if await day_cell.is_visible():
                                        await day_cell.click()
                                        print(f"✓ Selected date: {formatted_full} (after navigation)")
                                        return True
                                except Exception:
                                    continue
                                    
                except Exception:
                    continue
            
            # If calendar selection fails, try direct input methods
            for selector in date_selectors:
                try:
                    input_element = self.page.locator(selector).first
                    if await input_element.is_visible():
                        # Try MM/DD/YYYY format
                        formatted_date = date_obj.strftime("%m/%d/%Y")
                        await input_element.fill(formatted_date)
                        await self.page.wait_for_timeout(1000)
                        await self.page.keyboard.press('Enter')
                        await self.page.wait_for_timeout(1000)
                        
                        # If that didn't work, try YYYY-MM-DD format
                        if not await self._verify_date_selected(date_str):
                            await input_element.fill(date_str)
                            await self.page.wait_for_timeout(1000)
                            await self.page.keyboard.press('Enter')
                            await self.page.wait_for_timeout(1000)
                            
                        if await self._verify_date_selected(date_str):
                            print(f"✓ Entered date directly: {date_str}")
                            return True
                except Exception as e:
                    print(f"⚠️ Direct input failed: {str(e)}")
                    continue
            
            print("⚠️ Could not set date. The calendar interface may have changed.")
            try:
                await self.page.screenshot(path='date_selection_failed.png')
                print("📸 Screenshot saved for debugging")
            except:
                pass
            return False
            
        except Exception as e:
            print(f"❌ Error setting date: {str(e)}")
            try:
                await self.page.screenshot(path='date_error.png')
                print("📸 Error screenshot saved")
            except:
                pass
            return False

    async def _click_search_button(self) -> bool:
        """
        Click the search button with improved reliability.
        
        Returns:
            bool: True if search button was clicked successfully
        """
        try:
            print("🔍 Looking for search button...")
            
            # More comprehensive list of search button selectors
            search_selectors = [
                'button:has-text("Search")',
                'button:has-text("Find flights")',
                'button:has-text("Search flights")',
                'button[aria-label*="Search" i]',
                'button[aria-label*="Find" i]',
                'button[type="submit"]',
                'button[jsname*="search"]',
                'button[data-testid*="search"]',
                'button[class*="search"]',
                'button.VfPpkd-LgbsSe',  # Google Material Design button
                'button[jsaction*="search"]',
                'input[type="submit"]',
                '[role="button"]:has-text("Search")',
                '[role="button"]:has-text("Find")'
            ]
            
            # Try each selector
            for selector in search_selectors:
                try:
                    button = self.page.locator(selector).first
                    if await button.is_visible():
                        print(f"✓ Found search button: {selector}")
                        
                        # Clear any overlays first
                        await self._dismiss_dialogs()
                        await self.page.wait_for_timeout(500)
                        
                        # Try resilient click strategies without force=True
                        click_success = False
                        
                        # 1. Ensure button is actionable (visible, enabled, not obscured)
                        try:
                            # Wait for button to be in actionable state
                            await expect(button).to_be_visible(timeout=5000)
                            await expect(button).to_be_enabled(timeout=5000)
                            
                            # Scroll into view to ensure visibility
                            await button.scroll_into_view_if_needed()
                            await self.page.wait_for_timeout(500)
                            
                            # Check if button is covered by overlay
                            is_covered = await button.evaluate('''
                                element => {
                                    const rect = element.getBoundingClientRect();
                                    const centerX = rect.left + rect.width / 2;
                                    const centerY = rect.top + rect.height / 2;
                                    const topElement = document.elementFromPoint(centerX, centerY);
                                    return !element.contains(topElement) && topElement !== element;
                                }
                            ''')
                            
                            if is_covered:
                                print("⚠️ Button is covered by overlay, attempting to dismiss...")
                                await self._dismiss_dialogs()
                                await self.page.wait_for_timeout(1000)
                            
                            # Try regular click with timeout
                            await button.click(timeout=10000)
                            click_success = True
                            print("✓ Clicked search button (regular click)")
                            
                        except Exception as e:
                            print(f"Regular click failed: {e}")
                            
                            # 2. Try clicking via JavaScript (more reliable for dynamic pages)
                            try:
                                await button.evaluate('element => element.click()')
                                click_success = True
                                print("✓ Clicked search button (JavaScript click)")
                            except Exception as e:
                                print(f"JavaScript click failed: {e}")
                                
                                # 3. Try dispatch click event
                                try:
                                    await button.dispatch_event('click')
                                    click_success = True
                                    print("✓ Clicked search button (dispatch event)")
                                except Exception as e:
                                    print(f"Event dispatch failed: {e}")
                        
                        if click_success:
                            # Wait for navigation or loading indicator
                            try:
                                # Look for loading indicators
                                loading_selectors = [
                                    '[role="progressbar"]',
                                    '[class*="loading"]',
                                    '[class*="spinner"]',
                                    'text="Loading..."'
                                ]
                                
                                for loading_selector in loading_selectors:
                                    try:
                                        loading = self.page.locator(loading_selector).first
                                        if await loading.is_visible():
                                            print("⌛ Waiting for results to load...")
                                            await loading.wait_for(state='hidden', timeout=30000)
                                            break
                                    except Exception:
                                        continue
                                        
                                return True
                                
                            except Exception as e:
                                print(f"⚠️ Navigation check failed: {e}")
                                # Continue anyway as the click might have worked
                                return True
                        
                except Exception as e:
                    print(f"⚠️ Error with selector {selector}: {e}")
                    continue
            
            print("❌ Could not find or click search button")
            # Take a screenshot for debugging
            try:
                await self.page.screenshot(path='search_button_error.png')
                print("📸 Error screenshot saved")
            except:
                pass
            return False
            
        except Exception as e:
            print(f"❌ Error clicking search: {e}")
            try:
                await self.page.screenshot(path='search_error.png')
                print("📸 Error screenshot saved")
            except:
                pass
            return False

    async def _wait_for_results(self) -> bool:
        """
        Wait for flight results to load with better error handling and validation.
        
        Returns:
            bool: True if valid flight results are found, False otherwise
        """
        try:
            print("⌛ Waiting for results to load...")
            
            # First wait for initial loading
            await self.page.wait_for_load_state('networkidle')
            await self.page.wait_for_timeout(3000)
            
            # Check for loading indicators
            loading_selectors = [
                '[role="progressbar"]',
                '[class*="loading"]',
                '[class*="spinner"]',
                'text="Loading..."',
                '.progress-circular',
                '.loading-indicator'
            ]
            
            # Wait for loading indicators to disappear
            for selector in loading_selectors:
                try:
                    loading = self.page.locator(selector).first
                    if await loading.is_visible():
                        print(f"⌛ Found loading indicator: {selector}")
                        await loading.wait_for(state='hidden', timeout=30000)
                except Exception:
                    continue
            
            # Check for error messages that indicate no results
            error_selectors = [
                'text="No flights found"',
                'text="No matching flights"',
                'text="Try different dates"',
                'text="No options"',
                'text="No results"',
                'text="Sorry, we couldn\'t find any flights"',
                '.gws-flights-results__error-message',
                '[class*="error-message"]',
                '[class*="no-results"]',
                'text="0 flights available"',
                'text="No direct flights"',
                '[class*="empty-state"]'
            ]
            
            # Check all error messages
            for selector in error_selectors:
                try:
                    error = self.page.locator(selector).first
                    if await error.is_visible():
                        error_text = await error.text_content()
                        print(f"❌ No flights found: {error_text}")
                        # Take error screenshot
                        try:
                            await self.page.screenshot(path='no_results_error.png')
                            print("📸 Error screenshot saved")
                        except:
                            pass
                        return False
                except Exception:
                    continue
            
            # Look for flight results using multiple selectors
            result_selectors = [
                '[data-testid="flight-card"]',
                '[data-testid*="itinerary"]',
                '[class*="flight-card"]',
                '[class*="flight-result"]',
                '[jsname*="flight"]',
                'div[role="listitem"]',
                '.gws-flights-results__itinerary-card',
                '.R1xNUc',  # Google Flights result card
                '.Rk10dc',  # Another Google Flights result container
                '[class*="itinerary"]',
                '[class*="result-item"]'
            ]
            
            # Check each result selector
            for selector in result_selectors:
                try:
                    results = self.page.locator(selector)
                    count = await results.count()
                    
                    if count > 0:
                        # Verify the first result is actually visible and has content
                        first_result = results.first
                        if await first_result.is_visible():
                            # Try to get some flight details to validate it's a real result
                            result_text = await first_result.text_content()
                            if result_text and len(result_text.strip()) > 0:
                                print(f"✅ Found {count} flight results!")
                                
                                # Try to get price information for verification
                                price_selectors = [
                                    '[class*="price"]',
                                    '[aria-label*="price"]',
                                    'text=/\\$[0-9,]+/',  # Match price format
                                    'text=/[0-9,]+ USD/',
                                    'text=/USD [0-9,]+/'
                                ]
                                
                                # Look for price information to validate results
                                for price_selector in price_selectors:
                                    try:
                                        price = await first_result.locator(price_selector).first.text_content()
                                        if price:
                                            print(f"✓ Found price information: {price}")
                                            break
                                    except Exception:
                                        continue
                                
                                return True
                                
                except Exception as e:
                    print(f"⚠️ Error checking selector {selector}: {e}")
                    continue
            
            # If we get here, no valid results were found
            print("⚠️ No flight results found.")
            print("Possible reasons:")
            print("  • No flights available for the selected date")
            print("  • The route may not be serviced by any airlines")
            print("  • Website layout changes")
            print("  • Network or loading issues")
            
            # Take a screenshot for debugging
            try:
                await self.page.screenshot(path='no_flights_found.png', full_page=True)
                print("📸 Screenshot saved for debugging")
            except Exception as e:
                print(f"⚠️ Could not take screenshot: {e}")
            
            return False
            
        except Exception as e:
            print(f"❌ Error checking results: {e}")
            try:
                await self.page.screenshot(path='results_error.png')
                print("📸 Error screenshot saved")
            except:
                pass
            return False

    async def handle_booking(self, from_city: str, to_city: str, travel_date: str) -> bool:
        """
        Complete flight booking flow using Google Flights.
        
        Args:
            from_city: Departure city
            to_city: Destination city  
            travel_date: Date in YYYY-MM-DD format
            
        Returns:
            bool: True if booking flow completed successfully
        """
        try:
            print(f"🛫 Starting flight search: {from_city} → {to_city} on {travel_date}")
            
            # Search for flights (no login required for Google Flights)
            if await self.search_flights(from_city, to_city, travel_date):
                print("✅ Flight search completed successfully!")
                return True
            else:
                print("⚠️ Flight search completed with warnings")
                return False
                
        except Exception as e:
            print(f"❌ Error in booking flow: {str(e)}")
            return False
