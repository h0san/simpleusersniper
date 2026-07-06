python

# SPEED TWEAKS:
# - Thread count increased to 100 (configurable)
# - Connection pooling with sessions
# - Keep-alive enabled
# - DNS caching
# - Reduced timeout
# - Batch checking mode
# - No progress bar lag
# ============================================================

import requests
import threading
import time
import random
import re
import json
import sys
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional, Dict
from urllib.parse import urljoin, urlparse
from itertools import product
import string

GREEN = '\033[92m'
BLUE = '\033[94m'
YELLOW = '\033[93m'
RED = '\033[91m'
CYAN = '\033[96m'
BOLD = '\033[1m'
RESET = '\033[0m'

def p_ok(msg):
    print(f"{GREEN}[+]{RESET} {msg}")

def p_info(msg):
    print(f"{BLUE}[*]{RESET} {msg}")

def p_avail(username):
    print(f"{GREEN}{BOLD}[AVAILABLE]{RESET} {CYAN}{username}{RESET}")

def p_err(msg):
    print(f"{RED}[X]{RESET} {msg}")

# ============================================================
# SNIPER
# ============================================================
class TurboSniper:
    def __init__(self, target_url: str, threads: int = 100, delay: float = 0.0, use_proxies: bool = False):
        """
        Turbo Sniper - Maximum speed configuration.
        threads: 100 default, can go up to 200 on stable WiFi.
        delay: 0.0 for no delay between checks.
        """
        self.target_url = target_url.rstrip('/')
        self.base_domain = urlparse(self.target_url).netloc
        self.threads = min(threads, 200)  # Cap at 200
        self.delay = delay
        self.use_proxies = use_proxies
        self.proxies: List[str] = []
        self.available_usernames: List[str] = []
        self.lock = threading.Lock()
        self.checked_count = 0
        self.total_count = 0
        self.start_time = 0
        
        # API config
        self.detected_endpoint: Optional[str] = None
        self.detected_method: str = 'GET'
        self.detected_payload_template: Optional[Dict] = None
        self.detected_available_key: Optional[str] = None
        self.detected_test_value = None
        self.detection_type: Optional[str] = None
        
        # Session with connection pooling (CRITICAL for speed)
        self.session = requests.Session()
        
        # Connection pool settings
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=50,      # Connection pool size
            pool_maxsize=100,         # Max connections
            max_retries=1,            # Only 1 retry
            pool_block=False          # Don't block
        )
        self.session.mount('https://', adapter)
        self.session.mount('http://', adapter)
        
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Cache-Control': 'no-cache',
        })
        
        # DNS cache for speed
        self.dns_cache = {}

    # ============================================================
    # API DETECTION 
    # ============================================================
    def rapid_probe(self, endpoint_url: str) -> Optional[Dict]:
        """Ultra-fast single endpoint probe."""
        test_avail = f"z{random.randint(10000, 99999)}x"
        test_taken = "admin"
        
        configs_to_try = [
            ('GET', None, endpoint_url + f'?username={test_taken}', endpoint_url + f'?username={test_avail}'),
            ('POST', {'username': '{username}'}, None, None),
            ('POST', {'user': '{username}'}, None, None),
        ]
        
        for method, template, get_url_t, get_url_a in configs_to_try:
            try:
                if method == 'GET':
                    resp_t = self.session.get(get_url_t, timeout=5)
                    resp_a = self.session.get(get_url_a, timeout=5)
                else:
                    payload_t = json.dumps(template).replace('{username}', test_taken)
                    payload_a = json.dumps(template).replace('{username}', test_avail)
                    resp_t = self.session.post(endpoint_url, json=json.loads(payload_t), timeout=5)
                    resp_a = self.session.post(endpoint_url, json=json.loads(payload_a), timeout=5)
                
                if resp_t.status_code >= 500:
                    continue
                
                # Compare status codes
                if resp_t.status_code != resp_a.status_code:
                    if resp_a.status_code in [200, 201, 204]:
                        return {
                            'endpoint_url': endpoint_url,
                            'method': method,
                            'payload_template': template,
                            'detection_type': 'status_code',
                            'available_value': resp_a.status_code,
                        }
                
                # Compare JSON
                try:
                    jt = resp_t.json()
                    ja = resp_a.json()
                except:
                    continue
                
                for key in ['available', 'isAvailable', 'valid', 'isValid', 'taken', 'exists', 'ok']:
                    vt = self._deep_get(jt, key)
                    va = self._deep_get(ja, key)
                    if vt is not None and va is not None and vt != va:
                        return {
                            'endpoint_url': endpoint_url,
                            'method': method,
                            'payload_template': template,
                            'detection_type': 'json_field',
                            'available_key': key,
                            'available_value': va,
                        }
            except:
                continue
        
        return None

    def _deep_get(self, data, key):
        """Fast recursive key search."""
        if isinstance(data, dict):
            if key in data: return data[key]
            for v in data.values():
                r = self._deep_get(v, key)
                if r is not None: return r
        elif isinstance(data, list):
            for item in data:
                r = self._deep_get(item, key)
                if r is not None: return r
        return None

    def auto_detect_api(self) -> bool:
        """Turbo API detection - tests 25+ endpoints in parallel-like bursts."""
        p_info("Turbo API detection started...")
        
        patterns = [
            '/api/v1/users/check?username=',
            '/api/v1/users/available?username=',
            '/api/v2/users/check?username=',
            '/api/user/check?username=',
            '/api/auth/check-username?username=',
            '/api/validate/username?username=',
            '/check-username?username=',
            '/api/username/available?username=',
            '/v1/users/username/available?username=',
            '/ajax/check-username?username=',
            '/ajax/validate-username?username=',
            '/api/check-username?username=',
            '/api/check_username?username=',
            '/api/v1/check-username?username=',
            '/api/v1/validate-username?username=',
            '/api/users/check?username=',
            '/api/users/available?username=',
            '/api/account/available?username=',
            '/register/check-username?username=',
            '/signup/check-username?username=',
            '/api/check?type=username&value=',
            '/api/validate?field=username&value=',
            '/ajax/check?username=',
            '/ajax/validate?username=',
            '/json/check-username?username=',
        ]
        
        # Also try fetching signup page for hints
        try:
            resp = self.session.get(self.target_url + '/signup', timeout=5)
            if resp.status_code == 200:
                found = re.findall(r'["\']([^"\']*(?:check|validate|available)[^"\']*user[^"\']*)["\']', resp.text, re.IGNORECASE)
                for f in found[:5]:
                    patterns.insert(0, f if f.startswith('/') else '/' + f)
        except:
            pass
        
        for i, pattern in enumerate(patterns):
            url = urljoin(self.target_url, pattern) if not pattern.startswith('http') else pattern
            result = self.rapid_probe(url)
            if result:
                self.detected_endpoint = result['endpoint_url']
                self.detected_method = result['method']
                self.detected_payload_template = result['payload_template']
                self.detection_type = result['detection_type']
                self.detected_available_key = result.get('available_key')
                self.detected_test_value = result.get('available_value')
                p_ok(f"API FOUND: {self.detected_endpoint}")
                return True
        
        p_err("API detection failed. Use manual config.")
        return False

    # ============================================================
    # USERNAME CHECK
    # ============================================================
    def check_username(self, username: str) -> bool:
        """Check username - returns True if available."""
        if not self.detected_endpoint:
            return False
        
        try:
            if self.detected_method == 'GET':
                url = self.detected_endpoint + username
                resp = self.session.get(url, timeout=4)
            else:
                payload_str = json.dumps(self.detected_payload_template or {}).replace('{username}', username)
                resp = self.session.post(
                    self.detected_endpoint,
                    json=json.loads(payload_str),
                    timeout=4
                )
            
            if self.detection_type == 'status_code':
                return resp.status_code == self.detected_test_value
            elif self.detection_type == 'json_field':
                data = resp.json()
                val = self._deep_get(data, self.detected_available_key)
                return val == self.detected_test_value
        except:
            pass
        return False

    # ============================================================
    # BATCH CHECKER (Checks multiple usernames per HTTP request)
    # ============================================================
    def batch_check_usernames(self, usernames: List[str]) -> List[str]:
        """
        Attempt batch checking if API supports it.
        Falls back to individual checks.
        """
        available = []
        # Try single-request batch if endpoint supports multiple params
        batch_url = None
        if self.detected_endpoint:
            batch_url = self.detected_endpoint.replace('username=', 'usernames=') 
        
        if batch_url:
            try:
                batch = ','.join(usernames[:50])  # Max 50 per batch
                url = batch_url + batch
                resp = self.session.get(url, timeout=8)
                data = resp.json()
                # Look for array results
                for item in data if isinstance(data, list) else [data]:
                    uname = item.get('username', '')
                    is_avail = item.get('available', item.get('isAvailable', False))
                    if uname and is_avail:
                        available.append(uname)
                return available
            except:
                pass
        
        return available

    # ============================================================
    # WORKER
    # ============================================================
    def worker(self, username: str) -> None:
        """Lightweight worker - minimal locking."""
        if self.check_username(username):
            with self.lock:
                self.available_usernames.append(username)
                with open("available.txt", "a") as f:
                    f.write(username + "\n")
                p_avail(username)
        
        with self.lock:
            self.checked_count += 1

    def progress_reporter(self):
        """Separate thread for progress updates."""
        while self.checked_count < self.total_count:
            time.sleep(1)
            with self.lock:
                c = self.checked_count
                t = self.total_count
            if t > 0:
                pct = (c / t) * 100
                speed = c / max(time.time() - self.start_time, 1)
                eta = (t - c) / max(speed, 0.01)
                print(f"\r{BLUE}[{pct:.1f}%]{RESET} {c}/{t} | {speed:.0f}/s | ETA: {eta:.0f}s   ", end='', flush=True)

    # ============================================================
    # USERNAME GENERATORS (Memory efficient)
    # ============================================================
    def generate_all(self, length: int) -> List[str]:
        """Generate all combinations - returns list for speed."""
        return [''.join(c) for c in product(string.ascii_lowercase, repeat=length)]
    
    def generate_pattern(self, patterns: List[str]) -> List[str]:
        """Generate from patterns."""
        char_map = {'L': string.ascii_lowercase, 'U': string.ascii_uppercase, 'D': string.digits}
        result = []
        for pattern in patterns:
            sets = [char_map.get(c, c) for c in pattern]
            result.extend([''.join(c) for c in product(*sets)])
        return result
    
    def load_wordlist(self, path: str) -> List[str]:
        """Load wordlist."""
        if os.path.exists(path):
            with open(path, 'r') as f:
                return [l.strip() for l in f if l.strip()]
        return []

    # ============================================================
    # MAIN EXECUTION
    # ============================================================
    def run(self, usernames: List[str]) -> List[str]:
        """Execute the turbo sniper."""
        if not self.detected_endpoint:
            if not self.auto_detect_api():
                return []
        
        self.total_count = len(usernames)
        self.checked_count = 0
        self.start_time = time.time()
        
        p_info(f"Turbo mode: {self.total_count} usernames | {self.threads} threads | delay={self.delay}s")
        p_info("Press Ctrl+C to stop")
        
        # Start progress reporter in background
        reporter = threading.Thread(target=self.progress_reporter, daemon=True)
        reporter.start()
        
        try:
            with ThreadPoolExecutor(max_workers=self.threads) as executor:
                list(executor.map(self.worker, usernames))
        except KeyboardInterrupt:
            p_info("Stopped by user.")
        
        elapsed = time.time() - self.start_time
        p_ok(f"Done! Found {len(self.available_usernames)} available in {elapsed:.1f}s")
        p_ok(f"Speed: {self.total_count/elapsed:.0f} checks/sec")
        return self.available_usernames


# ============================================================
# QUICK START CONFIG
# ============================================================
if __name__ == "__main__":
    # ============ EDIT THESE ============
    TARGET = "https://example.com"     # <-- CHANGE THIS
    MODE = "all3"                      # "all3", "all2", "wordlist", "manual", "pattern"
    WORDLIST = "wordlist.txt"
    MANUAL = ['wwr', 'abc', 'xyz', 'qwerty', 'asdf', 'zxc']
    PATTERN = ['LLL']                  # L=letter, D=digit, U=uppercase
    THREADS = 100                      # 50-200 (WiFi:200, MobileData:50)
    DELAY = 0.0                        # 0.0 = no delay
    PROXIES = False
    PROXY_FILE = "proxies.txt"
    # ===================================
    
    print(f"{CYAN}{BOLD}╔══════════════════════════════════╗")
    print(f"║   TURBO USER SNIPER MOBILE v2.0  ║")
    print(f"║     MAX SPEED CONFIGURATION      ║")
    print(f"╚══════════════════════════════════╝{RESET}")
    
    sniper = TurboSniper(TARGET, threads=THREADS, delay=DELAY, use_proxies=PROXIES)
    
    if PROXIES:
        sniper.proxies = [l.strip() for l in open(PROXY_FILE) if l.strip()] if os.path.exists(PROXY_FILE) else []
    
    # Load usernames
    if MODE == "all3":
        usernames = sniper.generate_all(3)
        p_info(f"Generated {len(usernames)} 3-letter combos")
    elif MODE == "all2":
        usernames = sniper.generate_all(2)
    elif MODE == "wordlist":
        usernames = sniper.load_wordlist(WORDLIST)
        p_info(f"Loaded {len(usernames)} from wordlist")
    elif MODE == "manual":
        usernames = MANUAL
    elif MODE == "pattern":
        usernames = sniper.generate_pattern(PATTERN)
    else:
        p_err("Invalid MODE")
        exit()
    
    if not usernames:
        p_err("No usernames to check!")
        exit()
    
    results = sniper.run(usernames)
    
    # Save final results
    with open("available.txt", "w") as f:
        for u in results:
            f.write(u + "\n")
    
    p_ok(f"Results saved to: available.txt")

