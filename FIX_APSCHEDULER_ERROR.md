# Исправление ошибки: ModuleNotFoundError: No module named 'apscheduler'

## Проблема

При запуске приложения возникает ошибка:
```
ModuleNotFoundError: No module named 'apscheduler'
```

Это происходит потому что APScheduler был добавлен в код, но не был добавлен в зависимости проекта.

## ✅ Решение Выполнено

Зависимость **уже добавлена** в `pyproject.toml`:
```toml
"apscheduler (>=3.10.4,<4.0.0)"
```

## Шаги для Применения Изменений

### Вариант 1: Docker (Рекомендуется)

1. **Запустите Docker Desktop** (если не запущен)

2. **Остановите контейнеры:**
   ```bash
   cd C:\Users\val2\projects\sporttg
   docker-compose down
   ```

3. **Пересоберите контейнеры с новыми зависимостями:**
   ```bash
   docker-compose up --build -d
   ```

4. **Проверьте логи:**
   ```bash
   docker-compose logs -f sp_app
   ```

   Должны увидеть:
   ```
   INFO - Scheduler started
   INFO - Scheduled tour finalization: 0 * * * *
   ```

### Вариант 2: Локальная Установка (без Docker)

Если запускаете без Docker:

1. **Обновите зависимости через Poetry:**
   ```bash
   cd C:\Users\val2\projects\sporttg
   poetry install
   ```

2. **Или через pip (если не используете Poetry):**
   ```bash
   pip install apscheduler==3.10.4
   ```

3. **Запустите приложение:**
   ```bash
   python -m app.main
   # или
   uvicorn app.main:app --reload
   ```

### Вариант 3: Обновление Poetry Lock

Если используете Poetry и хотите обновить lock файл:

```bash
cd C:\Users\val2\projects\sporttg
poetry lock
poetry install
```

## Проверка Успешной Установки

После перезапуска проверьте:

### 1. Статус Scheduler через API
```bash
curl http://localhost:8000/api/tours/scheduler/status
```

**Ожидаемый ответ:**
```json
{
  "status": "running",
  "scheduled_jobs": [
    {
      "id": "tour_finalization",
      "name": "Tour Finalization",
      "next_run_time": "2026-01-30T20:00:00+00:00",
      "trigger": "cron[hour='*', minute='0']"
    }
  ],
  "total_jobs": 1
}
```

### 2. Проверка в Логах

В логах приложения должны быть строки:
```
INFO - Starting application and scheduler...
INFO - Scheduler started
INFO - Scheduled tour finalization: 0 * * * *
INFO - Application started
```

## Troubleshooting

### Ошибка: Docker Desktop не запущен

**Симптомы:**
```
error during connect: ... open //./pipe/dockerDesktopLinuxEngine: The system cannot find the file specified
```

**Решение:**
1. Откройте Docker Desktop
2. Дождитесь полного запуска (иконка перестанет мигать)
3. Повторите команды пересборки

### Ошибка: Poetry команды не работают

**Решение:**
```bash
# Установите Poetry если еще не установлен
pip install poetry

# Или используйте через python -m
python -m poetry install
```

### Scheduler не запускается после установки

**Проверьте:**

1. **Правильность импортов** в `app/main.py`:
   ```python
   from app.scheduler.config import start_scheduler, shutdown_scheduler
   ```

2. **Наличие переменных окружения** в `.env`:
   ```env
   TOUR_FINALIZATION_CRON="0 * * * *"
   RUN_FINALIZATION_ON_STARTUP="false"
   ```

3. **Логи на ошибки импорта:**
   ```bash
   docker-compose logs sp_app | grep -i error
   ```

## Дополнительная Настройка

### Изменение Расписания

Отредактируйте `.env`:
```env
# Каждые 30 минут
TOUR_FINALIZATION_CRON="*/30 * * * *"

# Каждый день в 2 часа ночи
TOUR_FINALIZATION_CRON="0 2 * * *"

# Каждый час
TOUR_FINALIZATION_CRON="0 * * * *"
```

После изменения перезапустите приложение:
```bash
docker-compose restart sp_app
```

### Запуск Финализации при Старте (для тестирования)

В `.env`:
```env
RUN_FINALIZATION_ON_STARTUP="true"
```

⚠️ **Внимание:** Используйте только для тестирования! В production оставьте `false`.

## Дополнительные Команды

### Просмотр установленных пакетов (Poetry)
```bash
poetry show apscheduler
```

### Просмотр установленных пакетов (pip)
```bash
pip show apscheduler
```

### Пересоздание контейнеров с нуля
```bash
docker-compose down -v
docker-compose up --build
```

## Проверка Работы Финализации

1. **Создайте тестовый сквад** через API
2. **Дождитесь завершения тура** (или смените `current_tour_id` вручную)
3. **Проверьте логи** на сообщения о финализации:
   ```
   INFO - Starting automatic tour finalization check
   INFO - Found 1 leagues to check
   INFO - Finalized tour X -> Y for league Z
   ```

4. **Проверьте через API:**
   ```bash
   curl http://localhost:8000/api/squads/1/history
   ```

## Успех! ✅

После выполнения этих шагов:
- ✅ APScheduler установлен
- ✅ Scheduler запущен и работает
- ✅ Автоматическая финализация туров настроена
- ✅ Ошибка исправлена

## Поддержка

Если проблема сохраняется:
1. Проверьте версию Python (должна быть >= 3.12)
2. Очистите кэш Poetry: `poetry cache clear pypi --all`
3. Пересоздайте виртуальное окружение: `poetry env remove python && poetry install`
4. Проверьте Docker образ: `docker-compose build --no-cache sp_app`
