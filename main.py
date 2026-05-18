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


def get_many_match_ids(puuid, total_count):
    all_match_ids = []
    start = 0

    while len(all_match_ids) < total_count:
        remaining = total_count - len(all_match_ids)
        batch_size = min(100, remaining)

        batch = get_match_ids(
            puuid,
            start=start,
            count=batch_size
        )

        if not batch:
            break

        all_match_ids.extend(batch)
        start += len(batch)

        print(f"Fetched {len(all_match_ids)} match IDs so far...")

        if len(batch) < batch_size:
            break

        # Small pause between ID requests
        time.sleep(1.2)

    return all_match_ids


def summarize_most_played(rows):
    champion_summary = defaultdict(
        lambda: {"games": 0, "wins": 0}
    )

    for row in rows:
        champion = row["player"]

        champion_summary[champion]["games"] += 1

        if row["win"]:
            champion_summary[champion]["wins"] += 1

    return champion_summary


def summarize_matchups(rows):
    matchup_summary = defaultdict(
        lambda: defaultdict(
            lambda: {"games": 0, "wins": 0}
        )
    )

    for row in rows:
        enemy = row["enemy"]
        player = row["player"]

        matchup_summary[enemy][player]["games"] += 1

        if row["win"]:
            matchup_summary[enemy][player]["wins"] += 1

    return matchup_summary


def main():
    print("=== League Ranked Solo Queue Analyzer ===\n")

    # Riot ID
    riot_id = input(
        "Enter Riot ID (example: Caps#EUW): "
    ).strip()

    # Role
    role_input = input(
        "Enter role (top, jungle, mid, bot, support): "
    ).strip()

    role = parse_role_input(role_input)

    if not role:
        print("Invalid role. Defaulting to MIDDLE.")
        role = "MIDDLE"

    # Match count
    count_input = input(
        "How many recent matches to scan? (example: 100, 200, 300): "
    ).strip()

    try:
        total_count = int(count_input)

        if total_count <= 0:
            raise ValueError

    except:
        print("Invalid number. Defaulting to 100.")
        total_count = 100

    # Patch filter
    patch_input = input(
        "Optional patch filter (example: 15.10). Leave empty for all patches: "
    ).strip()

    target_patch = patch_input if patch_input else None

    # Minimum matchup threshold
    threshold_input = input(
        "Minimum matchup sample size to display? (example: 2): "
    ).strip()

    try:
        minimum_games = int(threshold_input)

        if minimum_games <= 0:
            raise ValueError

    except:
        print("Invalid number. Defaulting to 2.")
        minimum_games = 2

    print("\n=== Settings ===")
    print(f"Role: {role}")
    print(f"Matches to scan: {total_count}")

    if target_patch:
        print(f"Patch filter: {target_patch}")
    else:
        print("Patch filter: ALL")

    print(f"Minimum matchup sample size: {minimum_games}")
    print()

    # Parse Riot ID
    name, tag = parse_riot_id(riot_id)

    print("Getting account...")
    account = get_account(name, tag)
    puuid = account["puuid"]

    print("Getting match IDs...")
    match_ids = get_many_match_ids(
        puuid,
        total_count=total_count
    )

    print(f"Total match IDs fetched: {len(match_ids)}\n")

    results = []

    # Process matches
    for index, match_id in enumerate(match_ids, start=1):
        try:
            match = get_match_with_retry(match_id)

            row = extract_role_matchup(
                match,
                puuid,
                role,
                target_patch=target_patch
            )

            if row:
                results.append(row)

            if index % 10 == 0:
                print(
                    f"Processed {index}/{len(match_ids)} matches..."
                )

            # Small pause between match detail requests
            time.sleep(1.25)

        except Exception as e:
            print(f"Error in match {match_id}: {e}")

    print("\n=== Analysis Results ===\n")

    if not results:
        print("No matching games found.")
        return

    print(
        f"Found {len(results)} ranked solo queue "
        f"{role.lower()} games.\n"
    )

    # MOST PLAYED CHAMPIONS
    print("=== Most Played Champions ===\n")

    most_played = summarize_most_played(results)

    sorted_champions = sorted(
        most_played.items(),
        key=lambda item: item[1]["games"],
        reverse=True
    )

    for champion, stats in sorted_champions:
        games = stats["games"]
        wins = stats["wins"]

        winrate = (
            (wins / games) * 100
            if games else 0
        )

        print(
            f"{champion} - "
            f"{games} games, "
            f"{wins} wins, "
            f"{winrate:.1f}% WR"
        )

    print()

    # MATCHUP SUMMARY
    print("=== Matchups By Enemy Champion ===\n")

    matchup_summary = summarize_matchups(results)

    for enemy, picks in sorted(matchup_summary.items()):

        filtered_picks = [
            (champion, stats)
            for champion, stats in picks.items()
            if stats["games"] >= minimum_games
        ]

        if not filtered_picks:
            continue

        print(f"Into {enemy}:")

        filtered_picks.sort(
            key=lambda item: item[1]["games"],
            reverse=True
        )

        for champion, stats in filtered_picks:
            games = stats["games"]
            wins = stats["wins"]

            winrate = (
                (wins / games) * 100
                if games else 0
            )

            print(
                f"  {champion} - "
                f"{games} games, "
                f"{wins} wins, "
                f"{winrate:.1f}% WR"
            )

        print()


if __name__ == "__main__":
    main()