# Инвентаризация использования полей Squad

Этот документ содержит детальный анализ использования полей модели Squad, которые будут перенесены в SquadTour.

## Поля для переноса

### 1. `budget: int`
- **Текущее использование**: Хранит текущий бюджет команды
- **Где используется**:
  - `services.py:1110` - Обновление при replace_players
  - `services.py:1202` - Возврат в get_replacement_info
  - `models.py:72` - Определение в модели (default=100_000)
- **После рефакторинга**: Перейдет в `SquadTour.budget`

### 2. `replacements: int`
- **Текущее использование**: Количество оставшихся бесплатных замен
- **Где используется**:
  - `services.py:1130-1147` - Логика платных/бесплатных трансферов
  - `services.py:1202` - Возврат в get_replacement_info  
  - `router.py:134, 140` - Отображение в ответах API
  - `models.py:73` - Определение в модели (default=2)
- **После рефакторинга**: Перейдет в `SquadTour.replacements`

### 3. `points: int`
- **Текущее использование**: Очки команды за текущий тур
- **Где используется**:
  - `services.py:992-994` - Для текущего тура в лидерборде
  - `services.py:1131` - Логирование текущих очков
  - `services.py:1471-1473` - Для текущего тура в лидерборде по fav_team
  - `router.py:133, 146` - Отображение в ответах API
  - `models.py:74` - Определение в модели (default=0)
- **После рефакторинга**: Перейдет в `SquadTour.points`

### 4. `penalty_points: int`
- **Текущее использование**: Штрафные очки за текущий тур
- **Где используется**:
  - `services.py:777` - Синхронизация с SquadTour
  - `services.py:993-994` - Для текущего тура в лидерборде
  - `services.py:1293` - Применение штрафов из next_tour_penalty_points
  - `services.py:1472-1473` - Для текущего тура в лидерборде по fav_team
  - `models.py:75` - Определение в модели (default=0)
- **После рефакторинга**: Перейдет в `SquadTour.penalty_points`

### 5. `next_tour_penalty_points: int`
- **Текущее использование**: Накопление штрафов для следующего тура
- **Где используется**:
  - `services.py:1147` - Накопление штрафов при трансферах
  - `services.py:1293-1294` - Применение и сброс при переходе тура
  - `models.py:79` - Определение в модели (default=0)
- **После рефакторинга**: **УДАЛИТЬ** - штрафы будут напрямую применяться к SquadTour следующего тура

### 6. `captain_id: int | null`
- **Текущее использование**: ID капитана команды
- **Где используется**:
  - `services.py:741, 774, 807` - Обновление и синхронизация
  - `services.py:1108` - Обновление при replace_players
  - `services.py:1277` - Копирование в новый SquadTour
  - `models.py:76` - Определение в модели
- **После рефакторинга**: Перейдет в `SquadTour.captain_id` (уже есть)

### 7. `vice_captain_id: int | null`
- **Текущее использование**: ID вице-капитана команды
- **Где используется**:
  - `services.py:742, 775, 808` - Обновление и синхронизация
  - `services.py:1109` - Обновление при replace_players
  - `services.py:1278` - Копирование в новый SquadTour
  - `models.py:77` - Определение в модели
- **После рефакторинга**: Перейдет в `SquadTour.vice_captain_id` (уже есть)

### 8. `current_tour_id: int | null`
- **Текущее использование**: ID текущего тура для команды
- **Где используется**:
  - `services.py:375` - Логирование при загрузке
  - `services.py:760, 766, 783, 805, 821` - Работа с текущим туром
  - `services.py:1290` - Обновление при переходе тура
  - `models.py:80` - Определение в модели (закомментирован!)
- **После рефакторинга**: **УДАЛИТЬ** - логику определения тура перенести на расчет по датам

## Таблицы связи (m2m) для текущего состава

### 9. `squad_players_association`
- **Текущее использование**: Связь текущих основных игроков со Squad
- **Где используется**:
  - `services.py:379-383, 401-408, 787-792` - Загрузка текущего состава
  - `services.py:717-732, 1149-1164` - Обновление состава
  - `models.py:10-16` - Определение таблицы
- **После рефакторинга**: **УДАЛИТЬ** - состав хранится в SquadTour

### 10. `squad_bench_players_association`
- **Текущее использование**: Связь текущих скамеечных игроков со Squad
- **Где используется**:
  - `services.py:385-391, 433-440, 794-800` - Загрузка текущей скамейки
  - `services.py:722-739, 1154-1170` - Обновление скамейки
  - `models.py:18-24` - Определение таблицы
- **После рефакторинга**: **УДАЛИТЬ** - состав хранится в SquadTour

## Методы Squad для удаления

### 11. `Squad.calculate_players_cost()`
- **Текущее использование**: Рассчитывает стоимость всех игроков
- **Где используется**: `models.py:122-125`
- **После рефакторинга**: Перенести логику в SquadService или удалить

### 12. `Squad.calculate_points(session)`
- **Текущее использование**: Рассчитывает очки команды
- **Где используется**:
  - `services.py:773, 818` - Пересчет очков для SquadTour
  - `services.py:1255` - Пересчет финальных очков
  - `models.py:176-197` - Определение метода
- **После рефакторинга**: Перенести в SquadService, работать с SquadTour

### 13. `Squad.count_different_players()`
- **Текущее использование**: Подсчитывает количество замененных игроков
- **Где используется**: `models.py:167-174`
- **После рефакторинга**: Перенести логику в SquadService

## Relationships для удаления

### 14. `Squad.current_main_players`
- **Текущее использование**: Relationship к основным игрокам
- **Где используется**:
  - `services.py:1113` - Получение текущего состава для сравнения
  - `services.py:1230, 1279` - Копирование в SquadTour
  - `models.py:86-90` - Определение relationship
- **После рефакторинга**: **УДАЛИТЬ** - использовать SquadTour.main_players

### 15. `Squad.current_bench_players`
- **Текущее использование**: Relationship к скамеечным игрокам
- **Где используется**:
  - `services.py:1114` - Получение текущей скамейки для сравнения
  - `services.py:1231, 1280` - Копирование в SquadTour
  - `models.py:91-95` - Определение relationship
- **После рефакторинга**: **УДАЛИТЬ** - использовать SquadTour.bench_players

## Критические методы для рефакторинга

### `replace_players()` (services.py:1034-1186)
**Текущая логика:**
1. Получает squad и текущий состав
2. Рассчитывает количество изменений
3. Списывает бесплатные замены из `squad.replacements`
4. Накапливает штрафы в `squad.next_tour_penalty_points`
5. Обновляет `squad.budget`, `squad.captain_id`, `squad.vice_captain_id`
6. Обновляет m2m таблицы текущего состава
7. Вызывает `_save_current_squad()` для синхронизации с SquadTour

**Новая логика:**
1. Получить squad
2. Получить тур для трансферов (первый где deadline > now)
3. Получить/создать SquadTour для этого тура
4. Рассчитать количество изменений относительно SquadTour
5. Обновить `squad_tour.replacements` и `squad_tour.penalty_points` НАПРЯМУЮ
6. Обновить `squad_tour.budget`, `squad_tour.captain_id`, `squad_tour.vice_captain_id`
7. Обновить `squad_tour.main_players`, `squad_tour.bench_players`
8. Убрать всю логику синхронизации

### `finalize_tour_for_all_squads()` (services.py:1207-1315)
**Текущая логика:**
1. Находит все Squad с `current_tour_id == tour_id`
2. Финализирует SquadTour (is_current = False)
3. Создает новый SquadTour для следующего тура
4. Обновляет `squad.current_tour_id = next_tour_id`
5. Применяет `squad.penalty_points = squad.next_tour_penalty_points`
6. Сбрасывает `squad.next_tour_penalty_points = 0`

**Новая логика:**
1. Найти все SquadTour для завершенного тура
2. Пометить `is_finalized = True`
3. **НЕ создавать** новые SquadTour (они создаются при start_tour)
4. Пересчитать финальные очки

### `_save_current_squad()` (services.py:751-821)
**Текущая логика:**
- Синхронизирует состояние Squad → SquadTour
- Копирует points, captain_id, vice_captain_id, penalty_points

**После рефакторинга:**
- **УДАЛИТЬ** - синхронизация больше не нужна

### `get_leaderboard()` (services.py:929-1029)
**Текущая логика:**
- Для текущего тура использует `squad.points` и `squad.penalty_points`
- Для исторических туров использует SquadTour

**Новая логика:**
- Для ВСЕХ туров использовать только SquadTour
- Упростить запросы - убрать разделение на current/historical

## План миграции данных

### Этап 1: Добавить поля в SquadTour
```sql
ALTER TABLE squad_tours 
ADD COLUMN budget INTEGER NOT NULL DEFAULT 100000,
ADD COLUMN replacements INTEGER NOT NULL DEFAULT 2,
ADD COLUMN is_finalized BOOLEAN NOT NULL DEFAULT FALSE,
ADD COLUMN created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
```

### Этап 2: Мигрировать существующие данные
```sql
-- Копируем текущие значения из Squad в соответствующие SquadTour
UPDATE squad_tours st
SET 
    budget = s.budget,
    replacements = s.replacements
FROM squads s
WHERE st.squad_id = s.id;
```

### Этап 3: Удалить поля из Squad (после тестирования)
```sql
-- Удаляем m2m таблицы
DROP TABLE IF EXISTS squad_players_association;
DROP TABLE IF EXISTS squad_bench_players_association;

-- Удаляем колонки
ALTER TABLE squads
DROP COLUMN budget,
DROP COLUMN replacements,
DROP COLUMN points,
DROP COLUMN penalty_points,
DROP COLUMN captain_id,
DROP COLUMN vice_captain_id,
DROP COLUMN next_tour_penalty_points;
```

## Новые методы для добавления

### `SquadService.get_current_playing_tour(league_id)`
Получить текущий игровой тур (start_date <= now <= end_date).
Если между турами - вернуть последний завершенный.

### `SquadService.get_tour_for_transfers(league_id)`
Получить тур для трансферов (первый где deadline > now).
Совпадает с текущим игровым туром.

### `SquadService.get_or_create_squad_tour(squad_id, tour_id, copy_from_tour_id)`
Получить или создать SquadTour.
Если создаем - копировать состав из copy_from_tour_id.

### `SquadService.start_tour(tour_id)`
Вызывается когда tour.start_date наступил.
Создает SquadTour для СЛЕДУЮЩЕГО тура для всех команд.

## Оценка воздействия

### Высокое воздействие:
- `replace_players()` - полная переработка логики
- `finalize_tour_for_all_squads()` - изменение логики финализации
- `get_leaderboard()` - упрощение запросов
- Все router endpoints использующие Squad поля

### Среднее воздействие:
- `create_squad()` - минимальные изменения
- `update_squad_players()` - обновление для работы с SquadTour
- `get_replacement_info()` - изменение источника данных

### Низкое воздействие:
- `rename_squad()` - без изменений
- `get_squad_tour_history_with_players()` - добавить budget/replacements в вывод

## Следующие шаги

1. ✅ Провести аудит использования полей
2. ⏳ Создать миграцию БД (добавить поля в SquadTour)
3. ⏳ Обновить модели
4. ⏳ Рефакторить сервисы
5. ⏳ Обновить роутеры
6. ⏳ Тестирование
7. ⏳ Создать миграцию для удаления полей из Squad
