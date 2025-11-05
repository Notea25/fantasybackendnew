def calculate_points(statistics: dict) -> int:
    points = 0

    minutes_played = statistics.get("games", {}).get("minutes", 0) or 0
    points += minutes_played // 60

    goals_total = statistics.get("goals", {}).get("total", 0) or 0
    points += goals_total * 5

    assists = statistics.get("goals", {}).get("assists", 0) or 0
    points += assists * 3

    if statistics.get("games", {}).get("position") == "Goalkeeper":
        goals_conceded = statistics.get("goals", {}).get("conceded", 0) or 0
        if goals_conceded == 0 and minutes_played >= 60:
            points += 5

    yellow_cards = statistics.get("cards", {}).get("yellow", 0) or 0
    points -= yellow_cards * 1

    yellow_red_cards = statistics.get("cards", {}).get("yellowred", 0) or 0
    points -= yellow_red_cards * 2

    red_cards = statistics.get("cards", {}).get("red", 0) or 0
    points -= red_cards * 3

    penalty_missed = statistics.get("penalty", {}).get("missed", 0) or 0
    points -= penalty_missed * 2

    return points if points > 0 else 0
