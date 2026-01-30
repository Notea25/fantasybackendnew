# Обновление poetry.lock для APScheduler

## Проблема

При сборке Docker контейнера возникает ошибка:
```
pyproject.toml changed significantly since poetry.lock was last generated. 
Run `poetry lock` to fix the lock file.
```

## Решение

Выполните эти команды **на сервере** (где запущен Docker):

```bash
cd ~/sporttg

# Вариант 1: Если Poetry установлен на сервере
poetry lock --no-update

# Вариант 2: Использовать Docker контейнер для обновления lock файла
docker run --rm -v "$(pwd):/app" -w /app python:3.12 bash -c "pip install poetry && poetry lock --no-update"

# После обновления lock файла
git add poetry.lock
git commit -m "Update poetry.lock with apscheduler dependency"
git push origin main

# Теперь пересоберите контейнер
docker-compose down
docker-compose up --build -d
```

## Быстрое Решение (Recommended)

Просто выполните эти команды на сервере одной строкой:

```bash
cd ~/sporttg && \
docker run --rm -v "$(pwd):/app" -w /app python:3.12 bash -c "pip install poetry && poetry lock --no-update" && \
git add poetry.lock && \
git commit -m "Update poetry.lock with apscheduler" && \
git push origin main && \
docker-compose up --build -d
```

## Альтернатива: Локальное Обновление (на Windows)

Если хотите обновить локально на Windows:

### Установите Poetry:
```powershell
# PowerShell
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -
```

### Добавьте в PATH:
```powershell
$env:Path += ";$env:APPDATA\Python\Scripts"
```

### Обновите lock:
```powershell
cd C:\Users\val2\projects\sporttg
poetry lock --no-update
git add poetry.lock
git commit -m "Update poetry.lock with apscheduler"
git push origin main
```

## Проверка

После успешного обновления и пересборки проверьте:

```bash
# На сервере
docker-compose logs sp_app | grep -i "scheduler"
```

Должны увидеть:
```
INFO - Scheduler started
INFO - Scheduled tour finalization: 0 * * * *
```

## Если poetry.lock уже обновлен в репозитории

Если вы видите эту ошибку после `git pull`, просто пересоберите:

```bash
docker-compose down
docker-compose build --no-cache sp_app
docker-compose up -d
```
