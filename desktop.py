import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException
from libs.FlowList import FlowList
from utils.flow_handler import flow_handler

numbers = """

959750502251
959750508258
959750506007
959750504256
959750501489
959750504827
959750509033
959750509147
959750508551
959750506645
959750504637
959750502001
959750501822
959750500217
959750502648
959750502970
959750501760
959750506432
959750506724
959750502058
959750502753
959750505317
959750502917
959750502330
959750504082
959750500518
959750506749
959750501661
959750509438
959750509936
959750506874
959750503996
959750500360
959750503127
959750501956
959750508611
959750508450
959750504282
959750504766
959750507654
959750505295
959750509075
959750500596
959750504573
959750503443
959750502803
959750503997
959750507724
959750504212
959750507712
959750507732
959750509878
959750509203
959750509125
959750507877
959750508775
959750507527
959750509459
959750504707
959750501251
959750502762
959750505378
959750507127
959750506359
959750503367
959750506341
959750508647
959750500232
959750506776
959750505880
959750505691
959750508269
959750505513
959750501508
959750508128
959750507513
959750503780
959750504771
959750501178
959750506149
959750509469
959750503419
959750502356
959750506565
959750500104
959750503674
959750500449
959750502456
959750503023
959750506830
959750506631
959750500872
959750500435
959750508497
959750505502
959750504546
959750507048
959750508251
959750501294
959750500020
"""

numbers = [num.strip() for num in numbers.split('\n') if num.strip()]


# Configuration
MAX_WORKERS = 5
FORGOT_URL = 'https://www.facebook.com/login/identify/?ctx=recover&ars=facebook_login&from_login_screen=0'


def click_element(driver, element):
    """Simple click with JavaScript fallback"""
    try:
        element.click()
    except:
        driver.execute_script("arguments[0].click();", element)


def agent(number):
    """Process a single phone number"""

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
        ('[aria-label="Reload page"]', "SOMETHING_WENT_WRONG"),
    ])

    driver = None
    result = {"number": number, "status": "unknown", "message": ""}

    try:
        # Simple Chrome setup
        options = uc.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-blink-features=AutomationControlled")
        # options.add_argument("--headless=new")  # Uncomment for headless mode
        custom_user_agent = "Mozilla/5.0 (Linux; Android 8.0.0; SM-G955U Build/R16NW) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Mobile Safari/537.36"
        options.add_argument(f"--user-agent={custom_user_agent}")

        driver = uc.Chrome(options=options)
        wait = WebDriverWait(driver, 30)
        driver.get(FORGOT_URL)

        while True:
            flow = flow_handler(driver, flows)
            print(f"[{number}] {flow}")

            if flow == "FIND_ACCOUNT":
                flows.remove_by_id("FIND_ACCOUNT")

                # Fill in the phone number
                input_elem = wait.until(EC.element_to_be_clickable((By.ID, "identify_email")))
                input_elem.clear()
                input_elem.send_keys(number)
                time.sleep(0.5)

                # Submit the form
                input_elem.send_keys(Keys.ENTER)
                continue

            if flow == "NO_SEARCH_RESULTS":
                flows.remove_by_id("NO_SEARCH_RESULTS")
                print(f"[{number}] No search result")
                result["status"] = "not_found"
                result["message"] = "No search results"
                break

            if flow == "DIRECT_SEND_CODE":
                flows.remove_by_id("DIRECT_SEND_CODE")
                continue_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[type="submit"]')))
                click_element(driver, continue_btn)
                continue

            if flow == "TRY_ANOTHER_WAY":
                flows.remove_by_id("TRY_ANOTHER_WAY")
                try_another_way = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'a[role="button"][href*="/recover/initiate/"]')))
                click_element(driver, try_another_way)
                continue

            if flow == "RECEIVE_CODE_METHOD":
                flows.remove_by_id("RECEIVE_CODE_METHOD")

                # Find SMS option matching our number
                time.sleep(1)
                sms_inputs = driver.find_elements(By.CSS_SELECTOR, "input[value^='send_sms:']")
                print(f"[{number}] Found {len(sms_inputs)} SMS options")

                found = False
                for inp in sms_inputs:
                    try:
                        label = inp.find_element(By.XPATH, "following-sibling::*[1]")
                        label_text = label.text.strip()
                        print(f"[{number}] Checking: {label_text}")

                        if number in label_text:
                            print(f"[{number}] Match found!")
                            click_element(driver, inp)
                            found = True
                            time.sleep(0.5)
                            break
                    except:
                        continue

                if not found:
                    print(f"[{number}] No SMS option available")
                    result["status"] = "no_sms"
                    result["message"] = "No SMS option available"
                    break

                # Click submit button
                submit_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '[name="reset_action"][type="submit"]')))
                click_element(driver, submit_btn)
                time.sleep(1)
                continue

            if flow == "IDENTIFY_YOUR_ACCOUNT":
                button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'a[role="button"][href*="/login/identify/?ctx=recover"]')))
                click_element(driver, button)
                continue

            if flow == "ACCOUNT_DISABLED":
                flows.remove_by_id("ACCOUNT_DISABLED")
                print(f"[{number}] Account disabled")
                result["status"] = "disabled"
                result["message"] = "Account disabled"
                break

            if flow == "SOMETHING_WENT_WRONG":
                flows.remove_by_id("SOMETHING_WENT_WRONG")
                result["status"] = "error"
                result["message"] = "Something went wrong"
                break

            if flow == "THROW_CAPTCHA":
                flows.remove_by_id("THROW_CAPTCHA")
                print(f"[{number}] Hit CAPTCHA")
                result["status"] = "captcha"
                result["message"] = "Hit CAPTCHA"
                break

            if flow == "ENTER_SECURITY_CODE":
                flows.remove_by_id("ENTER_SECURITY_CODE")
                print(f"[{number}] ✓ SUCCESS!")
                result["status"] = "success"
                result["message"] = "Security code page reached"
                time.sleep(10)
                break

    except TimeoutException:
        print(f"[{number}] Timeout")
        result["status"] = "timeout"
        result["message"] = "Operation timed out"
    except Exception as e:
        print(f"[{number}] Error: {str(e)}")
        result["status"] = "error"
        result["message"] = str(e)
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass

    return result


def main():
    print(f"Starting with {MAX_WORKERS} workers...")
    print(f"Processing {len(numbers)} numbers")
    print("-" * 50)

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_number = {executor.submit(agent, number): number for number in numbers}

        results = []
        for future in as_completed(future_to_number):
            number = future_to_number[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as exc:
                print(f"[{number}] Exception: {exc}")
                results.append({"number": number, "status": "exception", "message": str(exc)})

    print("-" * 50)
    print("Summary:")
    print("-" * 50)
    for result in results:
        print(f"{result['number']} | {result['status']} | {result['message']}")


if __name__ == '__main__':
    main()
