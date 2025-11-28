import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException
from libs.FlowList import FlowList
from utils.flow_handler import flow_handler

with open("numbers.txt", "r") as f:
    numbers = f.read()

numbers = [num.strip() for num in numbers.split('\n') if num.strip()]


# Configuration
MAX_WORKERS = 20
FORGOT_URL = 'https://m.facebook.com/login/identify/'

# Lock for driver initialization to prevent race conditions
driver_init_lock = Lock()


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
        ("//span[normalize-space()='Before we send the code']", "RECHAPTCHA"),
    ])

    driver = None
    result = {"number": number, "status": "unknown", "message": ""}

    try:
        # Simple Chrome setup
        options = uc.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--headless=new")  # Uncomment for headless mode
        custom_user_agent = "Mozilla/5.0 (Linux; Android 8.0.0; SM-G955U Build/R16NW) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Mobile Safari/537.36"
        options.add_argument(f"--user-agent={custom_user_agent}")

        with driver_init_lock:
            driver = uc.Chrome(options=options)
            driver.set_window_size(375, 812)

        wait = WebDriverWait(driver, 30)
        driver.get(FORGOT_URL)

        while True:
            flow = flow_handler(driver, flows)

            print(f"[{number}]", "flow: ", flow)

            if flow == "MOBILE_NUMBER": # done
                flows.remove_by_id("MOBILE_NUMBER")

                # Fill in the phone number
                for i in range(999):
                    input_elem = wait.until(EC.element_to_be_clickable((By.XPATH, "//input[contains(@aria-label, 'Mobile number')]")))

                    input_elem.click()
                    input_elem.send_keys(number)

                    value = input_elem.get_attribute("value")

                    if value == number:
                        print(f"[{number}] Success filled after {i + 1} times try")
                        break

                # Submit the form
                continue_btn = driver.find_element(By.XPATH, "//span[normalize-space()='Continue']")
                click_element(driver, continue_btn)
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


            if flow == "RECHAPTCHA": # done
                flows.remove_by_id("RECHAPTCHA")
                result["status"] = "recaptcha"
                result["message"] = "Trow RECHAPTCHA"
                break


            if flow == "ACCOUNT_CONFIRM": # done
                flows.remove_by_id("ACCOUNT_CONFIRM")
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
                time.sleep(3)
                driver.quit()
            except:
                pass

    print(f'[{number}] {result["message"]}')
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
