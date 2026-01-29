# Итоговая сводка: Добавление очков игроков в API

## Цель
Добавить возможность отображения двух типов очков для игроков:
1. **total_points** - общие очки за все туры
2. **tour_points** - очки за последний/текущий тур

## Выполненные изменения

### Бэкенд (Python/FastAPI)

#### 1. Эндпоинт `/api/squads/get_squad_{squad_id}`

**Файл: `app/squads/schemas.py`**
- Добавлены поля `total_points` и `tour_points` в `PlayerInSquadSchema`

**Файл: `app/squads/services.py`**
- Добавлен метод `_get_player_total_points()` - расчет общих очков игрока
- Добавлен метод `_get_player_tour_points()` - расчет очков за конкретный тур
- Добавлен метод `_get_current_or_last_tour_id()` - определение текущего/последнего тура
- Обновлены методы:
  - `find_one_or_none_with_relations()`
  - `find_all_with_relations()`
  - `find_filtered_with_relations()`

**Логика определения тура для `tour_points`:**
1. Если идет текущий тур → возвращаем его ID
2. Если текущего нет, но дедлайн следующего прошел → возвращаем следующий
3. Иначе → возвращаем последний завершенный тур

#### 2. Эндпоинт `/api/players/league/{league_id}/players_with_points`

**Статус:** ✅ Уже работает корректно

**Файл: `app/players/services.py`**
- Метод `find_all_with_total_points()` уже возвращает `total_points`
- Возвращается как поле `points` в `PlayerWithTotalPointsSchema`

**Что возвращает:**
```json
{
  "id": 1,
  "name": "Player Name",
  "team_id": 5,
  "team_name": "Team Name",
  "team_logo": "https://...",
  "position": "Midfielder",
  "market_value": 8000,
  "points": 120  // Это уже total_points!
}
```

### Фронтенд (React/TypeScript)

#### 1. Обновлены типы данных

**Файл: `src/lib/api.ts`**
```typescript
// Для игроков в составе команды
export interface SquadPlayer {
  // ... другие поля
  points: number;        // Обратная совместимость
  total_points: number;  // Общие очки
  tour_points: number;   // Очки за тур
}

// Для списка игроков лиги
export interface Player {
  // ... другие поля
  points: number; // УЖЕ содержит total_points с бэкенда!
}
```

#### 2. Обновлен компонент PlayerCard

**Файл: `src/components/PlayerCard.tsx`**

Добавлен проп `showTourPoints`:
```typescript
interface PlayerCardProps {
  // ... существующие пропсы
  showTourPoints?: boolean; // true = tour_points, false = total_points
}
```

Логика выбора очков:
```typescript
const displayPoints = showTourPoints 
  ? (player.tour_points ?? 0) 
  : (player.total_points ?? player.points ?? 0);
```

#### 3. Обновлены хуки

**Файл: `src/hooks/useSquadById.ts`**
```typescript
export interface EnrichedPlayer {
  // ... другие поля
  points: number;         // Обратная совместимость
  total_points?: number;  // Общие очки
  tour_points?: number;   // Очки за тур
}
```

#### 4. Обновлены страницы

**ViewTeam (`src/pages/ViewTeam.tsx`)** ✅ Готово
```typescript
<PlayerCard
  showTourPoints={true}  // Показываем очки за тур
  player={{
    total_points: player.total_points,
    tour_points: player.tour_points,
  }}
/>
```

**Остальные страницы:**
- TeamManagement - используют `showTourPoints={false}` (по умолчанию)
- TeamBuilder - используют `showTourPoints={false}` (по умолчанию)
- Transfers - используют `showTourPoints={false}` (по умолчанию)

## Как это работает

### Для страниц с total_points
Страницы: создание команды, трансферы, моя команда

**Источник данных:**
- `/api/players/league/{league_id}/players_with_points` - поле `points` уже содержит total_points
- `/api/squads/get_squad_{squad_id}` - поле `total_points` в каждом игроке

**На фронте:**
```typescript
// Для списка игроков лиги
player.points // УЖЕ total_points

// Для состава команды
<PlayerCard 
  showTourPoints={false} // или не указывать
  player={{ total_points: player.total_points }}
/>
```

### Для страниц с tour_points
Страницы: просмотр команды (/view-team), результаты

**Источник данных:**
- `/api/squads/get_squad_{squad_id}` - поле `tour_points` в каждом игроке

**На фронте:**
```typescript
<PlayerCard 
  showTourPoints={true}
  player={{ tour_points: player.tour_points }}
/>
```

## Обратная совместимость

✅ Все старые поля `points` сохранены
✅ Если новые поля отсутствуют, используется fallback на `points`
✅ Существующий код работает без изменений

## Тестирование

### Бэкенд
```bash
cd C:\Users\val2\projects\sporttg
poetry run uvicorn app.main:app --reload
```

Проверить эндпоинты:
1. `GET /api/squads/get_squad_{squad_id}` - должны быть `total_points` и `tour_points`
2. `GET /api/players/league/116/players_with_points` - поле `points` содержит total_points

### Фронтенд
```bash
cd C:\Users\val2\projects\tele-mini-sparkle
npm run dev
```

Проверить:
1. ViewTeam - очки за тур (tour_points)
2. Создание команды / Трансферы - общие очки (total_points)

## Edge Cases

1. **Нет туров** → `tour_points = 0`
2. **Игрок не играл** → `total_points = 0`, `tour_points = 0`
3. **Игрок играл раньше, но не в текущем туре** → `total_points > 0`, `tour_points = 0`

## Документация

Созданы файлы:
- `C:\Users\val2\projects\sporttg\PLAYER_POINTS_UPDATE.md` - документация бэкенда
- `C:\Users\val2\projects\tele-mini-sparkle\PLAYER_POINTS_FRONTEND_CHANGES.md` - документация фронтенда
- `C:\Users\val2\projects\sporttg\SUMMARY_PLAYER_POINTS.md` - эта сводка

## Что готово

✅ Бэкенд возвращает `total_points` и `tour_points` для `/api/squads/get_squad`
✅ Бэкенд возвращает `total_points` (как `points`) для `/api/players/league/{id}/players_with_points`
✅ Фронтенд: обновлены типы данных
✅ Фронтенд: PlayerCard умеет показывать нужный тип очков
✅ Фронтенд: ViewTeam показывает очки за тур
✅ Фронтенд: Страницы с Player.points показывают total_points (уже работало)
✅ Документация создана

## Итог

Все изменения выполнены и готовы к использованию. API корректно возвращает оба типа очков, фронтенд правильно их отображает в зависимости от контекста.
