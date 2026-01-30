# Tour Snapshots - Быстрый Старт

## Что Это?

Система исторических snapshots сохраняет состав команды на момент каждого тура. Это гарантирует, что история не изменяется при последующих трансферах.

## Ключевые Концепции

```
Тур 1: [Игрок A, Игрок B, Игрок C] → 50 очков
         ↓ (snapshot зафиксирован)
Тур 2: [Игрок A, Игрок D, Игрок C] → 45 очков
         ↓ (новый snapshot)
         
История всегда показывает корректный состав для каждого тура!
```

## Главные API Endpoints

### Получить историю туров
```http
GET /squads/{squad_id}/history
```

### Завершить тур (для админа)
```http
POST /tours/finalize_tour/{tour_id}?next_tour_id={next_tour_id}
```

## Изменения в Коде

### ✅ Обновлено
- `app/squads/schemas.py` - расширена схема истории
- `app/squads/services.py` - добавлены методы работы с snapshots
- `app/squads/router.py` - обновлен эндпоинт истории
- `app/tours/router.py` - добавлен эндпоинт финализации

### ✅ Создано
- `TOUR_SNAPSHOTS_LOGIC.md` - подробная документация логики
- `TOUR_SNAPSHOTS_USAGE.md` - инструкция по использованию
- `TOUR_SNAPSHOTS_CHANGELOG.md` - полная сводка изменений
- `test_tour_snapshots.py` - тестовый скрипт

## Быстрый Тест

1. **Запустите бэкенд:**
   ```bash
   cd C:\Users\val2\projects\sporttg
   # запустите ваш FastAPI сервер
   ```

2. **Создайте сквад через API**

3. **Запустите тестовый скрипт:**
   ```bash
   python test_tour_snapshots.py
   ```
   Обновите `TEST_SQUAD_ID` на реальный ID сквада

4. **Проверьте историю через API:**
   ```bash
   curl http://localhost:8000/squads/{squad_id}/history
   ```

## Архитектура

```
┌─────────────┐
│   Squad     │  ← Текущий состав
└──────┬──────┘
       │
       ├──→ SquadTour (Tour 1) [Snapshot зафиксирован]
       ├──→ SquadTour (Tour 2) [Snapshot зафиксирован]
       └──→ SquadTour (Tour 3) [Текущий, is_current=True]
```

- **Squad**: текущий состав (изменяется при трансферах)
- **SquadTour**: неизменные snapshots для каждого тура

## Жизненный Цикл

1. **Создание сквада** → Создается SquadTour для текущего тура
2. **Трансферы** → Обновляется только snapshot текущего тура
3. **Завершение тура** → Финализация snapshot + создание нового
4. **Просмотр истории** → Возвращаются все snapshots

## Ключевые Методы

| Метод | Назначение |
|-------|-----------|
| `get_squad_tour_history_with_players()` | Получить полную историю с составами |
| `finalize_tour_for_all_squads()` | Завершить тур для всех сквадов |
| `_save_current_squad()` | Сохранить/обновить snapshot текущего тура |

## Важные Правила

✅ **DO:**
- Вызывайте `finalize_tour_for_all_squads()` при завершении тура
- Используйте `get_squad_tour_history_with_players()` для истории
- Проверяйте `is_current` для определения текущего snapshot

❌ **DON'T:**
- Не изменяйте напрямую старые SquadTour
- Не пропускайте вызов `_save_current_squad()` при трансферах
- Не забывайте обновлять `current_tour_id` при смене тура

## Автоматизация

Рекомендуется настроить cron для автоматической финализации туров:

```python
# Пример с APScheduler
@scheduler.scheduled_job('cron', hour=0, minute=0)
async def auto_finalize():
    for league in leagues:
        prev, curr, next = await TourService.get_previous_current_next_tour(league.id)
        if curr and is_finished(curr) and next:
            await SquadService.finalize_tour_for_all_squads(curr.id, next.id)
```

## Миграции

**Не требуются!** Все необходимые таблицы уже существуют.

## Обратная Совместимость

✅ **100% обратная совместимость**

Старые клиенты продолжат работать. Новые поля опциональны.

## Документация

Читайте подробнее:
- **Логика**: `TOUR_SNAPSHOTS_LOGIC.md`
- **Использование**: `TOUR_SNAPSHOTS_USAGE.md`
- **Изменения**: `TOUR_SNAPSHOTS_CHANGELOG.md`

## Тестирование

```bash
# Запуск теста
python test_tour_snapshots.py

# SQL проверка
SELECT tour_id, COUNT(*) FROM squad_tour_players 
WHERE squad_tour_id IN (SELECT id FROM squad_tours WHERE squad_id = 1)
GROUP BY tour_id;
```

## Контакты и Поддержка

При возникновении вопросов см. подробную документацию в файлах `TOUR_SNAPSHOTS_*.md`

---

**Дата:** 2026-01-30  
**Статус:** ✅ Готово к использованию
