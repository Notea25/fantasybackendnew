# Проблема: Новый пользователь не может создать команду

## Симптомы
Пользователь заходит в приложение через Telegram Mini App, заполняет состав команды, нажимает "Сохранить", но получает ошибку "Не удалось создать команду".

## Логи ошибки
```
sp_app | 2026-02-03 13:35:07 - app.users.dependencies - ERROR - Authentication error: 401: Authentication failed
sp_app | Traceback (most recent call last):
sp_app |   File "/app/app/users/dependencies.py", line 68, in get_current_user
sp_app |     raise AuthenticationFailedException()
sp_app | app.utils.exceptions.AuthenticationFailedException: 401: Authentication failed
sp_app | INFO: 172.18.0.4:53654 - "GET /api/users/protected HTTP/1.1" 401 Unauthorized
sp_app | 2026-02-03 13:35:07 - app.users.router - DEBUG - No refresh token cookie provided
sp_app | INFO: 172.18.0.4:53656 - "POST /api/users/refresh HTTP/1.1" 401 Unauthorized
```

## Анализ проблемы

### Основная причина
**Пользователь НЕ авторизован** - запрос создания команды идёт без действительного access token.

### Почему это происходит?

1. **Ошибка авторизации проглатывается молча** (Frontend)
   - В `TelegramProvider.tsx` строки 108-110
   - При ошибке `loginWithTelegram()` приложение продолжает работать
   - Пользователь видит интерфейс, но не авторизован
   - При попытке создать команду → 401 Unauthorized

2. **Возможные причины ошибки авторизации:**

   **A. Telegram initData не передаётся или пустая**
   - `window.Telegram?.WebApp?.initData` undefined
   - Telegram WebApp не инициализировался правильно
   - Приложение открыто не через Telegram бота

   **B. Валидация initData на бэкенде падает**
   - Неправильный TELEGRAM_BOT_TOKEN
   - initData истекла (>1 час с момента генерации)
   - Hash не совпадает (подделка данных)

   **C. Supabase Edge Functions блокируют cookies**
   - Backend устанавливает refresh_token в cookies
   - Но через api-proxy cookies не передаются правильно
   - При попытке обновить токен → "No refresh token cookie provided"

3. **Короткое время жизни access token**
   - Access token живёт всего **15 минут** (ACCESS_TOKEN_EXPIRE_MINUTES=15)
   - Если пользователь долго собирает команду → токен истекает
   - Refresh token не работает из-за проблемы с cookies

## Исправления

### 1. Backend: Optional captain/vice-captain (commit eb6db0f)
```python
# app/squads/schemas.py
captain_id: Optional[int] = None  # Было: int
vice_captain_id: Optional[int] = None  # Было: int
```

**Проблема:** Pydantic требовал обязательные captain/vice-captain, но фронтенд мог отправлять null.

### 2. Backend: Fix datetime timezone (commit 0d09d4b)
```python
# app/squads/services.py (строка 194)
created_at=datetime.now(timezone.utc)  # Было: datetime.utcnow()
```

**Проблема:** База данных ожидает timezone-aware datetime, но получала naive datetime.

### 3. Frontend: Better error handling (commit 46dd5c4)
```typescript
// src/providers/TelegramProvider.tsx
// Добавлено:
- Логирование наличия initData
- Проверка успешности login response
- Alert пользователю при ошибке авторизации
- Детальное логирование в console
```

**Проблема:** Ошибки авторизации проглатывались молча, пользователь не знал что не авторизован.

## Диагностика для пользователя

### В консоли браузера (F12 → Console) проверить:

1. **Telegram initData доступна?**
```javascript
console.log('InitData:', window.Telegram?.WebApp?.initData);
console.log('User:', window.Telegram?.WebApp?.initDataUnsafe?.user);
```

2. **Токены в localStorage?**
```javascript
console.log('Access Token:', localStorage.getItem('fantasyAccessToken'));
console.log('Refresh Token:', localStorage.getItem('fantasyRefreshToken'));
console.log('User ID:', localStorage.getItem('fantasyUserId'));
```

3. **Логи авторизации**
Искать в console:
- "Telegram initData available: true/false"
- "Attempting Telegram login..."
- "Login response: {success: true/false}"

### В Network tab (F12 → Network):

1. **Проверить запрос `/api/users/login`**
   - Был ли запрос?
   - Статус: 200 (успех) или 401/500 (ошибка)?
   - Response содержит access_token?

2. **Проверить запрос `/api/squads/create`**
   - Есть ли заголовок Authorization: Bearer ...?
   - Статус ответа?
   - Текст ошибки в response?

## Решения для пользователя

### Временное решение (сейчас):

1. **Перезапустить приложение**
   - Полностью закрыть Telegram
   - Открыть Telegram заново
   - Запустить Mini App через бота

2. **Очистить данные приложения** (если перезапуск не помог)
   - Telegram → Settings → Advanced → Clear cache
   - Перезапустить приложение

3. **Проверить доступ через бота**
   - Убедиться что приложение открыто через Telegram бота
   - НЕ через прямую ссылку в браузере

### Долгосрочное решение:

1. **Увеличить время жизни access token**
   ```env
   # .env
   ACCESS_TOKEN_EXPIRE_MINUTES=60  # Вместо 15
   ```

2. **Автоматический перелогин при 401**
   - Если refresh token не работает
   - Попробовать повторить loginWithTelegram с текущим initData
   - Если initData тоже истекла → попросить перезапустить приложение

3. **Исправить передачу cookies через Supabase Edge Functions**
   - Или полностью перейти на передачу токенов в body/headers
   - Убрать зависимость от cookies для refresh_token

## Архитектурные проблемы

### 1. Supabase Edge Functions как прокси
**Проблема:** Cookies не передаются правильно между клиентом и бэкендом через api-proxy.

**Решение:** 
- Передавать refresh_token в теле запроса вместо cookies
- Или использовать прямое подключение к бэкенду без прокси

### 2. Короткое время жизни токена (15 минут)
**Проблема:** Пользователь может собирать команду >15 минут → токен истекает.

**Решение:**
- Увеличить ACCESS_TOKEN_EXPIRE_MINUTES до 60 минут
- Или добавить автоматическое обновление токена каждые 10 минут

### 3. Молчаливые ошибки авторизации
**Проблема:** Пользователь не знал что не авторизован до попытки создать команду.

**Решение:** ✅ Исправлено в commit 46dd5c4
- Теперь показывается alert при ошибке авторизации
- Логируется подробная информация в console

## Checklist для проверки

- [x] Backend принимает Optional captain/vice-captain
- [x] Backend использует timezone-aware datetime
- [x] Frontend показывает ошибки авторизации
- [ ] Увеличено время жизни access token (требует изменения .env)
- [ ] Добавлен автоматический перелогин при 401
- [ ] Исправлена передача refresh_token (cookies → body)

## Файлы изменены

### Backend:
- `app/squads/schemas.py` - Optional captain/vice-captain
- `app/squads/services.py` - timezone-aware datetime

### Frontend:
- `src/providers/TelegramProvider.tsx` - error handling и логирование

## Коммиты

### Backend:
- `eb6db0f` - FIX SQUAD CREATION - MAKE CAPTAIN/VICE-CAPTAIN OPTIONAL
- `0d09d4b` - FIX DATETIME TIMEZONE ERROR IN SQUAD CREATION

### Frontend:
- `46dd5c4` - ADD BETTER ERROR HANDLING FOR TELEGRAM LOGIN FAILURES

---

**Дата анализа:** 2026-02-03
**Статус:** Частично исправлено, требуется дальнейшее тестирование
