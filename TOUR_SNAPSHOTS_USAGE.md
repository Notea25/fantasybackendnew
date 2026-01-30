# Инструкция по Использованию Системы Tour Snapshots

## Обзор

Система автоматически сохраняет исторические снимки (snapshots) состава команды пользователя для каждого тура. Это гарантирует, что при просмотре истории туров отображается именно тот состав, который был у пользователя в момент этого тура.

## Основные Компоненты

### 1. API Endpoints

#### Получение истории туров
```http
GET /squads/{squad_id}/history
```

**Возвращает:**
```json
[
  {
    "tour_id": 1,
    "tour_number": 1,
    "points": 50,
    "used_boost": null,
    "captain_id": 123,
    "vice_captain_id": 456,
    "main_players": [
      {
        "id": 1,
        "name": "Player Name",
        "position": "Forward",
        "team_id": 10,
        "team_name": "Team Name",
        "team_logo": "https://...",
        "market_value": 5000,
        "photo": "https://...",
        "total_points": 120,
        "tour_points": 8
      },
      // ... 10 more players
    ],
    "bench_players": [
      // ... 4 players
    ]
  },
  // ... more tours
]
```

#### Финализация тура (для администратора)
```http
POST /tours/finalize_tour/{tour_id}?next_tour_id={next_tour_id}
```

**Описание:**
Завершает текущий тур и создает snapshots для всех сквадов в следующем туре.

**Параметры:**
- `tour_id` - ID завершаемого тура
- `next_tour_id` - ID следующего тура (query parameter)

**Возвращает:**
```json
{
  "status": "success",
  "message": "Tour 1 finalized, created snapshots for tour 2",
  "finalized_tours": 100,
  "created_tours": 100,
  "total_squads_processed": 100
}
```

### 2. Автоматические Процессы

#### При создании сквада
Автоматически создается `SquadTour` для текущего/следующего тура с начальным составом.

#### При изменении состава
- `PUT /squads/update_players/{squad_id}` - обновление основного состава
- `POST /squads/{squad_id}/replace_players` - трансферы

Оба эндпоинта автоматически обновляют snapshot **только текущего тура**.

## Сценарии Использования

### Базовый Поток

1. **Пользователь создает сквад**
   ```
   POST /squads/create
   ```
   - Создается `Squad` с текущим составом
   - Создается `SquadTour` для текущего тура

2. **Тур завершается**
   ```
   POST /tours/finalize_tour/1?next_tour_id=2
   ```
   - Финализируются все `SquadTour` для тура 1
   - Создаются новые `SquadTour` для тура 2 с копией текущего состава
   - Обновляется `Squad.current_tour_id = 2`

3. **Пользователь делает трансферы**
   ```
   POST /squads/{squad_id}/replace_players
   ```
   - Обновляется состав в `Squad`
   - Обновляется snapshot в `SquadTour` для тура 2
   - Snapshot тура 1 **НЕ изменяется**

4. **Просмотр истории**
   ```
   GET /squads/{squad_id}/history
   ```
   - Возвращаются snapshots всех туров
   - Тур 1: старый состав до трансферов
   - Тур 2: новый состав после трансферов

### Автоматизация через Cron

Рекомендуется настроить автоматический вызов финализации туров через cron или планировщик задач.

**Пример (Python APScheduler):**

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.squads.services import SquadService
from app.tours.services import TourService

scheduler = AsyncIOScheduler()

@scheduler.scheduled_job('cron', hour=0, minute=0)  # Каждую полночь
async def auto_finalize_tours():
    # Получаем все лиги
    leagues = await LeagueService.find_all()
    
    for league in leagues:
        prev, current, next_tour = await TourService.get_previous_current_next_tour(league.id)
        
        # Проверяем, не завершился ли текущий тур
        if current and is_tour_finished(current):
            if next_tour:
                await SquadService.finalize_tour_for_all_squads(
                    tour_id=current.id,
                    next_tour_id=next_tour.id
                )
                print(f"Finalized tour {current.id} for league {league.id}")

scheduler.start()
```

## Тестирование

### Ручное тестирование

1. Создайте сквад через API
2. Запустите тестовый скрипт:
   ```bash
   python test_tour_snapshots.py
   ```
3. Измените `TEST_SQUAD_ID` на ID вашего сквада
4. Скрипт выведет детальную информацию о snapshots

### Проверка Базы Данных

```sql
-- Просмотр всех snapshots для сквада
SELECT 
    st.tour_id,
    t.number as tour_number,
    st.points,
    st.is_current,
    COUNT(DISTINCT stp.player_id) as main_players_count,
    COUNT(DISTINCT stbp.player_id) as bench_players_count
FROM squad_tours st
JOIN tours t ON t.id = st.tour_id
LEFT JOIN squad_tour_players stp ON stp.squad_tour_id = st.id
LEFT JOIN squad_tour_bench_players stbp ON stbp.squad_tour_id = st.id
WHERE st.squad_id = 1
GROUP BY st.id, t.number
ORDER BY t.number;

-- Проверка игроков в snapshots разных туров
SELECT 
    t.number as tour,
    p.name as player_name,
    p.position
FROM squad_tour_players stp
JOIN squad_tours st ON st.id = stp.squad_tour_id
JOIN tours t ON t.id = st.tour_id
JOIN players p ON p.id = stp.player_id
WHERE st.squad_id = 1
ORDER BY t.number, p.position, p.name;
```

## Проблемы и Решения

### Проблема: История не отображает состав
**Причина:** Старая версия API возвращала только базовую информацию  
**Решение:** Обновите бэкенд - теперь API возвращает полные данные

### Проблема: Прошлые туры изменяются при трансферах
**Причина:** Не создаются snapshots или обновляются не те туры  
**Решение:** Проверьте, что вызывается `_save_current_squad()` и он обновляет только `current_tour_id`

### Проблема: Дублирование snapshots
**Причина:** Метод `finalize_tour_for_all_squads` вызывается несколько раз  
**Решение:** Добавьте проверку на существование `SquadTour` перед созданием

## TODO

- [ ] Добавить проверку прав администратора в `/tours/finalize_tour`
- [ ] Реализовать автоматическую финализацию туров через cron
- [ ] Добавить логику восстановления бесплатных замен при смене тура
- [ ] Реализовать обработку edge cases (первый/последний тур сезона)
- [ ] Добавить эндпоинт для просмотра конкретного snapshot тура
- [ ] Добавить валидацию при финализации (например, все матчи завершены)

## Дополнительные Ресурсы

- `TOUR_SNAPSHOTS_LOGIC.md` - подробное описание логики
- `test_tour_snapshots.py` - тестовый скрипт
- Модели: `app/squads/models.py` (Squad, SquadTour)
- Сервисы: `app/squads/services.py` (SquadService)
