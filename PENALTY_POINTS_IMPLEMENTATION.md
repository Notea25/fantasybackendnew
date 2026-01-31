# Реализация штрафных очков (Penalty Points)

## Обзор
Добавлена система штрафных очков для сквадов. Штрафы начисляются при превышении лимита бесплатных трансферов (replacements).

## Логика начисления штрафов

### Правило:
- Каждый сквад имеет лимит бесплатных трансферов (по умолчанию 3)
- При превышении лимита каждый дополнительный трансфер стоит **4 штрафных очка**
- Штрафы накапливаются отдельно от заработанных очков

### Пример:
```
Бесплатных трансферов: 2
Сделано трансферов: 5

Бесплатных использовано: 2
Платных трансферов: 3
Штраф: 3 × 4 = 12 очков
```

## Изменения в базе данных

### Миграция
- **Файл:** `alembic/versions/a3f7b8c9d1e2_add_penalty_points_to_squads_and_squad_tours.py`
- **Добавлено:**
  - `squads.penalty_points` (int, default=0)
  - `squad_tours.penalty_points` (int, default=0)

### Модели

#### Squad
```python
penalty_points: Mapped[int] = mapped_column(default=0)
```
- Хранит накопленные штрафы за все время

#### SquadTour
```python
penalty_points: Mapped[int] = mapped_column(default=0)
```
- Хранит штрафы на момент конкретного тура (snapshot)

## Изменения в API

### Схемы ответов
Все следующие схемы теперь включают поле `penalty_points`:
- `SquadReadSchema`
- `SquadTourHistorySchema`
- `PublicLeaderboardEntrySchema`
- `PublicClubLeaderboardEntrySchema`

### Эндпоинты
Все эндпоинты получения сквадов автоматически возвращают `penalty_points`:
- `GET /squads/my_squads`
- `GET /squads/get_squad_{squad_id}`
- `GET /squads/get_squad_by_id/{squad_id}`
- `GET /squads/{squad_id}/history`
- `GET /squads/leaderboard/{tour_id}`
- `GET /squads/leaderboard/{tour_id}/by-fav-team/{fav_team_id}`

### Лидерборд
Лидерборды теперь сортируются по **чистым очкам** (net points):
```
net_points = total_points - penalty_points
```

## Логика работы

### При создании сквада
```python
squad.penalty_points = 0
squad_tour.penalty_points = 0
```

### При замене игроков (replace_players)
1. Подсчитывается количество трансферов
2. Если трансферов больше чем `squad.replacements`:
   - Бесплатные: `min(transfers, squad.replacements)`
   - Платные: `transfers - squad.replacements`
   - Штраф: `paid_transfers × 4`
3. Штраф добавляется к `squad.penalty_points`
4. При сохранении snapshot: `squad_tour.penalty_points = squad.penalty_points`

### При финализации тура
При переходе на следующий тур:
- Текущий `SquadTour` сохраняет свои `penalty_points` (исторические данные)
- Новый `SquadTour` создается с `penalty_points = 0`
- `Squad.penalty_points` продолжает накапливаться

## Отображение на фронтенде

Рекомендуется показывать пользователю:
```
Заработано очков:     1250
Штрафные очки:        -12
────────────────────────
Итого:               1238
```

## Примечания

### Отличие от старой реализации
- **Старая:** Штрафы вычитались напрямую из `Squad.points`
- **Новая:** Штрафы хранятся отдельно в `Squad.penalty_points`

### Преимущества нового подхода
✅ Прозрачность - видны отдельно заработанные очки и штрафы
✅ Исторические данные - штрафы каждого тура сохраняются
✅ Гибкость - легко показать детализацию на фронтенде
✅ Аналитика - проще анализировать влияние трансферов

## Миграция существующих данных
При запуске миграции все существующие сквады получат `penalty_points = 0`.
Если нужно восстановить исторические штрафы, необходимо:
1. Проанализировать логи трансферов
2. Пересчитать штрафы
3. Обновить значения в базе
