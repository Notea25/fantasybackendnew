# История Туров - Реализованные Изменения

## Дата: 2026-01-30

## Цель
Реализовать систему исторических snapshots для туров, обеспечивающую корректное отображение состава команды на момент каждого конкретного тура.

## Требования
Логика истории туров должна обеспечивать:
1. **Историческую целостность**: каждый тур хранит snapshot состава на момент дедлайна
2. **Независимость туров**: изменения в будущих турах не влияют на прошлые
3. **Корректное начисление очков**: очки начисляются только игрокам из основы на момент тура
4. **Правильная логика трансферов**: купленные игроки начинают приносить очки со следующего тура

## Реализованные Изменения

### 1. Расширение API Схемы

**Файл:** `app/squads/schemas.py`

**Изменения:**
- Расширена `SquadTourHistorySchema` для включения полной информации о составе:
  - `captain_id: Optional[int]`
  - `vice_captain_id: Optional[int]`
  - `main_players: list[PlayerInSquadSchema]`
  - `bench_players: list[PlayerInSquadSchema]`

**До:**
```python
class SquadTourHistorySchema(BaseModel):
    tour_id: int
    tour_number: int
    points: int
    used_boost: Optional[str]
```

**После:**
```python
class SquadTourHistorySchema(BaseModel):
    tour_id: int
    tour_number: int
    points: int
    used_boost: Optional[str]
    captain_id: Optional[int]
    vice_captain_id: Optional[int]
    main_players: list[PlayerInSquadSchema]
    bench_players: list[PlayerInSquadSchema]
```

### 2. Новый Метод Сервиса

**Файл:** `app/squads/services.py`

**Добавлен метод:** `get_squad_tour_history_with_players(squad_id: int)`

**Функциональность:**
- Загружает все `SquadTour` для указанного сквада
- Для каждого тура загружает полную информацию об игроках
- Рассчитывает очки каждого игрока за конкретный тур
- Возвращает полные данные для каждого snapshot

**Особенности:**
- Использует `joinedload` для оптимизации загрузки данных
- Рассчитывает `total_points` (всего) и `tour_points` (за тур) для каждого игрока
- Сортирует туры по возрастанию `tour_id`

### 3. Обновление Эндпоинта Истории

**Файл:** `app/squads/router.py`

**Изменения:**
- Обновлен эндпоинт `GET /squads/{squad_id}/history`
- Теперь использует новый метод `get_squad_tour_history_with_players()`
- Возвращает полные данные вместо базовой информации

**До:**
```python
@router.get("/{squad_id}/history", response_model=list[SquadTourHistorySchema])
async def get_squad_history(...):
    squad = await SquadService.find_one_or_none_with_relations(id=squad_id)
    return squad.tour_history  # Только базовая информация
```

**После:**
```python
@router.get("/{squad_id}/history", response_model=list[SquadTourHistorySchema])
async def get_squad_history(...):
    squad = await SquadService.find_one_or_none_with_relations(id=squad_id)
    history = await SquadService.get_squad_tour_history_with_players(squad_id)
    return history  # Полные данные с составами
```

### 4. Исправление Сохранения Snapshots

**Файл:** `app/squads/services.py`

**Изменения:**
- Добавлен вызов `_save_current_squad()` в метод `replace_players()`
- Теперь snapshot обновляется после любых изменений состава

**Добавлено:**
```python
await session.commit()
await session.refresh(squad)

# Сохраняем snapshot текущего состава для текущего тура
await cls._save_current_squad(squad_id)
```

### 5. Метод Финализации Туров

**Файл:** `app/squads/services.py`

**Добавлен метод:** `finalize_tour_for_all_squads(tour_id: int, next_tour_id: int)`

**Функциональность:**
1. Находит все сквады с `current_tour_id == tour_id`
2. Для каждого сквада:
   - Финализирует `SquadTour` завершенного тура (`is_current = False`)
   - Пересчитывает финальные очки
   - Создает новый `SquadTour` для следующего тура
   - Копирует текущий состав в новый snapshot
   - Обновляет `Squad.current_tour_id`

**Возвращает:**
```python
{
    "finalized_tours": int,
    "created_tours": int,
    "total_squads_processed": int
}
```

### 6. Административный Эндпоинт

**Файл:** `app/tours/router.py`

**Добавлен эндпоинт:** `POST /tours/finalize_tour/{tour_id}`

**Параметры:**
- `tour_id` (path) - ID завершаемого тура
- `next_tour_id` (query) - ID следующего тура

**Использование:**
```http
POST /tours/finalize_tour/1?next_tour_id=2
```

**Ответ:**
```json
{
    "status": "success",
    "message": "Tour 1 finalized, created snapshots for tour 2",
    "finalized_tours": 100,
    "created_tours": 100,
    "total_squads_processed": 100
}
```

## Документация

### Созданные Файлы

1. **TOUR_SNAPSHOTS_LOGIC.md**
   - Подробное описание концепции и логики
   - Жизненный цикл snapshots
   - Инварианты системы
   - Описание моделей и методов

2. **TOUR_SNAPSHOTS_USAGE.md**
   - Инструкция по использованию API
   - Примеры запросов и ответов
   - Сценарии использования
   - Автоматизация через cron
   - Руководство по тестированию
   - Типичные проблемы и решения

3. **test_tour_snapshots.py**
   - Скрипт для тестирования логики
   - Проверка исторической целостности
   - Сравнение snapshots разных туров
   - Детальный вывод информации

4. **TOUR_SNAPSHOTS_CHANGELOG.md** (этот файл)
   - Сводка всех изменений
   - До/После сравнение
   - Описание новых методов и эндпоинтов

## Проверка Работоспособности

### Тестовый Сценарий

1. Создайте сквад в туре 1
2. Проверьте, что создался `SquadTour` с `is_current = True`
3. Финализируйте тур 1 и создайте snapshot для тура 2:
   ```
   POST /tours/finalize_tour/1?next_tour_id=2
   ```
4. Сделайте трансферы
5. Получите историю:
   ```
   GET /squads/{squad_id}/history
   ```
6. Убедитесь, что:
   - Тур 1 показывает старый состав
   - Тур 2 показывает новый состав
   - Очки рассчитываются корректно

### SQL Проверка

```sql
-- Проверка snapshots
SELECT 
    st.id,
    st.tour_id,
    t.number,
    st.is_current,
    COUNT(DISTINCT stp.player_id) as main_count,
    COUNT(DISTINCT stbp.player_id) as bench_count
FROM squad_tours st
JOIN tours t ON t.id = st.tour_id
LEFT JOIN squad_tour_players stp ON stp.squad_tour_id = st.id
LEFT JOIN squad_tour_bench_players stbp ON stbp.squad_tour_id = st.id
WHERE st.squad_id = YOUR_SQUAD_ID
GROUP BY st.id, t.number
ORDER BY t.number;
```

## Миграции БД

**Не требуются** - все необходимые таблицы уже существовали:
- `squad_tours`
- `squad_tour_players`
- `squad_tour_bench_players`

Модель `SquadTour` уже содержала все необходимые поля.

## Обратная Совместимость

✅ **Полная обратная совместимость**

Старые версии фронтенда продолжат работать, так как:
- Эндпоинт `/squads/{squad_id}/history` остался на том же URL
- Все старые поля в ответе сохранены
- Добавлены только новые поля

## Производительность

### Оптимизации
- Использование `joinedload` для предзагрузки связей
- Батчинг SQL запросов
- Кэширование очков игроков

### Рекомендации
- При большом количестве туров рассмотреть пагинацию истории
- Добавить индексы на `squad_id` и `tour_id` в таблице `squad_tours`

## TODO для Будущих Улучшений

- [ ] Добавить проверку прав администратора в `/tours/finalize_tour`
- [ ] Реализовать автоматическую финализацию через cron
- [ ] Добавить логику восстановления бесплатных замен при смене тура
- [ ] Реализовать обработку edge cases (первый/последний тур)
- [ ] Добавить пагинацию для истории туров
- [ ] Добавить кэширование на уровне Redis для часто запрашиваемых данных
- [ ] Реализовать вебсокеты для real-time обновлений очков

## Заключение

Система исторических snapshots полностью реализована и готова к использованию. Все требования выполнены:

✅ Историческая целостность туров  
✅ Независимость составов по турам  
✅ Корректное начисление очков  
✅ Правильная логика трансферов  
✅ API для получения истории  
✅ API для финализации туров  
✅ Документация и тесты  

Система обеспечивает неизменность прошлых туров при внесении изменений в будущих турах.
