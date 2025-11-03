import time, re
import undetected_chromedriver as uc
from selenium.common import NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

numbers = """
2250799820746
2250799824683
2250799826616
2250799821457
2250799829315
2250799828311
2250799829626
2250799824819
2250799826805
2250799822371
2250799825428
2250799820679
2250799825948
2250799825884
2250799822188
2250799824996
2250799826098
2250799829216
2250799824682
2250799827213
2250799829513
2250799826469
2250799822973
2250799821796
2250799828181
2250799824729
2250799824059
2250799828117
2250799822266
2250799828234
2250799827516
2250799824886
2250799820542
2250799823158
2250799823967
2250799826273
2250799822488
2250799820143
2250799822993
2250799823803
2250799821767
2250799829413
2250799824137
2250799829638
2250799828072
2250799821783
2250799826062
2250799823559
2250799827574
2250799829223
2250799827588
2250799825773
2250799820603
2250799824681
2250799824809
2250799820700
2250799827039
2250799820633
2250799822440
2250799826061
2250799829544
2250799824731
2250799828272
2250799824095
2250799827557
2250799829755
2250799824108
2250799821417
2250799820037
2250799823138
2250799829885
2250799828978
2250799821445
2250799826208
2250799821307
2250799823587
2250799824944
2250799820433
2250799824202
2250799821704
2250799827192
2250799825871
2250799820886
2250799826072
2250799823955
2250799824890
2250799825435
2250799828134
2250799827330
2250799826257
2250799820019
2250799829263
2250799823199
2250799826306
2250799829289
2250799829512
2250799829580
2250799826904
2250799822597
2250799821044
"""

numbers = [num.strip() for num in numbers.split('\n') if num.strip()]


import unicodedata

def normalize_text(s: str) -> str:
    # Replace smart quotes, dashes, etc.
    replacements = {
        "’": "'", "‘": "'", "‛": "'", "‚": "'",
        "“": '"', "”": '"', "„": '"', "‟": '"',
        "–": "-", "—": "-", "―": "-",
        "…": "...",
    }
    for k, v in replacements.items():
        s = s.replace(k, v)

    # Normalize and reduce to ASCII
    s = unicodedata.normalize("NFKD", s)
    s = s.encode("ascii", "ignore").decode("ascii")
    return s.strip().lower()


def flow_handler(driver, selectors, timeout=9999, interval=0.25):
    start = time.time()

    while time.time() - start < timeout:
        try:
            for selector in selectors:
                try:
                    elem = driver.find_element(By.CSS_SELECTOR, selector[0])
                    if elem.is_displayed():
                        return selector[1]
                except (NoSuchElementException, StaleElementReferenceException):
                    pass
                except Exception:
                    pass
            time.sleep(interval)
        except Exception:
            time.sleep(interval)

    return -1


class FlowList(list):
    def __init__(self, *args):
        super().__init__(*args)
        self._backup = list(self)  # keep a copy of original data

    def remove_by_id(self, target_id):
        """Remove a tuple by its ID (second element)."""
        for item in self[:]:
            if item[1] == target_id:
                self.remove(item)
                break

    def restore_by_id(self, target_id):
        """Restore a previously removed tuple by its ID."""
        for item in self._backup:
            if item[1] == target_id and item not in self:
                self.append(item)
                break

    def restore_all(self):
        """Restore all items from backup if missing."""
        for item in self._backup:
            if item not in self:
                self.append(item)


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


def main():
    proxy_server = "127.0.0.1:8080"

    options = uc.ChromeOptions()
    # options.add_argument(f'--proxy-server={proxy_server}')
    options.add_argument(f'--headless=new')

    driver = uc.Chrome(options=options)

    wait = WebDriverWait(driver, 9999)

    flows = FlowList([
        ("#identify_email", "FIND_ACCOUNT"),
        (".uiBoxRed ._9o4g.fsl.fwb.fcb", "NO_SEARCH_RESULTS"),
        ('.uiInterstitialBar a[href*="/recover/account/"]', "RECEIVE_CODE_METHOD"),
        ('.uiInterstitialBar a[href*="/login/web/"]', "DIRECT_SEND_CODE"),
        ('.login_form_container a[role="button"][href*="/recover/initiate/"]', "TRY_ANOTHER_WAY"),
        ('img[src*="/captcha/tfbimage.php?captcha_challenge_code"]', "THROW_CAPTCHA"),
        ('form[action*="/recover/code/?"]', "ENTER_SECURITY_CODE"),
        ('.uiInterstitialContent a[role="button"][href*="/login/identify/?ctx=recover"]', "IDENTIFY_YOUR_ACCOUNT"),
        ('.uiInterstitialContent a[href*="/help/"]', "ACCOUNT_DISABLED"),
    ])

    FORGOT_URL = 'https://www.facebook.com/login/identify/?ctx=recover&ars=facebook_login&from_login_screen=0'

    driver.get(FORGOT_URL)

    for number in numbers:

        flows.restore_all()

        while True:
            flow = flow_handler(driver, flows)

            print(flow)

            if flow == "FIND_ACCOUNT":
                flows.remove_by_id("FIND_ACCOUNT")
                flows.restore_by_id("NO_SEARCH_RESULTS")

                input_field = wait.until(
                    EC.visibility_of_element_located((By.ID, "identify_email"))
                )
                input_field.clear()
                input_field.send_keys(number, Keys.ENTER)
                time.sleep(4)

                continue

            if flow == "NO_SEARCH_RESULTS":
                flows.remove_by_id("NO_SEARCH_RESULTS")
                flows.restore_by_id("FIND_ACCOUNT")
                print(f"No search result for the number {number}")
                break

            if flow == "DIRECT_SEND_CODE":
                flows.remove_by_id("DIRECT_SEND_CODE")
                continue_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[type="submit"]')))
                continue_btn.click()

            if flow == "TRY_ANOTHER_WAY":
                flows.remove_by_id("TRY_ANOTHER_WAY")
                try_another_way = wait.until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, 'a[role="button"][href*="/recover/initiate/"]'))
                )
                try_another_way.click()
                continue

            if flow == "RECEIVE_CODE_METHOD":
                flows.remove_by_id("RECEIVE_CODE_METHOD")

                is_available_num = False
                sms_inputs = driver.find_elements(By.CSS_SELECTOR, "input[value^='send_sms:']")

                for inp in sms_inputs:
                    next_el = inp.find_element(By.XPATH, "following-sibling::*[1]")
                    num = next_el.find_element(By.CSS_SELECTOR, 'div._9o1y div[dir="ltr"], div._9o1y div[dir="rtl"]')
                    num = num.text.strip()
                    # if re.fullmatch(r"\+\d{6,}", num):
                    if number in num:
                        is_available_num = True
                        next_el.click()
                        break

                if not is_available_num:
                    print(f"No SMS option for number {number}")
                    driver.get(FORGOT_URL)
                    break

                button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '[name="reset_action"][type="submit"]')) )
                button.click()

            if flow == "IDENTIFY_YOUR_ACCOUNT":
                button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'a[role="button"][href*="/login/identify/?ctx=recover"]')))
                button.click()

            if flow == "ACCOUNT_DISABLED":
                flows.remove_by_id("ACCOUNT_DISABLED")
                print(f"Account disabled for number {number}")
                clear_cookies(driver)
                driver.get(FORGOT_URL)
                break

            if flow == "THROW_CAPTCHA":
                flows.remove_by_id("THROW_CAPTCHA")
                print("Hit CAPTCHA, skipping...")
                clear_cookies(driver)
                driver.get(FORGOT_URL)
                break

            if flow == "ENTER_SECURITY_CODE":
                flows.remove_by_id("ENTER_SECURITY_CODE")
                print("Success for number:", number)
                clear_cookies(driver)
                driver.get(FORGOT_URL)
                break


    input("Press enter to continue...")

    driver.quit()


if __name__ == '__main__':
    main()
