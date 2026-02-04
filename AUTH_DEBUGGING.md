# Диагностика проблемы авторизации

## Проблема
При авторизации через Telegram появляется ошибка: "Ошибка авторизации: Неизвестная ошибка. Попробуйте перезапустить приложение."

## Что было сделано
1. Добавлено детальное логирование во фронтенде:
   - `TelegramProvider.tsx` - логирование initData и ответа от бэкенда
   - `auth.ts` - логирование процесса loginWithTelegram
   - `api.ts` - логирование запросов через api-proxy

## Что проверить

### 1. Логи браузера (Frontend)
Откройте DevTools в браузере Telegram и проверьте консоль на наличие сообщений:
- `[callBackend] Request to /api/users/login`
- `[loginWithTelegram] API response received`
- Обратите внимание на статус ответа и текст ошибки

### 2. Логи бэкенда (Backend)
На сервере проверьте логи FastAPI приложения:
```bash
tail -f /path/to/logs/app.log | grep -E "(login|auth|error|validation)"
```

Ищите сообщения:
- `Login attempt started`
- `Validation error:`
- `Hash mismatch`
- `Init data expired`
- `Authentication error:`

### 3. Переменные окружения
Убедитесь, что на бэкенде правильно настроены:
- `TELEGRAM_BOT_TOKEN` - токен вашего бота (проверьте, что он актуальный)
- `SECRET_KEY` - секретный ключ для JWT токенов
- `MODE` - режим работы (PROD для production)

### 4. Частые причины ошибок

#### Hash mismatch (Неверная подпись)
**Причина**: Неправильный TELEGRAM_BOT_TOKEN
**Решение**: Проверьте токен бота в `.env` файле на сервере

#### Init data expired (Данные устарели)
**Причина**: Разница во времени > 1 часа между клиентом и сервером
**Решение**: Синхронизируйте время на сервере с помощью NTP

#### No initData available
**Причина**: Приложение не запущено через Telegram
**Решение**: Убедитесь, что приложение открывается через Telegram Mini App

#### Supabase function error
**Причина**: Проблемы с Supabase Edge Function (api-proxy)
**Решение**: 
- Проверьте логи Supabase Dashboard
- Убедитесь, что функция развернута
- Проверьте переменную BACKEND_URL в настройках функции

## Проверка шаг за шагом

1. **Откройте приложение в Telegram**
2. **Откройте DevTools в браузере Telegram**
3. **Перезагрузите приложение**
4. **Проверьте консоль на наличие логов**
5. **Найдите ошибку и её детали**:
   - Если ошибка "Hash mismatch" → проверьте TELEGRAM_BOT_TOKEN
   - Если ошибка "Init data expired" → проверьте время на сервере
   - Если ошибка "Proxy request failed" → проверьте доступность бэкенда
   - Если статус 401/403 → проверьте логи бэкенда

## Временное решение для тестирования
Если нужно быстро протестировать без авторизации, установите `MODE=DEV` в `.env` на бэкенде. Это отключит проверку Telegram данных и будет использоваться тестовый пользователь.

**ВАЖНО**: Не используйте DEV режим в production!

## Код изменений
Изменённые файлы:
- `tele-mini-sparkle/src/providers/TelegramProvider.tsx` - улучшенная обработка ошибок
- `tele-mini-sparkle/src/lib/auth.ts` - детальное логирование
- `tele-mini-sparkle/src/lib/api.ts` - логирование запросов

## Дополнительная проверка на бэкенде

### Проверить валидацию Telegram данных
```python
# Добавьте в app/users/utils.py временное логирование:

def validate_telegram_data(init_data: str) -> dict:
    logger.info(f"Validating init_data (length: {len(init_data)})")
    logger.info(f"First 100 chars: {init_data[:100]}")
    # ... остальной код
```

### Проверить токен бота
```bash
# На сервере:
grep TELEGRAM_BOT_TOKEN .env
# Убедитесь, что токен правильный и без лишних пробелов
```

### Проверить время на сервере
```bash
date
# Если время неправильное, синхронизируйте:
sudo ntpdate -s time.nist.gov
```
