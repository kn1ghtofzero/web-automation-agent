# Resilient UI Automation Strategies

This document outlines the robust strategies implemented in this project for handling dynamic web components without relying on fragile tactics like `force=True` or arbitrary delays.

## Overview

Modern web applications use dynamic components that can be challenging to automate:
- **Hidden autocomplete suggestions** in dropdown menus
- **Custom date pickers** that don't respond to standard input methods
- **Overlays and modals** that intercept clicks
- **Dynamic content** that loads asynchronously

## Implemented Strategies

### 1. Handling Hidden Autocomplete Suggestions

**Problem**: Autocomplete dropdowns are often hidden in the DOM until triggered, making them hard to locate.

**Solution**: Multi-strategy approach implemented in `make_my_trip.py`:

```python
# Strategy 1: Use ARIA relationships (most robust)
controls_id = await input_field.get_attribute('aria-controls')
if controls_id:
    suggestions = page.locator(f"#{controls_id}")

# Strategy 2: Contextual locator - find visible listbox with options
suggestions = page.locator('[role="listbox"]').filter(
    has=page.locator('[role="option"]')
).first

# Strategy 3: Wait for network idle instead of arbitrary delays
await page.wait_for_load_state('networkidle', timeout=5000)
await page.wait_for_timeout(500)  # Small buffer for UI updates
```

**Key Points**:
- Use semantic selectors (`role="listbox"`, `role="option"`)
- Wait for network activity to settle after typing
- Leverage ARIA attributes for relationships
- Filter for visible elements only

### 2. Handling Custom Date Pickers

**Problem**: Custom date pickers ignore typed input and require clicking specific calendar cells.

**Solution**: Multi-format date selection in `make_my_trip.py`:

```python
# Try multiple date formats for ARIA labels
calendar_selectors = [
    f'[aria-label*="{formatted_full}"]',  # "January 15, 2024"
    f'[aria-label*="{formatted_short}"]', # "Jan 15, 2024"
    f'td[role="gridcell"]:has-text("{day}")',
    f'button:has-text("{day}")',
    f'[data-value="{date_str}"]',
]

# Navigate to correct month if needed
while not correct_month_displayed:
    next_button = page.locator('[aria-label*="Next month"]').first
    await next_button.click()
    await page.wait_for_timeout(500)
```

**Key Points**:
- Try multiple selector strategies
- Use semantic attributes (ARIA labels, roles)
- Navigate calendar programmatically if direct selection fails
- Verify calendar state before clicking dates

### 3. Handling Click Interception by Overlays

**Problem**: Overlays, modals, or loading indicators can intercept clicks, causing "element is not clickable" errors.

**Solution**: Actionability checks and overlay detection in `make_my_trip.py`:

```python
# 1. Ensure element is actionable
await expect(button).to_be_visible(timeout=5000)
await expect(button).to_be_enabled(timeout=5000)
await button.scroll_into_view_if_needed()

# 2. Check if element is covered by overlay
is_covered = await button.evaluate('''
    element => {
        const rect = element.getBoundingClientRect();
        const centerX = rect.left + rect.width / 2;
        const centerY = rect.top + rect.height / 2;
        const topElement = document.elementFromPoint(centerX, centerY);
        return !element.contains(topElement) && topElement !== element;
    }
''')

# 3. Dismiss overlays if detected
if is_covered:
    await dismiss_dialogs()
    await page.wait_for_timeout(1000)

# 4. Try click with proper timeout
await button.click(timeout=10000)
```

**Key Points**:
- **Never use `force=True`** - it bypasses actionability checks
- Detect overlays using JavaScript element inspection
- Dismiss overlays programmatically
- Use Playwright's built-in actionability checks

### 4. Waiting for Dynamic Content

**Problem**: Content loads asynchronously, and arbitrary `wait_for_timeout()` is unreliable.

**Solution**: Smart waiting strategies in `browser_executor.py`:

```python
# 1. Wait for network to be idle
await page.wait_for_load_state("networkidle", timeout=20000)

# 2. Wait for specific elements to appear
await page.wait_for_selector(selector, state="visible", timeout=20000)

# 3. Wait for loading indicators to disappear
loading = page.locator('[role="progressbar"]')
if await loading.is_visible():
    await loading.wait_for(state='hidden', timeout=30000)

# 4. Verify element stability before interaction
await element.wait_for(state="visible", timeout=5000)
await page.wait_for_timeout(500)  # Small buffer for animations
```

**Key Points**:
- Use `networkidle` for AJAX-heavy pages
- Wait for specific conditions, not arbitrary times
- Wait for loading indicators to disappear
- Allow small buffers for CSS animations

### 5. YouTube Video Search (Specific Example)

**Problem**: YouTube search results are highly dynamic with ads, shorts, and varying layouts.

**Solution**: Implemented in `browser_executor.py`:

```python
# 1. Wait for network idle after search
await page.wait_for_load_state("networkidle", timeout=20000)

# 2. Try multiple container selectors
containers = [
    "#contents ytd-video-renderer",
    "ytd-search #contents ytd-video-renderer",
    "ytd-two-column-search-results-renderer #contents ytd-video-renderer",
]

# 3. Skip ads and shorts
for idx in range(count):
    item = results.nth(idx)
    
    # Check for ad markers
    ad_marker = item.locator("ytd-badge-supported-renderer:has-text('Ad')")
    if await ad_marker.is_visible(timeout=1000):
        continue
    
    # Prefer non-shorts videos
    link = item.locator("a#video-title[href*='watch']:not([href*='shorts'])")
    if await link.is_visible(timeout=2000):
        await link.scroll_into_view_if_needed()
        await page.wait_for_timeout(500)  # Wait for stability
        await link.click()
        break
```

**Key Points**:
- Filter out ads and shorts
- Wait for element stability before clicking
- Use multiple fallback strategies
- Verify navigation success

## Best Practices Summary

### ✅ DO:
- Use semantic selectors (ARIA roles, labels)
- Wait for network idle on AJAX-heavy pages
- Check element actionability before interaction
- Detect and dismiss overlays programmatically
- Use multiple fallback strategies
- Verify success after actions

### ❌ DON'T:
- Use `force=True` clicks (bypasses safety checks)
- Use arbitrary `wait_for_timeout()` without context
- Rely on fixed delays for dynamic content
- Use fragile CSS selectors that break easily
- Ignore actionability errors

## Testing Recommendations

1. **Test with slow network**: Ensures waits are sufficient
2. **Test with overlays**: Verify overlay detection works
3. **Test edge cases**: Empty results, errors, timeouts
4. **Monitor for flakiness**: Retry failed tests to identify race conditions

## References

- [Playwright Auto-waiting](https://playwright.dev/docs/actionability)
- [Playwright Best Practices](https://playwright.dev/docs/best-practices)
- [ARIA Authoring Practices](https://www.w3.org/WAI/ARIA/apg/)

## Implementation Files

- `Automation/browser_executor.py` - Main execution logic
- `Automation/make_my_trip.py` - Flight booking automation
- `agents/intent_handlers.py` - Command parsing and action generation
