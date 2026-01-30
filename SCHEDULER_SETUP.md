# Настройка Автоматической Финализации Туров

## Установка Зависимостей

Добавьте в `requirements.txt`:

```
APScheduler==3.10.4
```

Установите:
```bash
pip install APScheduler==3.10.4
```

## Переменные Окружения

Добавьте в `.env`:

```env
# Расписание финализации туров (формат cron)
# Формат: "минута час день месяц день_недели"
# По умолчанию: каждый час в начале часа
TOUR_FINALIZATION_CRON="0 * * * *"

# Запускать финализацию при старте приложения (для тестирования)
RUN_FINALIZATION_ON_STARTUP="false"
```

## Примеры Расписаний

| Описание | Значение |
|----------|----------|
| Каждый час | `0 * * * *` |
| Каждые 30 минут | `*/30 * * * *` |
| Раз в день в полночь | `0 0 * * *` |
| Раз в день в 2 часа ночи | `0 2 * * *` |
| Каждый понедельник в полночь | `0 0 * * 1` |

## Проверка Работы

### 1. Статус Scheduler

```bash
curl http://localhost:8000/api/tours/scheduler/status
```

Ответ:
```json
{
  "status": "running",
  "scheduled_jobs": [
    {
      "id": "tour_finalization",
      "name": "Tour Finalization",
      "next_run_time": "2026-01-30T19:00:00+00:00",
      "trigger": "cron[hour='*', minute='0']"
    }
  ],
  "total_jobs": 1
}
```

### 2. Ручная Финализация

```bash
curl -X POST "http://localhost:8000/api/tours/finalize_tour/1?next_tour_id=2" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 3. Логи

Проверьте логи приложения:
```
2026-01-30 18:00:00 - app.scheduler.config - INFO - Scheduler started
2026-01-30 18:00:00 - app.scheduler.config - INFO - Scheduled tour finalization: 0 * * * *
2026-01-30 19:00:00 - app.scheduler.tour_finalizer - INFO - Starting automatic tour finalization check
```

## Архитектура

```
FastAPI App
    ↓
scheduler/
├── config.py           # Настройка APScheduler
├── tour_finalizer.py   # Логика финализации
└── __init__.py

Процесс:
1. При старте FastAPI → start_scheduler()
2. APScheduler по расписанию → run_tour_finalization()
3. TourFinalizer проверяет все лиги
4. Для завершенных туров создаются snapshots
5. При остановке FastAPI → shutdown_scheduler()
```

## Мониторинг

### Эндпоинты

- `GET /api/tours/scheduler/status` - статус scheduler
- `POST /api/tours/finalize_tour/{tour_id}` - ручная финализация

### Логирование

Все операции логируются:
- `app.scheduler.config` - управление scheduler
- `app.scheduler.tour_finalizer` - процесс финализации
- `app.squads.services` - операции с SquadTour

## Troubleshooting

### Scheduler не запускается

**Проблема:** Ошибка при старте приложения

**Решение:**
1. Проверьте установку APScheduler: `pip show apscheduler`
2. Проверьте логи на ошибки импорта
3. Убедитесь, что формат CRON корректный

### Задачи не выполняются

**Проблема:** Scheduler запущен, но финализация не происходит

**Решение:**
1. Проверьте статус: `GET /api/tours/scheduler/status`
2. Проверьте `next_run_time` - когда следующий запуск
3. Проверьте логи на ошибки в `run_tour_finalization`
4. Убедитесь, что есть туры для финализации

### Дублирование Финализации

**Проблема:** Туры финализируются несколько раз

**Решение:**
- Scheduler настроен с `max_instances=1` - предотвращает параллельные запуски
- Проверка `_check_if_tour_finalized` предотвращает повторную финализацию
- Если проблема сохраняется, проверьте логи на race conditions

## Production Рекомендации

1. **Используйте отдельный процесс для cron**
   - Если у вас несколько инстансов FastAPI
   - Настройте только на одном инстансе

2. **Мониторинг**
   - Добавьте алерты на ошибки в логах
   - Мониторьте `next_run_time` задач

3. **Backup**
   - Держите ручной эндпоинт финализации
   - Документируйте процедуру восстановления

4. **Тестирование**
   - Используйте `RUN_FINALIZATION_ON_STARTUP=true` для тестов
   - Проверяйте на staging окружении

## Альтернативы

### System Cron (Linux/Mac)

Если предпочитаете system cron:

```cron
# /etc/cron.d/tour-finalization
0 * * * * curl -X POST http://localhost:8000/api/tours/finalize_tour/CURRENT_TOUR_ID?next_tour_id=NEXT_TOUR_ID
```

### Celery

Для более сложных сценариев рассмотрите Celery:
- Distributed task queue
- Лучше для множественных инстансов
- Требует Redis/RabbitMQ

## FAQ

**Q: Что если приложение перезапускается во время финализации?**  
A: Scheduler автоматически перезапустится. Логика проверяет, был ли тур уже финализирован.

**Q: Можно ли изменить расписание без перезапуска?**  
A: Нет, нужен перезапуск приложения. Измените `.env` и перезапустите.

**Q: Как протестировать финализацию?**  
A: Установите `RUN_FINALIZATION_ON_STARTUP=true` или вызовите ручной эндпоинт.

**Q: Влияет ли финализация на производительность?**  
A: Минимально. Выполняется в фоне, не блокирует API requests.
