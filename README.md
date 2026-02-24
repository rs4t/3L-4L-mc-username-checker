# MC Checker

MC Checker is a terminal-based Minecraft username generator and availability checker written in Python. It focuses on checking short usernames (3–4 characters) using Mojang’s official public API, with an interactive CLI and real-time output.

## Features

- Supports 3 and 4 character usernames  
- Custom character sets (letters, numbers, or both)  
- Optional underscore support  
- Multi-threaded checking with rate limiting  
- Automatic retries for temporary API errors  
- Avoids duplicate checks using a local cache  
- Colored terminal output with ASCII banner  
- Saves results to `checked.txt`

## How It Works

Usernames are randomly generated based on selected rules and checked using:
https://api.mojang.com/users/profiles/minecraft/<username>

Responses are interpreted as available, taken, or unknown (retried automatically).

## Requirements

- Python 3.8+
- requests (auto installed when running the script)

