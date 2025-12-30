import requests

API_KEY = "b3dfd15ec3cb3989715ceb4eef1417af"  # Замените на ваш ключ
HEADERS = {"x-apisports-key": API_KEY}

def get_player_season_stats(player_name: str, league_name: str, season: int, team_name: str):
    # Шаг 1: Получить ID лиги
    leagues_url = "https://v3.football.api-sports.io/leagues"
    params = {"name": league_name, "season": season}
    leagues_response = requests.get(leagues_url, headers=HEADERS, params=params)
    leagues_data = leagues_response.json()
    league_id = leagues_data["response"][0]["league"]["id"]

    # Шаг 2: Получить ID команды
    teams_url = "https://v3.football.api-sports.io/teams"
    params = {"name": team_name, "season": season, "league": league_id}
    teams_response = requests.get(teams_url, headers=HEADERS, params=params)
    teams_data = teams_response.json()
    team_id = teams_data["response"][0]["team"]["id"]

    # Шаг 3: Получить ID игрока
    players_url = "https://v3.football.api-sports.io/players"
    params = {"name": player_name, "team": team_id}
    players_response = requests.get(players_url, headers=HEADERS, params=params)
    players_data = players_response.json()
    player_id = players_data["response"][0]["player"]["id"]

    # Шаг 4: Получить статистику игрока за сезон
    stats_url = f"https://v3.football.api-sports.io/players/{player_id}/seasons/{season}"
    stats_response = requests.get(stats_url, headers=HEADERS)
    stats_data = stats_response.json()

    # Фильтруем статистику по лиге
    player_stats = []
    for stat in stats_data["response"]:
        if stat["league"]["id"] == league_id:
            for fixture in stat.get("fixtures", []):
                player_stats.append({
                    "match": f"{fixture['home']['name']} vs {fixture['away']['name']}",
                    "date": fixture["date"],
                    "goals": fixture["statistics"].get("goals", {}).get("total", 0),
                    "assists": fixture["statistics"].get("goals", {}).get("assists", 0),
                    "rating": fixture["statistics"].get("rating", {}).get("average", 0),
                })

    return player_stats

# Пример использования
ronaldo_stats = get_player_season_stats(
    player_name="Cristiano Ronaldo",
    league_name="Serie A",
    season=2021,
    team_name="Juventus"
)

for stat in ronaldo_stats:
    print(f"Матч: {stat['match']}, Дата: {stat['date']}, Голы: {stat['goals']}, Пасы: {stat['assists']}, Рейтинг: {stat['rating']}")
