# Решение проблемы Invalid Signature

## Проблема
```
InvalidSignatureException: 401: Invalid signature
```

Это означает, что `TELEGRAM_BOT_TOKEN` на бэкенде не совпадает с токеном бота.

## Как исправить

### 1. Узнайте правильный токен бота
1. Откройте Telegram
2. Найдите бота @BotFather
3. Отправьте команду `/mybots`
4. Выберите вашего бота
5. Нажмите "API Token"
6. Скопируйте токен (формат: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`)

### 2. Обновите токен на сервере

Подключитесь к серверу и выполните:

```bash
# Перейдите в папку проекта
cd /path/to/sporttg

# Откройте .env файл
nano .env

# Найдите строку TELEGRAM_BOT_TOKEN и замените на правильный токен
TELEGRAM_BOT_TOKEN=ВАШ_ПРАВИЛЬНЫЙ_ТОКЕН_СЮДА

# Сохраните (Ctrl+O, Enter, Ctrl+X)
```

### 3. Перезапустите бэкенд

```bash
# Если используется Docker:
docker-compose restart

# Или перезапустите конкретный контейнер:
docker-compose restart app

# Если используется systemd:
sudo systemctl restart sporttg
```

### 4. Проверьте логи

```bash
# Docker:
docker-compose logs -f app

# Или:
tail -f /path/to/logs/app.log
```

### 5. Проверьте авторизацию снова

Откройте приложение в Telegram и попробуйте авторизоваться снова.

## Альтернативный способ проверки токена

Если не можете подключиться к серверу, попросите администратора выполнить:

```bash
# На сервере
cd /path/to/sporttg
grep TELEGRAM_BOT_TOKEN .env
```

Убедитесь, что токен:
- Начинается с цифр
- Содержит двоеточие `:`
- После двоеточия идёт длинная строка букв и цифр
- Нет лишних пробелов до или после токена
- Нет кавычек вокруг токена (если они есть, уберите)

## Правильный формат в .env

```bash
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
```

❌ **Неправильно:**
```bash
TELEGRAM_BOT_TOKEN="1234567890:ABCdefGHIjklMNOpqrsTUVwxyz"  # Лишние кавычки
TELEGRAM_BOT_TOKEN= 1234567890:ABCdefGHIjklMNOpqrsTUVwxyz  # Пробел после =
TELEGRAM_BOT_TOKEN=старый_токен  # Неактуальный токен
```

## Проверка после исправления

После обновления токена и перезапуска:
1. Откройте приложение в Telegram
2. Перейдите на `/debug-auth`
3. Нажмите "Проверить авторизацию"
4. Должно появиться: `Success: true`
