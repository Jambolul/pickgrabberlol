RANKED_SOLO_QUEUE_ID = 420


def get_position(participant):
    team_position = participant.get("teamPosition")
    if team_position:
        return team_position

    individual_position = participant.get("individualPosition")
    if individual_position and individual_position != "INVALID":
        return individual_position

    return None


def extract_mid_matchup(match, puuid):
    info = match.get("info", {})
    participants = info.get("participants", [])
    queue_id = info.get("queueId")

    if queue_id != RANKED_SOLO_QUEUE_ID:
        return None

    player = next((p for p in participants if p.get("puuid") == puuid), None)
    if not player:
        return None

    player_position = get_position(player)
    if player_position != "MIDDLE":
        return None

    enemy_mid = next(
        (
            p for p in participants
            if p.get("teamId") != player.get("teamId")
            and get_position(p) == "MIDDLE"
        ),
        None
    )

    if not enemy_mid:
        return None

    return {
        "match_id": match.get("metadata", {}).get("matchId"),
        "queue_id": queue_id,
        "patch": info.get("gameVersion"),
        "player": player.get("championName"),
        "enemy": enemy_mid.get("championName"),
        "win": player.get("win"),
    }