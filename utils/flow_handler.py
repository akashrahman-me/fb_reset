import time

from selenium.common import NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.common.by import By


def flow_handler(driver, selectors, timeout=9999, interval=0.25):
    start = time.time()

    while time.time() - start < timeout:
        try:
            for selector in selectors:
                try:
                    elem = driver.find_element(By.XPATH, selector[0])
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

