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
959757989718
959757989985
959757983335
959757988640
959757989398
959757988587
959757988828
959757985776
959757982287
959757982988
959757989128
959757984337
959757985147
959757983825
959757982607
959757986956
959757983982
959757987395
959757986256
959757981411
959757989087
959757984295
959757984803
959757988690
959757985450
959757983060
959757986924
959757981236
959757985289
959757981626
959757985719
959757986440
959757980063
959757983606
959757988753
959757983879
959757988565
959757989751
959757987107
959757982393
959757986270
959757989093
959757987539
959757986807
959757986280
959757986712
959757989044
959757980755
959757988968
959757986252
959757985509
959757985607
959757980640
959757980131
959757988805
959757982384
959757989514
959757987061
959757980031
959757984915
959757987938
959757980336
959757983199
959757984989
959757986127
959757980170
959757988544
959757988036
959757980479
959757983401
959757983245
959757989446
959757983689
959757984500
959757982193
959757982754
959757987408
959757989500
959757986484
959757989294
959757985670
959757987705
959757982498
959757981409
959757986799
959757986583
959757987245
959757988949
959757984433
959757986038
959757987661
959757985446
959757988263
959757983636
959757985658
959757987580
959757988696
959757987470
959757988638
959757989231
"""

numbers = [num.strip() for num in numbers.split('\n') if num.strip()]

numbers = numbers[:3]

# Configuration for concurrent processing
MAX_WORKERS = 3  # Number of concurrent browser sessions

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
