from collections import defaultdict
import time

from riot_api import get_account, get_match_ids, get_match_with_retry
from parser import extract_role_matchup


def parse_riot_id(riot_id):
    if "#" not in riot_id:
        raise ValueError("Riot ID must be in the format Name#TAG")
    name, tag = riot_id.split("#", 1)
    return name, tag


def parse_role_input(role_input):
    role_map = {
        "top": "TOP",
        "jungle": "JUNGLE",
        "jg": "JUNGLE",
        "mid": "MIDDLE",
        "middle": "MIDDLE",
        "bot": "BOTTOM",
        "bottom": "BOTTOM",
        "adc": "BOTTOM",
        "support": "UTILITY",
        "sup": "UTILITY",
        "utility": "UTILITY",
    }

    normalized = role_input.strip().lower()
    return role_map.get(normalized)


def get_many_match_ids(puuid, total_count=200):
    all_match_ids = []
    start = 0

    while len(all_match_ids) < total_count:
        remaining = total_count - len(all_match_ids)
        batch_size = min(100, remaining)

        batch = get_match_ids(puuid, start=start, count=batch_size)

        if not batch:
            break

        all_match_ids.extend(batch)
        start += len(batch)

        print(f"Fetched {len(all_match_ids)} match IDs so far...")

        if len(batch) < batch_size:
            break

        time.sleep(1.2)

    return all_match_ids


def summarize_most_played(rows):
    champion_summary = defaultdict(lambda: {"games": 0, "wins": 0})

    for row in rows:
        champion = row["player"]
        champion_summary[champion]["games"] += 1
        if row["win"]:
            champion_summary[champion]["wins"] += 1

    return champion_summary


def summarize_matchups(rows):
    matchup_summary = defaultdict(lambda: defaultdict(lambda: {"games": 0, "wins": 0}))

    for row in rows:
        enemy = row["enemy"]
        player = row["player"]
        matchup_summary[enemy][player]["games"] += 1
        if row["win"]:
            matchup_summary[enemy][player]["wins"] += 1

    return matchup_summary


def main():
    riot_id = input("Enter Riot ID (example: Caps#EUW): ").strip()
    role_input = input("Enter role (top, jungle, mid, bot, support): ").strip()
    count_input = input("How many recent matches to scan? (e.g. 50, 100, 200): ").strip()

    try:
        total_count = int(count_input)
        if total_count <= 0:
            raise ValueError
    except:
        print("Invalid number. Defaulting to 100.")
        total_count = 100

    name, tag = parse_riot_id(riot_id)
    role = parse_role_input(role_input)

    if not role:
        print("Invalid role. Defaulting to MIDDLE.")
        role = "MIDDLE"

    print(f"Selected role: {role}")

    print("Getting account...")
    account = get_account(name, tag)
    puuid = account["puuid"]

    print("Getting match IDs...")
    match_ids = get_many_match_ids(puuid, total_count=total_count)
    print(f"Total match IDs fetched: {len(match_ids)}")

    results = []

    for index, match_id in enumerate(match_ids, start=1):
        try:
            match = get_match_with_retry(match_id)
            row = extract_role_matchup(match, puuid, role)

            if row:
                results.append(row)

            if index % 10 == 0:
                print(f"Processed {index}/{len(match_ids)} matches...")

            time.sleep(1.25)

        except Exception as e:
            print(f"Error in match {match_id}: {e}")

    print(f"\nRanked solo queue {role.lower()} analysis:\n")

    if not results:
        print(f"No ranked solo queue games found for role {role}.")
        return

    print(f"Found {len(results)} ranked solo queue games for role {role}.\n")

    most_played = summarize_most_played(results)
    sorted_champions = sorted(
        most_played.items(),
        key=lambda item: item[1]["games"],
        reverse=True
    )

    print("Most played champions:\n")
    for champion, stats in sorted_champions:
        games = stats["games"]
        wins = stats["wins"]
        winrate = (wins / games) * 100 if games else 0
        print(f"{champion} - {games} games, {wins} wins, {winrate:.1f}% win rate")

    print()

    matchup_summary = summarize_matchups(results)

    print("Matchups by enemy champion (only picks with at least 2 games):\n")
    for enemy, picks in sorted(matchup_summary.items()):
        filtered_picks = [
            (champion, stats)
            for champion, stats in picks.items()
            if stats["games"] >= 2
        ]

        if not filtered_picks:
            continue

        print(f"Into {enemy}:")
        filtered_picks.sort(key=lambda item: item[1]["games"], reverse=True)

        for champion, stats in filtered_picks:
            games = stats["games"]
            wins = stats["wins"]
            winrate = (wins / games) * 100 if games else 0
            print(f"  {champion} - {games} games, {wins} wins, {winrate:.1f}% win rate")

        print()


if __name__ == "__main__":
    main()