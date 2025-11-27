import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from libs.FlowList import FlowList
from utils.flow_handler import flow_handler

numbers = """
2250712579031
2250712575559
2250712571137
2250712574881
2250712572794
2250712570511
2250712570223
2250712573276
2250712574964
2250712577700
2250712577957
2250712574615
2250712576292
2250712573186
2250712575336
2250712578370
2250712574092
2250712576788
2250712571978
2250712572163
2250712578124
2250712576696
2250712573324
2250712579233
2250712572082
2250712573086
2250712577006
2250712576432
2250712575366
2250712570050
2250712576125
2250712575087
2250712574298
2250712577593
2250712574839
2250712576953
2250712570789
2250712574794
2250712572482
2250712575850
2250712573594
2250712572277
2250712577635
2250712578046
2250712574781
2250712570102
2250712570420
2250712577382
2250712572656
2250712571782
2250712570859
2250712579761
2250712576681
2250712575179
2250712574982
2250712579507
2250712579883
2250712578629
2250712577212
2250712579394
2250712576027
2250712572169
2250712574522
2250712571584
2250712576461
2250712575910
2250712573032
2250712578593
2250712570566
2250712576743
2250712577463
2250712574925
2250712579084
2250712578408
2250712571151
2250712573059
2250712570614
2250712575011
2250712575337
2250712577474
2250712578144
2250712571767
2250712575082
"""

numbers = [num.strip() for num in numbers.split('\n') if num.strip()]


# Configuration
MAX_WORKERS = 7
FORGOT_URL = 'https://m.facebook.com/login/identify/'


def click_element(driver, element):
    """Simple click with JavaScript fallback"""
    try:
        element.click()
    except:
        driver.execute_script("arguments[0].click();", element)


def agent(number):
    """Process a single phone number"""

    flows = FlowList([
        # ("/span[normalize-space()='Forgotten password?']", "FORGOTTEN_PASSWORD"),
        ("//span[contains(normalize-space(), 'Enter your mobile number')]", "MOBILE_NUMBER"),
        ('//div[contains(normalize-space(), "t find your account")]', "COULD_NOT_FIND_ACCOUNT"),
        ('//div[contains(normalize-space(), "That didn\'t work")]', "COULD_NOT_FIND_ACCOUNT2"),
        # ("//div[normalize-space()='Failed to load']", "FAILED_TO_LOAD"),
        ("//span[normalize-space()='Try another way']", "TRY_ANOTHER_WAY"),
        ("//span[normalize-space()='Choose a way to log in.']", "CHOOSE_LOGIN_WAY"),
        ("//span[normalize-space()='Choose your account']", "CHOOSE_ACCOUNT"),
        ("//span[normalize-space()='Confirm your account']", "ACCOUNT_CONFIRM"),
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
        driver.set_window_size(375, 812)

        wait = WebDriverWait(driver, 30)
        driver.get(FORGOT_URL)

        while True:
            flow = flow_handler(driver, flows)

            if flow == "MOBILE_NUMBER": # done
                flows.remove_by_id("MOBILE_NUMBER")

                # Fill in the phone number
                input_elem = wait.until(EC.element_to_be_clickable((By.XPATH, "//input[contains(@aria-label, 'Mobile number')]")))
                input_elem.clear()
                input_elem.send_keys(number)
                time.sleep(0.5)

                # Submit the form
                input_elem.send_keys(Keys.ENTER)
                continue

            if flow == "COULD_NOT_FIND_ACCOUNT" or flow == "COULD_NOT_FIND_ACCOUNT2": # done
                flows.remove_by_id("COULD_NOT_FIND_ACCOUNT")
                flows.remove_by_id("COULD_NOT_FIND_ACCOUNT2")
                result["status"] = "no_account"
                result["message"] = "Couldn't find account"
                break

            if flow == "FAILED_TO_LOAD": # done
                flows.remove_by_id("FAILED_TO_LOAD")
                result["status"] = "internal_error"
                result["message"] = "Something went wrong"
                break


            if flow == "CHOOSE_ACCOUNT": # done
                flows.remove_by_id("CHOOSE_ACCOUNT")
                continue_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[contains(@style, 'border: 1px solid rgb(221, 226, 232)') and contains(@style, 'border-radius: 16px')]/div[1]/div[1]")))
                click_element(driver, continue_btn)
                continue

            if flow == "TRY_ANOTHER_WAY": # done
                flows.remove_by_id("TRY_ANOTHER_WAY")
                try_another_way = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[normalize-space()='Try another way']")))
                click_element(driver, try_another_way)
                continue

            if flow == "CHOOSE_LOGIN_WAY": # done
                flows.remove_by_id("CHOOSE_LOGIN_WAY")

                try:
                    code_via_sms =  WebDriverWait(driver, 1).until(EC.element_to_be_clickable((By.XPATH, "//span[normalize-space()='Get code or link via SMS']")))
                    click_element(driver, code_via_sms)
                except TimeoutException:
                    result["status"] = "code_unavailable"
                    result["message"] = "Code via SMS unavailable"
                    break

                submit_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[normalize-space()='Continue']")))
                click_element(driver, submit_btn)

                continue


            if flow == "ACCOUNT_CONFIRM": # done
                flows.remove_by_id("ACCOUNT_CONFIRM")
                print(f"[{number}] ✓ SUCCESS!")
                result["status"] = "success"
                result["message"] = "Security code page reached"
                time.sleep(3)
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

    print(result["message"])
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
