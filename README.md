# MC Checker
Check releases for download.
MC Checker is a fast, terminal-based Minecraft username generator and availability checker written in Python. It targets short usernames (3–4 characters) and uses Mojang’s official API with an asynchronous architecture for significantly improved performance and reliability.

## Features

- Supports 3 and 4 character usernames
- Custom character sets (letters, numbers, or both)
- Optional underscore support
- Fully asynchronous checking using `asyncio` and `aiohttp`
- Configurable concurrent requests for high throughput
- Automatic retries with exponential backoff for rate limits and server errors
- Real-time progress and colored terminal output
- Categorizes results as Available, Taken, or Unclear
- Avoids duplicate checks using a local cache
- Saves all checked usernames to `checked_mc.txt` with timestamps
- Interactive CLI with persistent retry loop

## How It Works

Usernames are randomly generated based on user-selected rules and checked against Mojang’s official API:
https://api.mojang.com/users/profiles/minecraft/<username>

Response handling:
- `404 / 204` → Available  
- `200` → Taken  
- Timeouts / rate limits → Marked as unclear  

Async concurrency allows multiple usernames to be checked in parallel while respecting rate limits.

## Requirements

- Python 3.9+
- aiohttp (automatically installed on first run)
