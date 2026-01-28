# Исправление: Поддержка платных трансферов

## Изменённые файлы

### 1. `app/squads/services.py`
**Функция:** `replace_players()` (строки 757-898)

#### Изменения:
- **Убрана жёсткая блокировка** (строки 835-841): `raise HTTPException("No replacements left")`
- **Добавлен подсчёт трансферов** (строки 835-843): считаем реальное количество замен
- **Реализована логика платных трансферов** (строки 845-863):
  - Если `replacements >= transfer_count` → все бесплатные
  - Если `replacements < transfer_count` → часть бесплатных, часть платных
  - Штраф: `penalty = paid_transfers * 4`
  - **Вычитание очков**: `squad.points -= penalty` (может уйти в минус!)
- **Возврат детальной информации** (строки 891-898):
  ```python
  return {
      "squad": squad,
      "transfers_applied": transfer_count,
      "free_transfers_used": free_transfers_used,
      "paid_transfers": paid_transfers,
      "penalty": penalty,
  }
  ```
- **Логирование** (строки 850-855): для отладки

### 2. `app/squads/schemas.py`
**Схема:** `SquadReplacePlayersResponseSchema` (строки 56-66)

#### Добавлены поля:
```python
transfers_applied: Optional[int] = None
free_transfers_used: Optional[int] = None
paid_transfers: Optional[int] = None
penalty: Optional[int] = None
new_total_points: Optional[int] = None
```

### 3. `app/squads/router.py`
**Эндпоинт:** `POST /{squad_id}/replace_players` (строки 96-140)

#### Изменения:
- Обработка возвращаемого словаря вместо объекта squad (строка 116)
- Извлечение данных: `squad = result["squad"]`
- Передача всех полей в response (строки 135-139)
- Логирование результата (строки 120-128)

## Логика работы

### До исправления:
```
replacements = 0 → ❌ HTTPException 400 "No replacements left"
```

### После исправления:
```
Пример 1: replacements=2, transfers=1
→ free_used=1, paid=0, penalty=0, replacements=1 ✅

Пример 2: replacements=1, transfers=3
→ free_used=1, paid=2, penalty=8, replacements=0, points -= 8 ✅

Пример 3: replacements=0, transfers=2, points=0
→ free_used=0, paid=2, penalty=8, replacements=0, points=-8 ✅
```

## Пример ответа API

### Успешный ответ с платными трансферами:
```json
{
  "status": "success",
  "message": "Players replaced successfully",
  "remaining_replacements": 0,
  "transfers_applied": 3,
  "free_transfers_used": 2,
  "paid_transfers": 1,
  "penalty": 4,
  "new_total_points": -4,
  "squad": {
    "id": 123,
    "name": "My Squad",
    "points": -4,
    ...
  }
}
```

## Тестирование

### Проверить:
1. ✅ Бесплатные трансферы работают (replacements уменьшаются)
2. ✅ Платные трансферы разрешены (не блокируются)
3. ✅ Штраф правильно рассчитывается (paid_transfers × 4)
4. ✅ Очки уменьшаются на penalty
5. ✅ Очки могут уходить в минус
6. ✅ API возвращает детальную информацию

### Запустить:
```bash
# В директории sporttg
uvicorn app.main:app --reload
```

### Проверить логи:
```
Squad {squad_id} transfer calculation: transfer_count=..., available_replacements=..., current_points=...
Squad {squad_id} transfers completed: transfers=..., free=..., paid=..., penalty=..., new_points=..., remaining_replacements=...
```

## Совместимость с фронтендом

Фронтенд ожидает новые поля:
- ✅ `transfers_applied`
- ✅ `free_transfers_used`
- ✅ `paid_transfers`
- ✅ `penalty`
- ✅ `new_total_points`

После обновления бэкенда фронтенд сможет:
1. Показывать детальную информацию о трансферах
2. Синхронизировать локальное состояние с сервером
3. Корректно отображать штрафы пользователю

## Бусты (TODO)

⚠️ **Примечание:** Логика бустов "Трансферы +" и "Золотой тур" пока не реализована в `replace_players`.

Для полной поддержки нужно:
1. Проверять активные бусты для squad
2. Если активен `transfers_plus` или `gold_tour`:
   - Не тратить `replacements`
   - Не применять `penalty`
3. Пример проверки:
   ```python
   # Проверить активный буст для следующего тура
   active_boost = await get_active_boost_for_next_tour(squad_id)
   if active_boost in ['transfers_plus', 'gold_tour']:
       # Все трансферы бесплатны
       free_transfers_used = transfer_count
       paid_transfers = 0
       penalty = 0
       # НЕ уменьшать squad.replacements
   ```
