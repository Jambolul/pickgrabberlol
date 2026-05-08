from collections import defaultdict
import time

from riot_api import get_account, get_match_ids, get_match_with_retry
from parser import extract_mid_matchup


def parse_riot_id(riot_id):
    if "#" not in riot_id:
        raise ValueError("Riot ID must be in the format Name#TAG")
    name, tag = riot_id.split("#", 1)
    return name, tag


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

    name, tag = parse_riot_id(riot_id)

    print("Getting account...")
    account = get_account(name, tag)
    puuid = account["puuid"]

    print("Getting match IDs...")
    match_ids = get_many_match_ids(puuid, total_count=200)
    print(f"Total match IDs fetched: {len(match_ids)}")

    results = []

    for index, match_id in enumerate(match_ids, start=1):
        try:
            match = get_match_with_retry(match_id)
            row = extract_mid_matchup(match, puuid)

            if row:
                results.append(row)

            if index % 10 == 0:
                print(f"Processed {index}/{len(match_ids)} matches...")

            time.sleep(1.25)

        except Exception as e:
            print(f"Error in match {match_id}: {e}")

    print("\nRanked solo queue midlane analysis:\n")

    if not results:
        print("No ranked solo queue midlane games found.")
        return

    print(f"Found {len(results)} ranked solo queue midlane games.\n")

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