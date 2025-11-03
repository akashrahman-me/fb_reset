import os
import shutil

CACHE_DIR = "./mitmproxy_cache"

if os.path.exists(CACHE_DIR):
    shutil.rmtree(CACHE_DIR)
    print(f"✓ Cache cleared: {CACHE_DIR}")
    os.makedirs(CACHE_DIR, exist_ok=True)
    print(f"✓ Cache directory recreated: {CACHE_DIR}")
else:
    print(f"⚠ Cache directory doesn't exist: {CACHE_DIR}")

