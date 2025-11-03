import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from libs.FlowList import FlowList
from utils.flow_handler import flow_handler
from utils.fingerprint_randomizer import (
    get_chrome_options_with_randomization,
    apply_cdp_anti_fingerprint,
    get_random_window_size
)

numbers = """
2250710945738
2250710942264
2250710941832
2250710948951
2250710942209
2250710947020
2250710949805
2250710949430
2250710943531
2250710946494
2250710940685
2250710944943
2250710945515
2250710943429
2250710946147
2250710941629
2250710946737
2250710941343
2250710948418
2250710941261
2250710943361
2250710947891
2250710949254
2250710947190
2250710947056
2250710949618
2250710947121
2250710941899
2250710943649
2250710945621
2250710941712
2250710949387
2250710943245
2250710945257
2250710940910
2250710948543
2250710946224
2250710942485
2250710945823
2250710949986
2250710942317
2250710944052
2250710943890
2250710942438
2250710949634
2250710946186
2250710940559
2250710947949
2250710944998
2250710941917
2250710944830
2250710941148
2250710943003
2250710940460
2250710941209
2250710949332
2250710940840
2250710943641
2250710946562
2250710948790
2250710949395
2250710941888
2250710941609
2250710940507
2250710947285
2250710943287
2250710946058
2250710945133
2250710945615
2250710947050
2250710949292
2250710942702
2250710944286
2250710945957
2250710941534
2250710944280
2250710942451
2250710949411
2250710941833
2250710942973
2250710940400
2250710942138
2250710948071
2250710945894
2250710948288
2250710949145
2250710941989
2250710943126
2250710942999
2250710941345
2250710948554
2250710947801
2250710944506
2250710942771
2250710945629
2250710948194
2250710946212
2250710944390
2250710948916
2250710941453
"""

numbers = [num.strip() for num in numbers.split('\n') if num.strip()]


# Configuration for concurrent processing
MAX_WORKERS = 10  # Number of concurrent browser sessions

FORGOT_URL = 'https://www.facebook.com/login/identify/?ctx=recover&ars=facebook_login&from_login_screen=0'

# Threading lock to prevent race condition during driver initialization
driver_init_lock = Lock()


def agent(number):
    """Process a single phone number in a separate browser session"""

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

    proxy_server = "127.0.0.1:8080"

    driver = None
    result = {"number": number, "status": "unknown", "message": ""}

    try:
        # Use lock to prevent race condition during driver initialization
        with driver_init_lock:
            # Get randomized Chrome options
            options = uc.ChromeOptions()

            # Apply all anti-fingerprinting Chrome arguments
            for option in get_chrome_options_with_randomization():
                options.add_argument(option)

            # Uncomment to use proxy
            # options.add_argument(f'--proxy-server={proxy_server}')
            # options.add_argument(f'--headless=new')

            # Additional preferences to prevent fingerprinting
            prefs = {
                "credentials_enable_service": False,
                "profile.password_manager_enabled": False,
                "profile.default_content_setting_values.notifications": 2,
                "profile.default_content_setting_values.media_stream": 2,
                "profile.default_content_setting_values.geolocation": 2,
            }
            options.add_experimental_option("prefs", prefs)


            driver = uc.Chrome(options=options)

        # Apply CDP-based anti-fingerprinting (must be outside lock for performance)
        user_agent = apply_cdp_anti_fingerprint(driver)
        print(f"[{number}] Using UA: {user_agent[:50]}...")

        # Set randomized window size
        width, height = get_random_window_size()
        driver.set_window_size(width, height)

        wait = WebDriverWait(driver, 9999)
        driver.get(FORGOT_URL)

        while True:
            flow = flow_handler(driver, flows)

            print(f"[{number}] {flow}")

            if flow == "FIND_ACCOUNT":
                flows.remove_by_id("FIND_ACCOUNT")
                input = wait.until(EC.element_to_be_clickable((By.ID, "identify_email")))
                input.clear()
                while input.get_attribute("value") == "":
                    input.send_keys(number, Keys.ENTER)
                    time.sleep(1)

                continue

            if flow == "NO_SEARCH_RESULTS":
                flows.remove_by_id("NO_SEARCH_RESULTS")
                print(f"[{number}] No search result for the number {number}")
                result["status"] = "not_found"
                result["message"] = "No search results"
                break

            if flow == "DIRECT_SEND_CODE":
                flows.remove_by_id("DIRECT_SEND_CODE")
                continue_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[type="submit"]')))
                continue_btn.click()
                continue

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
                    if number in num:
                        is_available_num = True
                        next_el.click()
                        break

                if not is_available_num:
                    print(f"[{number}] No SMS option for number {number}")
                    result["status"] = "no_sms"
                    result["message"] = "No SMS option available"
                    driver.get(FORGOT_URL)
                    break

                button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '[name="reset_action"][type="submit"]')) )
                button.click()

            if flow == "IDENTIFY_YOUR_ACCOUNT":
                button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'a[role="button"][href*="/login/identify/?ctx=recover"]')))
                button.click()

            if flow == "ACCOUNT_DISABLED":
                flows.remove_by_id("ACCOUNT_DISABLED")
                print(f"[{number}] Account disabled for number {number}")
                result["status"] = "disabled"
                result["message"] = "Account disabled"
                break

            if flow == "THROW_CAPTCHA":
                flows.remove_by_id("THROW_CAPTCHA")
                print(f"[{number}] Hit CAPTCHA, skipping...")
                result["status"] = "captcha"
                result["message"] = "Hit CAPTCHA"
                break

            if flow == "ENTER_SECURITY_CODE":
                flows.remove_by_id("ENTER_SECURITY_CODE")
                print(f"[{number}] Success for number: {number}")
                result["status"] = "success"
                result["message"] = "Security code page reached"
                time.sleep(10)
                break

    except Exception as e:
        print(f"[{number}] Error processing number {number}: {str(e)}")
        result["status"] = "error"
        result["message"] = str(e)
    finally:
        if driver:
            try:
                driver.quit()
            except Exception as e:
                # Suppress quit errors
                pass

    return result


def main():
    print(f"Starting concurrent processing with {MAX_WORKERS} workers...")
    print(f"Processing {len(numbers)} numbers")
    print("-" * 50)

    # Use ThreadPoolExecutor to process numbers concurrently
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Submit all tasks
        future_to_number = {executor.submit(agent, number): number for number in numbers}

        # Process results as they complete
        results = []
        for future in as_completed(future_to_number):
            number = future_to_number[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as exc:
                print(f"[{number}] Generated an exception: {exc}")
                results.append({"number": number, "status": "exception", "message": str(exc)})

    # Print summary
    print("-" * 50)
    print("Processing completed! Summary:")
    print("-" * 50)
    for result in results:
        print(f"Number: {result['number']} | Status: {result['status']} | Message: {result['message']}")


if __name__ == '__main__':
    main()
