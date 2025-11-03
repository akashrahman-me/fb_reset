import time, re
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from libs.FlowList import FlowList
from utils.clear_cookies import clear_cookies
from utils.flow_handler import flow_handler

numbers = """
2250799820746
2250799824683
2250799826616
"""

numbers = [num.strip() for num in numbers.split('\n') if num.strip()]



def main():


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



    for number in numbers:

        proxy_server = "127.0.0.1:8080"

        options = uc.ChromeOptions()
        # options.add_argument(f'--proxy-server={proxy_server}')
        # options.add_argument(f'--headless=new')

        driver = uc.Chrome(options=options)

        wait = WebDriverWait(driver, 9999)

        driver.get(FORGOT_URL)

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
                driver.quit()
                break

            if flow == "THROW_CAPTCHA":
                flows.remove_by_id("THROW_CAPTCHA")
                print("Hit CAPTCHA, skipping...")
                driver.quit()
                break

            if flow == "ENTER_SECURITY_CODE":
                flows.remove_by_id("ENTER_SECURITY_CODE")
                print("Success for number:", number)
                driver.quit()
                break



if __name__ == '__main__':
    main()
