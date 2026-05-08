import time
import requests
from config import HEADERS, REGION_ROUTING

BASE_URL = f"https://{REGION_ROUTING}.api.riotgames.com"


def get_account(game_name, tag_line):
    url = f"{BASE_URL}/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}"
    r = requests.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    return r.json()


def get_match_ids(puuid, start=0, count=100):
    url = f"{BASE_URL}/lol/match/v5/matches/by-puuid/{puuid}/ids"
    params = {"start": start, "count": count}
    r = requests.get(url, headers=HEADERS, params=params, timeout=20)
    r.raise_for_status()
    return r.json()


def get_match_with_retry(match_id, max_retries=5):
    url = f"{BASE_URL}/lol/match/v5/matches/{match_id}"

    for attempt in range(1, max_retries + 1):
        r = requests.get(url, headers=HEADERS, timeout=20)

        if r.status_code == 429:
            retry_after = r.headers.get("Retry-After")
            wait_seconds = int(retry_after) if retry_after and retry_after.isdigit() else 5
            print(f"Rate limited on {match_id}. Waiting {wait_seconds}s before retrying...")
            time.sleep(wait_seconds)
            continue

        r.raise_for_status()
        return r.json()

    raise Exception(f"Failed to fetch {match_id} after {max_retries} retries")