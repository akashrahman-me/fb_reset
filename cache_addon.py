# cache_addon.py
import os
import sqlite3
import hashlib
import json
import time
import tempfile
import threading
from collections import OrderedDict
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse
from email.utils import parsedate_to_datetime
from mitmproxy import http, ctx


## CLEANUP CACHED DATA ONLY FOR DEVELOPMENT TIME
import shutil
CACHE_DIR = "./mitmproxy_cache"
if os.path.exists(CACHE_DIR):
    shutil.rmtree(CACHE_DIR)
    print(f"✓ Cache cleared: {CACHE_DIR}")
    os.makedirs(CACHE_DIR, exist_ok=True)
    print(f"✓ Cache directory recreated: {CACHE_DIR}")
else:
    print(f"⚠ Cache directory doesn't exist: {CACHE_DIR}")



# ---------- CONFIG ----------
CACHE_DIR = os.path.expanduser("./mitmproxy_cache")   # bodies stored here
DB_PATH = os.path.join(CACHE_DIR, "cache.sqlite")
CLEANUP_INTERVAL = 10000              # cleanup expired entries every 10,000 requests (very rare)
MEMORY_CACHE_SIZE = 10000             # keep 10,000 most recent responses in RAM (super fast!)
# If True, cache responses even when they include Set-Cookie (dangerous for auth flows)
ALLOW_SET_COOKIE_CACHE = False
# Query param names to drop from the key because they are usually cache-busters
CACHE_BUSTER_KEYS = {"_", "t", "ts", "timestamp", "cb", "rand", "version", "v", "cachebuster"}
# ----------------------------

os.makedirs(CACHE_DIR, exist_ok=True)

def _normalize_url(raw_url: str) -> str:
    """
    Normalize URL by removing common cache-buster query params and
    by sorting remaining params to produce deterministic order.
    """
    try:
        p = urlparse(raw_url)
        qs = parse_qsl(p.query, keep_blank_values=True)
        # filter out cache-buster keys and parameters that are pure numeric timestamps (heuristic)
        filtered = []
        for k, v in qs:
            if k.lower() in CACHE_BUSTER_KEYS:
                continue
            # drop param if name ends with 'timestamp' or if value looks like a unix ts (10 digits)
            if k.lower().endswith("timestamp") or (v.isdigit() and (9 <= len(v) <= 13)):
                continue
            filtered.append((k, v))
        # sort for deterministic order
        filtered.sort()
        new_qs = urlencode(filtered, doseq=True)
        new_p = p._replace(query=new_qs)
        return urlunparse(new_p)
    except Exception:
        return raw_url

def _make_key(request: http.Request) -> str:
    # key based on method + normalized url + body (if any)
    body = request.get_text() if request.content else ""
    url = _normalize_url(request.url)
    raw = f"{request.method.upper()} {url} {body}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

def _parse_cache_ttl(headers) -> float:
    """
    Parse cache headers to determine TTL.
    Returns:
    - float: TTL in seconds (can be very large for long-term caching)
    - None: Cache forever (infinite TTL)
    """
    # Check Cache-Control header
    cache_control = headers.get("cache-control", "").lower()

    if cache_control:
        # Check for no-cache, no-store
        if "no-cache" in cache_control or "no-store" in cache_control:
            return 0  # Don't cache

        # Look for max-age
        for directive in cache_control.split(","):
            directive = directive.strip()
            if directive.startswith("max-age="):
                try:
                    max_age = int(directive.split("=")[1])
                    if max_age > 0:
                        ctx.log.info(f"[CACHE] Found max-age={max_age} seconds in Cache-Control")
                        return float(max_age)
                except (ValueError, IndexError):
                    pass
            elif directive.startswith("s-maxage="):
                try:
                    s_maxage = int(directive.split("=")[1])
                    if s_maxage > 0:
                        ctx.log.info(f"[CACHE] Found s-maxage={s_maxage} seconds in Cache-Control")
                        return float(s_maxage)
                except (ValueError, IndexError):
                    pass

    # Check Expires header
    expires = headers.get("expires", "")
    if expires:
        try:
            expires_dt = parsedate_to_datetime(expires)
            now = time.time()
            expires_ts = expires_dt.timestamp()
            ttl = expires_ts - now
            if ttl > 0:
                ctx.log.info(f"[CACHE] Found Expires header, TTL={int(ttl)} seconds")
                return ttl
        except Exception as e:
            ctx.log.debug(f"[CACHE] Failed to parse Expires header: {e}")

    # No expiration specified - cache forever!
    ctx.log.info(f"[CACHE] No expiration headers found - caching FOREVER (infinite TTL)")
    return None  # None means infinite

class LRUCache:
    """Simple thread-safe LRU cache for response bodies"""
    def __init__(self, max_size=100):
        self.cache = OrderedDict()
        self.max_size = max_size
        self.lock = threading.Lock()

    def get(self, key):
        with self.lock:
            if key in self.cache:
                # Move to end (most recently used)
                self.cache.move_to_end(key)
                return self.cache[key]
            return None

    def put(self, key, value):
        with self.lock:
            if key in self.cache:
                self.cache.move_to_end(key)
            else:
                self.cache[key] = value
                if len(self.cache) > self.max_size:
                    # Remove least recently used
                    self.cache.popitem(last=False)

class SQLiteCacheAddon:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=30)
        self.conn.execute("PRAGMA journal_mode=WAL;")
        self.conn.execute("PRAGMA synchronous=NORMAL;")
        self.conn.execute("PRAGMA temp_store=MEMORY;")
        self._ensure_schema()
        self.lock = threading.Lock()
        self.request_count = 0
        self.memory_cache = LRUCache(MEMORY_CACHE_SIZE)

    def _ensure_schema(self):
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    status INTEGER,
                    headers TEXT,
                    body_path TEXT,
                    ts REAL,
                    expires_at REAL
                );
            """)

    def _lookup(self, key):
        cur = self.conn.execute("SELECT status, headers, body_path, ts, expires_at FROM cache WHERE key = ?", (key,))
        row = cur.fetchone()
        if not row:
            return None
        status, headers_json, body_path, ts, expires_at = row
        return {
            "status": status,
            "headers": json.loads(headers_json),
            "body_path": body_path,
            "ts": ts,
            "expires_at": expires_at
        }

    def _store(self, key, status, headers, body_bytes, ttl):
        body_fn = os.path.join(CACHE_DIR, f"{key}.body")
        tmp_fd, tmp_path = tempfile.mkstemp(dir=CACHE_DIR)
        try:
            os.write(tmp_fd, body_bytes)
            os.close(tmp_fd)
            os.replace(tmp_path, body_fn)
        finally:
            try:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except Exception:
                pass

        headers_json = json.dumps(dict(headers))
        ts = time.time()

        # Calculate expiration timestamp
        # None means infinite (store as NULL in DB)
        expires_at = None if ttl is None else (ts + ttl)

        with self.conn:
            self.conn.execute(
                "INSERT OR REPLACE INTO cache (key, status, headers, body_path, ts, expires_at) VALUES (?, ?, ?, ?, ?, ?)",
                (key, status, headers_json, body_fn, ts, expires_at)
            )

    def _delete_entry(self, key, body_path):
        with self.conn:
            self.conn.execute("DELETE FROM cache WHERE key = ?", (key,))
        try:
            if body_path and os.path.exists(body_path):
                os.remove(body_path)
        except Exception:
            pass

    def _cleanup_expired(self):
        now = time.time()
        # Only delete entries where expires_at is NOT NULL and is less than now
        cur = self.conn.execute(
            "SELECT key, body_path FROM cache WHERE expires_at IS NOT NULL AND expires_at < ?",
            (now,)
        )
        rows = cur.fetchall()
        if rows:
            ctx.log.info(f"[CACHE] Cleaning up {len(rows)} expired entries")
        for key, body_path in rows:
            self._delete_entry(key, body_path)

    # mitmproxy event: when client request arrives
    def request(self, flow: http.HTTPFlow):
        req = flow.request
        # Only cache GET requests
        if req.method.upper() != "GET":
            ctx.log.debug(f"[CACHE] skip (not GET) {req.method} {req.url}")
            return

        # skip if Authorization header present (private)
        if any(h.lower() == "authorization" for h in req.headers.keys()):
            ctx.log.debug(f"[CACHE] skip (Authorization header) {req.url}")
            return

        key = _make_key(req)

        with self.lock:
            entry = self._lookup(key)
            self.request_count += 1

        if entry:
            # check freshness
            expires_at = entry.get("expires_at")

            # If expires_at is None, it's cached forever - always serve it
            # If expires_at is set, check if it's still valid
            is_expired = False
            if expires_at is not None:
                if time.time() >= expires_at:
                    is_expired = True

            if not is_expired:
                body_path = entry["body_path"]
                if body_path and os.path.exists(body_path):
                    try:
                        # Try to get from memory cache first (FAST!)
                        content = self.memory_cache.get(key)
                        if content is None:
                            # Not in memory, read from disk
                            with open(body_path, "rb") as bf:
                                content = bf.read()
                            # Store in memory cache for next time
                            self.memory_cache.put(key, content)
                            ctx.log.debug(f"[CACHE] loaded from disk into memory key={key}")

                        headers = entry["headers"]
                        flow.response = http.Response.make(
                            entry["status"],
                            content,
                            headers
                        )
                        flow.response.headers["x-mitmproxy-cache"] = "HIT"
                        # Mark this flow as served from cache
                        flow.metadata["cache_hit"] = True

                        age = int(time.time() - entry["ts"])
                        if expires_at is None:
                            ctx.log.info(f"[CACHE] HIT {req.url} key={key} age={age}s (INFINITE TTL)")
                        else:
                            remaining = int(expires_at - time.time())
                            ctx.log.info(f"[CACHE] HIT {req.url} key={key} age={age}s (expires in {remaining}s)")
                        return
                    except Exception as e:
                        ctx.log.warn(f"[CACHE] hit-but-failed-to-serve {req.url} key={key} err={e}")
                        # fallthrough to fetch live
                else:
                    ctx.log.debug(f"[CACHE] entry exists but body missing for key={key}")
            else:
                # expired
                age = int(time.time() - entry["ts"])
                ctx.log.info(f"[CACHE] expired key={key} age={age}s -- deleting")
                try:
                    self._delete_entry(key, entry.get("body_path"))
                except Exception:
                    pass

        # periodic cleanup trigger
        if self.request_count >= CLEANUP_INTERVAL:
            with self.lock:
                try:
                    self._cleanup_expired()
                except Exception:
                    pass
                self.request_count = 0

        # log MISS for visibility
        ctx.log.info(f"[CACHE] MISS (will fetch) {req.url} key={key}")

    # mitmproxy event: when server responds
    def response(self, flow: http.HTTPFlow):
        # Skip if this was served from cache
        if flow.metadata.get("cache_hit"):
            return

        req = flow.request
        resp = flow.response
        if req.method.upper() != "GET":
            return
        if resp is None:
            return
        status = resp.status_code
        if not (200 <= status < 300):
            ctx.log.debug(f"[CACHE] skip storing non-2xx {status} {req.url}")
            return

        if any(h.lower() == "authorization" for h in req.headers.keys()):
            ctx.log.debug(f"[CACHE] skip storing (Authorization header) {req.url}")
            return

        if any(h.lower() == "set-cookie" for h in resp.headers.keys()):
            if not ALLOW_SET_COOKIE_CACHE:
                ctx.log.info(f"[CACHE] skip storing (Set-Cookie present) {req.url}")
                return
            else:
                ctx.log.info(f"[CACHE] WARNING: storing despite Set-Cookie present {req.url}")

        key = _make_key(req)
        body_bytes = resp.content or b""

        # Parse TTL from response headers
        ttl = _parse_cache_ttl(resp.headers)

        # Don't cache if ttl is 0 (no-cache/no-store)
        if ttl == 0:
            ctx.log.info(f"[CACHE] NOT storing (no-cache/no-store directive) {req.url}")
            return

        try:
            with self.lock:
                self._store(key, status, resp.headers, body_bytes, ttl)
                # Store in memory cache immediately
                self.memory_cache.put(key, body_bytes)
                # Add MISS header to indicate this was fetched from server
                resp.headers["x-mitmproxy-cache"] = "MISS"

                if ttl is None:
                    ctx.log.info(f"[CACHE] stored {req.url} key={key} size={len(body_bytes)} TTL=INFINITE ♾️")
                else:
                    ctx.log.info(f"[CACHE] stored {req.url} key={key} size={len(body_bytes)} TTL={int(ttl)}s")
        except Exception as e:
            ctx.log.warn(f"[CACHE] failed to store {req.url} key={key} err={e}")

addons = [
    SQLiteCacheAddon()
]

# cd
# mitmdump -s cache_addon.py -p 2476
# mitmweb -s cache_addon.py -p 2476
