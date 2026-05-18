RANKED_SOLO_QUEUE_ID = 420


def get_position(participant):
    team_position = participant.get("teamPosition")
    if team_position:
        return team_position

    individual_position = participant.get("individualPosition")
    if individual_position and individual_position != "INVALID":
        return individual_position

    return None


def extract_role_matchup(match, puuid, target_role, target_patch=None):
    info = match.get("info", {})
    participants = info.get("participants", [])
    queue_id = info.get("queueId")

    # Ranked solo queue only
    if queue_id != RANKED_SOLO_QUEUE_ID:
        return None

    game_version = info.get("gameVersion", "")

    # Patch filter
    if target_patch:
        if not game_version.startswith(target_patch):
            return None

    player = next((p for p in participants if p.get("puuid") == puuid), None)
    if not player:
        return None

    player_position = get_position(player)

    if player_position != target_role:
        return None

    enemy_same_role = next(
        (
            p for p in participants
            if p.get("teamId") != player.get("teamId")
            and get_position(p) == target_role
        ),
        None
    )

    if not enemy_same_role:
        return None

    return {
        "player": player.get("championName"),
        "enemy": enemy_same_role.get("championName"),
        "win": player.get("win"),
        "patch": game_version,
    }