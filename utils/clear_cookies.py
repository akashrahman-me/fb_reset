
def clear_cookies(driver):
    """Completely clear cookies, cache, and storage for the current session."""
    try:
        # Clear cookies via Selenium
        driver.delete_all_cookies()

        # Clear browser-level cookies and cache (CDP)
        driver.execute_cdp_cmd("Network.clearBrowserCookies", {})
        driver.execute_cdp_cmd("Network.clearBrowserCache", {})

        # Clear localStorage and sessionStorage (run after a page load)
        driver.execute_script("window.localStorage.clear(); window.sessionStorage.clear();")

        print("✅ Browser cookies, cache, and storage cleared.")
    except Exception as e:
        print(f"⚠️ Error clearing cookies: {e}")
