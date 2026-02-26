import subprocess
import sys
import os

# Install aiohttp if not already installed
try:
    import aiohttp
except ImportError:
    print("📦 Installing aiohttp...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "aiohttp"])
    import aiohttp

import random
import asyncio
from datetime import datetime

# Clear terminal
os.system('cls' if os.name == 'nt' else 'clear')

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

MAX_CONCURRENT = 8
REQUEST_TIMEOUT = 15
MAX_RETRIES = 3
BACKOFF_BASE_SECONDS = 0.4

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

checked_file_path = os.path.join(os.path.dirname(__file__), 'checked_mc.txt')

def load_checked_usernames(path):
    """Load previously checked usernames from file"""
    checked = set()
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                if ': ' in line:
                    username = line.split(': ', 1)[1].strip()
                    if username:
                        checked.add(username)
    return checked

def generate_igns(count, seen, chars, N):
    """Generate random IGNs"""
    igns = []
    local_seen = set()
    while len(igns) < count:
        ign = ''.join(random.choices(chars, k=N))
        if ign not in seen and ign not in local_seen:
            local_seen.add(ign)
            igns.append(ign)
    return igns

async def check_ign(ign, session, semaphore):
    """
    Check if a Minecraft IGN is available via Mojang API.
    
    Returns:
        ("available", ign) if 404/204 response
        ("taken", ign) if 200 response (profile exists)
        ("unclear", ign) if error/timeout
    """
    url = f"https://api.mojang.com/users/profiles/minecraft/{ign}"
    
    async with semaphore:
        for attempt in range(MAX_RETRIES):
            try:
                headers = {"User-Agent": "mcchecker-improved/1.0"}
                timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)
                
                async with session.get(url, headers=headers, timeout=timeout) as resp:
                    status = resp.status
                    
                    if status in (204, 404):
                        # Not found = available
                        return ("available", ign)
                    
                    if status == 200:
                        # Found = taken
                        return ("taken", ign)
                    
                    if status in (429, 500, 502, 503, 504):
                        # Rate limit or server error - retry
                        await asyncio.sleep(BACKOFF_BASE_SECONDS * (2 ** attempt))
                        continue
                    
                    return ("unclear", ign)
            
            except asyncio.TimeoutError:
                await asyncio.sleep(BACKOFF_BASE_SECONDS * (2 ** attempt))
                continue
            except Exception as e:
                await asyncio.sleep(BACKOFF_BASE_SECONDS * (2 ** attempt))
                continue
        
        return ("unclear", ign)

async def run_checks(igns, file_handle=None):
    """Run all IGN checks concurrently"""
    results = []
    available = []
    taken = []
    unclear = []
    
    connector = aiohttp.TCPConnector(limit=MAX_CONCURRENT)
    timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)
    
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        semaphore = asyncio.Semaphore(MAX_CONCURRENT)
        
        # Create tasks for all IGNs
        tasks = [check_ign(ign, session, semaphore) for ign in igns]
        
        # Run with progress
        for i, task in enumerate(asyncio.as_completed(tasks), 1):
            status, ign = await task
            results.append((status, ign))
            
            if status == "available":
                available.append(ign)
                label = "✅ AVAILABLE:"
                print(f"{GREEN}{label} {BRIGHT_WHITE}{ign}{RESET}")
                if file_handle:
                    file_handle.write(f"{label} {ign}\n")
                    file_handle.flush()
            elif status == "taken":
                taken.append(ign)
                label = "❌ Taken:"
                print(f"{GRAY}{label} {ign}{RESET}")
                if file_handle:
                    file_handle.write(f"{label} {ign}\n")
                    file_handle.flush()
            else:
                unclear.append(ign)
            
            # Progress indicator
            print(f"{GRAY}[{i}/{len(igns)}]{RESET}", end='\r')
        
        print(" " * 30, end='\r')  # Clear progress line
    
    return results, available, taken, unclear

async def main():
    """Main async loop"""
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
                chars = "abcdefghijklmnopqrstuvwxyz"
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
                chars = "abcdefghijklmnopqrstuvwxyz0123456789"
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
        print(f"{CYAN}Getting things ready, please be patient...{RESET}")
        print(f"{YELLOW}Note: Using async for better performance (~8 concurrent requests){RESET}\n")
        
        checked_usernames = load_checked_usernames(checked_file_path)
        igns_to_check = generate_igns(tries, checked_usernames, chars, N)
        
        with open(checked_file_path, 'a', encoding='utf-8') as f:
            f.write(f"\n\n{N} {underscore_display} {charset_choice} {tries} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.flush()
            
            # Run async checks
            results, available, taken, unclear = await run_checks(igns_to_check, f)
            
            if unclear:
                print(f"\n{YELLOW}⚠️  {len(unclear)} results unclear (rate limit/error) - may retry{RESET}")

        # Print summary
        print(f"\n{CYAN}" + "="*40 + f"{RESET}")
        print(f"{GREEN}Available: {len(available)}{RESET}")
        print(f"{GRAY}Taken: {len(taken)}{RESET}")
        print(f"{YELLOW}Unclear: {len(unclear)}{RESET}")
        
        if available:
            print(f"\n{GREEN}Found {len(available)} available IGN(s):{RESET}")
            for ign in available:
                print(f"  {GREEN}•{RESET} {BRIGHT_WHITE}{ign}{RESET}")
        
        print(f"{CYAN}" + "="*40 + f"{RESET}")
        
        # Ask to continue
        user_input = input(f"\n{YELLOW}Press 1 to retry, or Enter to exit: {RESET}")
        if user_input == "1":
            os.system('cls' if os.name == 'nt' else 'clear')
            print_banner()
            print()
            retry = True
        else:
            retry = False

if __name__ == "__main__":
    asyncio.run(main())
