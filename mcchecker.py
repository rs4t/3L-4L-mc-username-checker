import random
import concurrent.futures
import os
import time
import threading
import subprocess
import sys

# Check and install requests if not available
try:
    import requests
except ImportError:
    print("Installing required package: requests...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "-q"])
    import requests

# Clear terminal
os.system('cls' if os.name == 'nt' else 'clear')

# Print banner
print('\033[96m' + r"""
___.                            _____   __   
\_ |__ ___.__. _______  ______ /  |  |_/  |_ 
 | __ <   |  | \_  __ \/  ___//   |  |\   __|
 | \_\ \___  |  |  | \/\___ \/    ^   /|  |  
 |___  / ____|  |__|  /____  >____   | |__|  
     \/\/                  \/     |__|       
MC CHECKER - github.com/rs4t""" + '\033[0m')

# ANSI color codes
CYAN = '\033[96m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BRIGHT_WHITE = '\033[97m'
GRAY = '\033[90m'
RESET = '\033[0m'

MAX_WORKERS = 5
REQUEST_TIMEOUT = 5
MAX_RETRIES = 3
BACKOFF_BASE_SECONDS = 0.4
RATE_LIMIT_DELAY_SECONDS = 0.2
EXTRA_RETRY_ROUNDS = 2

def print_banner():
    print(f"{CYAN}")
    print(r"""
___.                            _____   __   
\_ |__ ___.__. _______  ______ /  |  |_/  |_ 
 | __ <   |  | \_  __ \/  ___//   |  |\   __|
 | \_\ \___  |  |  | \/\___ \/    ^   /|  |  
 |___  / ____|  |__|  /____  >____   | |__|  
     \/\/                  \/     |__|       
MC CHECKER - github.com/rs4t""")
    print(f"{RESET}")

def print_selections(length=None, underscore=None, charset=None, amount=None):
    if length:
        print(f"{GREEN}Length:{RESET} {BRIGHT_WHITE}{length}{RESET}")
    if underscore is not None:
        print(f"{GREEN}_ :{RESET} {BRIGHT_WHITE}{underscore}{RESET}")
    if charset:
        print(f"{GREEN}Set:{RESET} {BRIGHT_WHITE}{charset}{RESET}")
    if amount:
        print(f"{GREEN}Amount:{RESET} {BRIGHT_WHITE}{amount}{RESET}")
    print()

checked_file_path = os.path.join(os.path.dirname(__file__), 'checked.txt')
thread_local = threading.local()

def get_session():
    if not hasattr(thread_local, "session"):
        session = requests.Session()
        session.headers.update({"User-Agent": "mc-userchecker/1.0"})
        thread_local.session = session
    return thread_local.session

def load_checked_usernames(path):
    checked = set()
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                # Extract username from lines like "✅ AVAILABLE: username" or "❌ Taken: username"
                if ': ' in line:
                    username = line.split(': ', 1)[1].strip()
                    if username:
                        checked.add(username)
    return checked

def generate_igns(count, seen, chars, N):
    igns = []
    local_seen = set()
    while len(igns) < count:
        ign = ''.join(random.choices(chars, k=N))
        if ign not in seen and ign not in local_seen:
            local_seen.add(ign)
            igns.append(ign)
    return igns

def check_ign(ign):
    url = f"https://api.mojang.com/users/profiles/minecraft/{ign}"
    for attempt in range(MAX_RETRIES):
        try:
            r = get_session().get(url, timeout=REQUEST_TIMEOUT)
            if r.status_code in (204, 404):
                return ("available", ign)
            if r.status_code == 200:
                return ("taken", ign)
            if r.status_code in (429, 500, 502, 503, 504):
                time.sleep(BACKOFF_BASE_SECONDS * (2 ** attempt))
                continue
            return ("unknown", ign)
        except requests.RequestException:
            time.sleep(BACKOFF_BASE_SECONDS * (2 ** attempt))
    return ("unknown", ign)

def run_checks(igns, max_workers, delay_between, file_handle=None, collect_unknowns=False):
    results = []
    unknowns = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {}

        for ign in igns:
            future = executor.submit(check_ign, ign)
            futures[future] = ign
            if delay_between > 0:
                time.sleep(delay_between)

        for future in concurrent.futures.as_completed(futures):
            ign = futures[future]
            status, checked_ign = future.result()
            results.append((status, checked_ign))
            
            if status == "available":
                label = "✅ AVAILABLE:"
                print(f"{GREEN}{label} {BRIGHT_WHITE}{checked_ign}{RESET}")
                if file_handle:
                    file_handle.write(f"{label} {checked_ign}\n")
                    file_handle.flush()
            elif status == "taken":
                label = "❌ Taken:"
                print(f"{GRAY}{label} {checked_ign}{RESET}")
                if file_handle:
                    file_handle.write(f"{label} {checked_ign}\n")
                    file_handle.flush()
            else:
                if collect_unknowns:
                    unknowns.append(checked_ign)

    return results, unknowns

retry = True
while retry:
    # Step 1: Choose length
    while True:
        length_choice = input(f"{YELLOW}Choose username length (3 or 4): {RESET}").strip()
        if length_choice in ("3", "4"):
            N = int(length_choice)
            os.system('cls' if os.name == 'nt' else 'clear')
            print_banner()
            print_selections(length=N)
            break
        print(f"{RED}Please enter 3 or 4.{RESET}")

    # Step 2: Choose underscore
    while True:
        underscore_choice = input(f"{YELLOW}Include underscores (_)? (y/n): {RESET}").strip().lower()
        if underscore_choice in ("y", "n"):
            include_underscore = underscore_choice == "y"
            underscore_display = "y" if include_underscore else "n"
            os.system('cls' if os.name == 'nt' else 'clear')
            print_banner()
            print_selections(length=N, underscore=underscore_display)
            break
        print(f"{RED}Please enter y or n.{RESET}")

    # Step 3: Choose character set
    print(f"{CYAN}Character set options:{RESET}")
    print("1: Letters only")
    print("2: Numbers only")
    print("3: Letters and numbers")

    while True:
        charset_choice = input(f"{YELLOW}Choose character set (1, 2, or 3): {RESET}").strip()
        if charset_choice == "1":
            chars = "abcdefghijklmnopqsstuvwxyz"
            if include_underscore:
                chars += "_"
            os.system('cls' if os.name == 'nt' else 'clear')
            print_banner()
            print_selections(length=N, underscore=underscore_display, charset=charset_choice)
            break
        elif charset_choice == "2":
            chars = "0123456789"
            if include_underscore:
                chars += "_"
            os.system('cls' if os.name == 'nt' else 'clear')
            print_banner()
            print_selections(length=N, underscore=underscore_display, charset=charset_choice)
            break
        elif charset_choice == "3":
            chars = "abcdefghijklmnopqsstuvwxyz0123456789"
            if include_underscore:
                chars += "_"
            os.system('cls' if os.name == 'nt' else 'clear')
            print_banner()
            print_selections(length=N, underscore=underscore_display, charset=charset_choice)
            break
        else:
            print(f"{RED}Please enter 1, 2, or 3.{RESET}")

    # Step 4: Choose amount
    tries = int(input(f"{YELLOW}How many IGNs would you like to test: {RESET}"))
    os.system('cls' if os.name == 'nt' else 'clear')
    print_banner()
    print_selections(length=N, underscore=underscore_display, charset=charset_choice, amount=tries)

    # Start checking
    print(f"{CYAN}Getting things ready, please be patient...{RESET}\n")
    checked_usernames = load_checked_usernames(checked_file_path)
    available_usernames = []
    
    igns_to_check = generate_igns(tries, checked_usernames, chars, N)
    max_workers = min(MAX_WORKERS, len(igns_to_check)) or 1

    with open(checked_file_path, 'a', encoding='utf-8') as f:
        # Write summary line for this run (with 2 blank lines before)
        f.write(f"\n\n{N} {underscore_display} {charset_choice} {tries}\n")
        f.flush()
        
        results, unknowns = run_checks(igns_to_check, max_workers, RATE_LIMIT_DELAY_SECONDS, f, True)
        
        for status, checked_ign in results:
            if status == "available":
                available_usernames.append(checked_ign)

        for round_index in range(EXTRA_RETRY_ROUNDS):
            if not unknowns:
                break
            print(f"\n{YELLOW}Retrying {len(unknowns)} rate-limited/timeouts (round {round_index + 1}/{EXTRA_RETRY_ROUNDS})...{RESET}")
            time.sleep(1.5 + (round_index * 0.5))
            retry_results, unknowns = run_checks(unknowns, 1, 0.35, f, True)

            for status, checked_ign in retry_results:
                if status == "available":
                    available_usernames.append(checked_ign)

        if unknowns:
            print(f"{YELLOW}⚠️  Skipped {len(unknowns)} usernames due to persistent rate limits/timeouts.{RESET}")

    print(f"\n{CYAN}" + "="*40 + f"{RESET}")
    if available_usernames:
        print(f"{GREEN}Found {len(available_usernames)} available username(s):{RESET}")
        for username in available_usernames:
            print(f"  {GREEN}•{RESET} {BRIGHT_WHITE}{username}{RESET}")
    else:
        print(f"{GRAY}No available IGN found after checking {tries} IGNs.{RESET}")
    print(f"{CYAN}" + "="*40 + f"{RESET}")
    
    user_input = input(f"\n{YELLOW}Press 1 to retry, or Enter to exit: {RESET}")
    if user_input == "1":
        os.system('cls' if os.name == 'nt' else 'clear')
        print_banner()
        print()
        retry = True
    else:
        retry = False
