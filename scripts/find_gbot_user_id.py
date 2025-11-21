"""Helper script to find G-bot's Slack user ID

This script uses the Slack API to search for G-bot and retrieve its user ID,
which is needed to properly mention the bot in messages.

Usage:
    poetry run python scripts/find_gbot_user_id.py
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")

if not SLACK_BOT_TOKEN:
    print("Error: SLACK_BOT_TOKEN not found in .env file")
    exit(1)

# List all users in the workspace
url = "https://slack.com/api/users.list"
headers = {
    "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
    "Content-Type": "application/json"
}

print("Searching for G-bot in Slack workspace...")
print()

try:
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()
    
    if not data.get("ok"):
        print(f"Error: {data.get('error', 'Unknown error')}")
        exit(1)
    
    # Search for G-bot
    members = data.get("members", [])
    gbot_candidates = []
    
    for member in members:
        name = member.get("name", "").lower()
        real_name = member.get("real_name", "").lower()
        display_name = member.get("profile", {}).get("display_name", "").lower()
        
        # Look for variations of "g-bot" or "gbot"
        if any(term in name or term in real_name or term in display_name 
               for term in ["g-bot", "gbot", "g bot"]):
            gbot_candidates.append({
                "id": member.get("id"),
                "name": member.get("name"),
                "real_name": member.get("real_name"),
                "display_name": member.get("profile", {}).get("display_name"),
                "is_bot": member.get("is_bot", False)
            })
    
    if not gbot_candidates:
        print("❌ G-bot not found in workspace")
        print()
        print("Showing all bots in workspace:")
        print()
        for member in members:
            if member.get("is_bot") and not member.get("deleted"):
                print(f"  - {member.get('name')} (ID: {member.get('id')})")
                print(f"    Real name: {member.get('real_name')}")
                print()
    else:
        print("✅ Found G-bot candidate(s):")
        print()
        for bot in gbot_candidates:
            print(f"  Name: {bot['name']}")
            print(f"  Real Name: {bot['real_name']}")
            print(f"  Display Name: {bot['display_name']}")
            print(f"  User ID: {bot['id']}")
            print(f"  Is Bot: {bot['is_bot']}")
            print()
            print(f"  To mention this bot, use: <@{bot['id']}>")
            print(f"  Update .env with: SLACK_WHITELIST_COMMAND_TEMPLATE=<@{bot['id']}> ip_whitelist {{ip}}")
            print()
            print("-" * 60)
            print()

except requests.RequestException as e:
    print(f"Error calling Slack API: {e}")
    exit(1)

