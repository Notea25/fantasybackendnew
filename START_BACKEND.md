# Запуск бэкенда после исправлений

## Установка зависимостей

### Вариант 1: Poetry (рекомендуется)
```powershell
# Установить Poetry (если не установлен)
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -

# Установить зависимости
poetry install

# Запустить сервер
poetry run uvicorn app.main:app --reload
```

### Вариант 2: pip + venv
```powershell
# Создать виртуальное окружение
python -m venv venv

# Активировать окружение
.\venv\Scripts\Activate.ps1

# Установить зависимости (если есть requirements.txt)
pip install -r requirements.txt

# Или установить необходимые пакеты
pip install fastapi uvicorn sqlalchemy alembic pydantic

# Запустить сервер
uvicorn app.main:app --reload
```

## Проверка работы

После запуска сервер должен быть доступен:
- **API**: http://127.0.0.1:8000
- **Docs**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc

## Тестирование исправлений

### 1. Проверить API endpoint
Откройте http://127.0.0.1:8000/docs и найдите:
- `POST /squads/{squad_id}/replace_players`

### 2. Сделать тестовый запрос
```json
POST /squads/123/replace_players
{
  "main_player_ids": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
  "bench_player_ids": [12, 13, 14, 15]
}
```

### 3. Проверить ответ
Должны быть новые поля:
```json
{
  "status": "success",
  "message": "Players replaced successfully",
  "remaining_replacements": 0,
  "transfers_applied": 2,
  "free_transfers_used": 2,
  "paid_transfers": 0,
  "penalty": 0,
  "new_total_points": 0,
  "squad": { ... }
}
```

### 4. Проверить логи
В консоли должны появиться записи:
```
Squad 123 transfer calculation: transfer_count=2, available_replacements=3, current_points=0
Squad 123 transfers completed: transfers=2, free=2, paid=0, penalty=0, new_points=0, remaining_replacements=1
```

## Проверка с фронтендом

1. Запустите фронтенд:
   ```powershell
   cd C:\Users\val2\projects\tele-mini-sparkle
   npm run dev
   ```

2. Откройте страницу трансферов

3. Попробуйте сделать трансферы когда `replacements = 0`

4. **Ожидаемое поведение:**
   - ✅ Трансферы разрешены (не блокируются)
   - ✅ Показывается информация о штрафе
   - ✅ Очки уменьшаются на размер штрафа

5. **Старое поведение (ошибка):**
   - ❌ "Ошибка: No replacements left"

## Troubleshooting

### Python не найден
Установите Python 3.10+ с https://python.org

### Poetry не установлен
```powershell
pip install poetry
```

### Ошибки при запуске
Проверьте:
1. База данных запущена (PostgreSQL)
2. Файл `.env` настроен корректно
3. Миграции применены: `poetry run alembic upgrade head`
