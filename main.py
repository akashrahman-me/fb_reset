import time, re
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from libs.FlowList import FlowList
from utils.clear_cookies import clear_cookies
from utils.flow_handler import flow_handler

numbers = """
243848437177
243848433312
243848434049
243848438681
243848435333
243848437345
243848431876
243848430218
243848432767
243848439834
243848438791
243848438277
243848434417
243848439094
243848436759
243848434476
243848438618
243848431469
243848431310
243848434438
243848439577
243848437218
243848434011
243848436935
243848432839
243848432690
243848435831
243848437086
243848433516
243848430806
243848432135
243848435168
243848434262
243848431995
243848433762
243848435351
243848436642
243848431079
243848432788
243848431626
243848432872
243848435688
243848431639
243848435547
243848431856
243848430960
243848432787
243848437781
243848437707
243848437006
243848430464
243848434449
"""

numbers = [num.strip() for num in numbers.split('\n') if num.strip()]


# Configuration for concurrent processing
MAX_WORKERS = 10  # Number of concurrent browser sessions

FORGOT_URL = 'https://www.facebook.com/login/identify/?ctx=recover&ars=facebook_login&from_login_screen=0'

# Threading lock to prevent race condition during driver initialization
driver_init_lock = Lock()


def process_number(number):
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

    options = uc.ChromeOptions()
    # options.add_argument(f'--proxy-server={proxy_server}')
    # options.add_argument(f'--headless=new')

    driver = None
    result = {"number": number, "status": "unknown", "message": ""}

    try:
        # Use lock to prevent race condition during driver initialization
        with driver_init_lock:
            driver = uc.Chrome(options=options)
            time.sleep(0.5)  # Small delay to ensure driver is fully initialized
            driver.set_window_size(1200, 800)

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
        future_to_number = {executor.submit(process_number, number): number for number in numbers}

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
