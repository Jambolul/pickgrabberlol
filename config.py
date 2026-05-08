import os
from dotenv import load_dotenv

load_dotenv()

RIOT_API_KEY = os.getenv("RIOT_API_KEY")

print("Loaded key repr:", repr(RIOT_API_KEY))

if not RIOT_API_KEY:
    raise ValueError("Missing RIOT_API_KEY in .env file")

HEADERS = {
    "X-Riot-Token": RIOT_API_KEY
}

REGION_ROUTING = "europe"