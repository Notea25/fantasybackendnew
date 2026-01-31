# Исправление логики создания сквадов

## Проблема

При создании нового сквада создавался SquadTour для **текущего** тура, если он существовал. Это приводило к проблемам:

1. **Текущий тур уже идет** - матчи могут быть начаты или завершены
2. **Штрафы записывались неправильно** - penalty_points должны фиксироваться для будущего тура
3. **Нелогичное поведение** - пользователь создает команду, которая уже "участвует" в текущем туре

### Старая логика (НЕПРАВИЛЬНАЯ):

```python
# Правило: если есть текущий тур (матчи идут сейчас) - используем его, иначе - следующий
active_tour = current_tour if current_tour else next_tour
```

**Проблемный сценарий:**
```
Текущий тур: Тур 5 (идет прямо сейчас)
Следующий тур: Тур 6 (еще не начался)

Пользователь создает сквад
  ↓
Создается SquadTour для Тура 5 ❌
  ↓
ПРОБЛЕМА: Тур 5 уже идет, создавать для него сквад поздно!
```

## Решение

При создании нового сквада **всегда** создается SquadTour для **следующего** тура.

### Новая логика (ПРАВИЛЬНАЯ):

```python
# Правило: новый сквад всегда создается для следующего тура
# (текущий тур уже идет, поэтому создавать для него нельзя)
active_tour = next_tour
```

**Правильный сценарий:**
```
Текущий тур: Тур 5 (идет прямо сейчас)
Следующий тур: Тур 6 (еще не начался)

Пользователь создает сквад
  ↓
Создается SquadTour для Тура 6 ✅
  ↓
ПРАВИЛЬНО: Сквад готов участвовать в Туре 6
```

## Изменения в коде

### Файл: `app/squads/services.py`

#### 1. Строки 54-62 (определение тура)

**Было:**
```python
# Определяем актуальный тур для сквада
previous_tour, current_tour, next_tour = await TourService.get_previous_current_next_tour(league_id)
logger.debug(f"Tours for league {league_id}: previous={previous_tour}, current={current_tour}, next={next_tour}")

# Правило: если есть текущий тур (матчи идут сейчас) - используем его, иначе - следующий
active_tour = current_tour if current_tour else next_tour
active_tour_id = active_tour.id if active_tour else None
logger.debug(f"Active tour for new squad: {active_tour_id}")
```

**Стало:**
```python
# Определяем следующий тур для сквада
previous_tour, current_tour, next_tour = await TourService.get_previous_current_next_tour(league_id)
logger.debug(f"Tours for league {league_id}: previous={previous_tour}, current={current_tour}, next={next_tour}")

# Правило: новый сквад всегда создается для следующего тура
# (текущий тур уже идет, поэтому создавать для него нельзя)
active_tour = next_tour
active_tour_id = active_tour.id if active_tour else None
logger.debug(f"Next tour for new squad: {active_tour_id}")
```

#### 2. Строки 187-207 (создание SquadTour)

**Было:**
```python
# Создаём SquadTour для актуального тура
if active_tour_id:
    # ...
    logger.info(f"Created SquadTour for squad {squad.id} and tour {active_tour_id}")
else:
    logger.warning(f"No active tour found for league {league_id}, SquadTour not created")
```

**Стало:**
```python
# Создаём SquadTour для следующего тура
if active_tour_id:
    # ...
    logger.info(f"Created SquadTour for squad {squad.id} and next tour {active_tour_id}")
else:
    logger.warning(f"No next tour found for league {league_id}, SquadTour not created")
```

## Влияние на другую логику

### ✅ Согласованность с другими методами

1. **`finalize_tour_for_all_squads`** - уже правильно создает SquadTour для **следующего** тура при завершении текущего
2. **`replace_players`** - работает с текущим составом и правильно записывает penalty_points
3. **`_save_current_squad`** - сохраняет snapshot для текущего тура сквада

### Штрафные очки (penalty_points)

Теперь логика штрафов работает правильно:

```
Пользователь создает сквад
  ↓
SquadTour создается для Тура 6
  ↓
penalty_points = 0 (начальное значение)
  ↓
Пользователь делает трансферы до дедлайна Тура 6
  ↓
Штрафы накапливаются в Squad.penalty_points
  ↓
При сохранении snapshot: SquadTour.penalty_points = Squad.penalty_points
  ↓
Тур 6 начинается со штрафами, зафиксированными в SquadTour
```

## Граничные случаи

### 1. Что если нет следующего тура?
```python
active_tour = next_tour  # может быть None
active_tour_id = active_tour.id if active_tour else None

if active_tour_id:
    # Создаем SquadTour
else:
    logger.warning(f"No next tour found for league {league_id}, SquadTour not created")
```
**Результат:** Сквад создается, но без SquadTour. Он будет создан позже, когда появится следующий тур.

### 2. Что если сезон еще не начался?
```
current_tour = None
next_tour = Тур 1

active_tour = next_tour  # Тур 1
```
**Результат:** ✅ Сквад создается для Тура 1 (правильно)

### 3. Что если сезон завершен?
```
current_tour = None
next_tour = None

active_tour = None
```
**Результат:** ⚠️ Сквад создается, но без SquadTour (нет будущих туров)

## Тестирование

### Сценарии для проверки:

1. ✅ **Создание сквада до начала сезона**
   - Ожидание: SquadTour для Тура 1

2. ✅ **Создание сквада во время Тура 5**
   - Ожидание: SquadTour для Тура 6 (не для Тура 5!)

3. ✅ **Создание сквада после дедлайна Тура 5, но до начала Тура 6**
   - Ожидание: SquadTour для Тура 6

4. ✅ **Штрафы записываются в правильный тур**
   - Создать сквад → Сделать трансферы с штрафами → Проверить penalty_points в SquadTour следующего тура

## Заключение

Это исправление делает логику создания сквадов:
- ✅ **Последовательной** - всегда создается для следующего тура
- ✅ **Логичной** - нельзя создать команду для уже идущего тура
- ✅ **Правильной** - штрафы фиксируются для корректного тура
- ✅ **Согласованной** - совпадает с логикой `finalize_tour_for_all_squads`
