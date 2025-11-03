import concurrent.futures
import tempfile
import shutil
import psutil
import undetected_chromedriver as uc
import os

def open_site(i):
    # Create isolated temporary user profile for each browser
    profile_dir = tempfile.mkdtemp(prefix=f"chrome_profile_{i}_")

    options = uc.ChromeOptions()
    # options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=800,600")
    options.add_argument("--blink-settings=imagesEnabled=false")
    options.add_argument(f"--user-data-dir={profile_dir}")
    options.add_argument("--disk-cache-size=104857600")  # 100 MB cache
    options.add_argument("--media-cache-size=10485760")  # 10 MB media cache
    options.add_argument("--enable-application-cache")


    proxy_server = "127.0.0.1:8080"
    options.add_argument(f'--proxy-server={proxy_server}')

    try:
        driver = uc.Chrome(options=options)
        driver.get("https://google.com")
        print(f"[{i}] Opened:", driver.title)
        driver.quit()
    finally:
        # Clean up temporary profile to free space
        shutil.rmtree(profile_dir, ignore_errors=True)

# --- auto adjust concurrency based on free RAM ---
def get_optimal_workers():
    free_gb = psutil.virtual_memory().available / (1024 ** 3)
    workers = int(free_gb // 0.35)  # assume ~350 MB per Chrome
    return workers

if __name__ == "__main__":
    max_workers = get_optimal_workers()
    print(f"Detected free RAM: {psutil.virtual_memory().available / (1024**3):.2f} GB")
    print(f"Running with {max_workers} concurrent browsers...")

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        futures = [executor.submit(open_site, i) for i in range(1, 21)]
        concurrent.futures.wait(futures)
