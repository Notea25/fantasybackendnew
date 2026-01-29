# Добавление очков игроков в API `/api/squads/get_squad`

## Описание изменений

Добавлена возможность отображения очков игроков в ответе API `GET /api/squads/get_squad_{squad_id}` и связанных эндпоинтов.

## Что было сделано

### 1. Обновлена схема `PlayerInSquadSchema` (app/squads/schemas.py)

Добавлены два новых поля:
- `total_points: int = 0` - общее количество очков игрока за все туры (сумма очков из всех матчей)
- `tour_points: int = 0` - очки игрока за последний/текущий тур

### 2. Добавлены вспомогательные методы в `SquadService` (app/squads/services.py)

#### `_get_player_total_points(session, player_id: int) -> int`
Рассчитывает общее количество очков игрока за все матчи из таблицы `player_match_stats`.

#### `_get_player_tour_points(session, player_id: int, tour_id: int) -> int`
Рассчитывает очки игрока за конкретный тур:
1. Получает все матчи тура через `tour_matches_association`
2. Суммирует очки игрока из этих матчей

#### `_get_current_or_last_tour_id(session, league_id: int) -> Optional[int]`
Определяет ID текущего или последнего тура по логике:
1. Если идет текущий тур (матчи идут сейчас) - возвращаем его
2. Если текущего тура нет, но дедлайн следующего тура прошел - возвращаем следующий
3. Иначе возвращаем последний завершенный тур
4. Если туров нет - возвращаем `None`

### 3. Обновлены методы для возврата данных со статистикой

Следующие методы теперь включают расчет и возврат очков для каждого игрока:

- `find_one_or_none_with_relations(**filter_by)`
- `find_all_with_relations()`
- `find_filtered_with_relations(**filter_by)`

Для каждого игрока (как основного состава, так и скамейки) теперь рассчитываются:
- Общее количество очков (`total_points`)
- Очки за текущий/последний тур (`tour_points`)

### 4. Добавлен импорт `timedelta`

Импортирован `timedelta` для расчета дедлайна туров.

## Логика отображения очков на фронтенде

### Страницы с `total_points` (общие очки за все туры):
- Страница создания команды
- Страница трансферов
- Страница "Моя команда"

На этих страницах должно отображаться поле `total_points` из ответа API.

### Страницы с `tour_points` (очки за последний/текущий тур):
- Страница "Средний результат"
- Страница "Мои очки"
- Страница "Лучший результат" (`/view-team`)

На этих страницах должно отображаться поле `tour_points` из ответа API.

## Пример ответа API

```json
{
  "id": 1,
  "name": "My Squad",
  "user_id": 123,
  "username": "user123",
  "league_id": 1,
  "fav_team_id": 5,
  "budget": 50000,
  "replacements": 3,
  "points": 100,
  "captain_id": 10,
  "vice_captain_id": 11,
  "main_players": [
    {
      "id": 1,
      "name": "Player One",
      "position": "Forward",
      "team_id": 5,
      "team_name": "Team A",
      "team_logo": "https://example.com/logo.png",
      "market_value": 8000,
      "photo": "https://example.com/photo.jpg",
      "total_points": 45,
      "tour_points": 8
    }
    // ... остальные игроки
  ],
  "bench_players": [
    {
      "id": 12,
      "name": "Player Twelve",
      "position": "Goalkeeper",
      "team_id": 3,
      "team_name": "Team B",
      "team_logo": "https://example.com/logo2.png",
      "market_value": 5000,
      "photo": "https://example.com/photo2.jpg",
      "total_points": 20,
      "tour_points": 0
    }
    // ... остальные игроки скамейки
  ]
}
```

## Тестирование

### 1. Запустить бэкенд
```powershell
cd C:\Users\val2\projects\sporttg
poetry run uvicorn app.main:app --reload
```

### 2. Проверить API
Откройте http://127.0.0.1:8000/docs и протестируйте эндпоинт:
- `GET /squads/get_squad_{squad_id}`

### 3. Проверить ответ
Убедитесь, что в ответе для каждого игрока есть поля:
- `total_points` - общие очки
- `tour_points` - очки за тур

Если очки не найдены, они должны отображаться как 0.

## Обработка edge cases

1. **Если у лиги нет туров** - `tour_points` будет 0 для всех игроков
2. **Если игрок не играл ни в одном матче** - `total_points` и `tour_points` будут 0
3. **Если игрок играл в прошлых турах, но не в текущем** - `total_points` > 0, но `tour_points` = 0

## Производительность

Для каждого игрока выполняется 2 дополнительных запроса к БД:
1. Получение общих очков (SELECT SUM)
2. Получение очков за тур (SELECT SUM с JOIN)

Для оптимизации в будущем можно:
- Добавить кеширование
- Использовать batch-запросы для получения очков всех игроков одновременно
- Добавить индексы на `player_id` и `match_id` в таблице `player_match_stats`
