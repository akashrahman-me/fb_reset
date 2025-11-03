import undetected_chromedriver as uc

options = uc.ChromeOptions()
options.add_argument("--proxy-server=http://127.0.0.1:2476")


driver = uc.Chrome(options=options)
driver.set_window_size(1200, 800)
driver.get("https://www.facebook.com/login/identify/")

input("Press enter to quite...")
driver.quit()