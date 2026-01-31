# Цель
Убрать дублирование данных между Squad и SquadTour, перенеся все изменяемое состояние в SquadTour. Squad будет хранить только метаданные команды, а каждая запись SquadTour будет полным снепшотом состояния команды на конкретный тур.
# Текущая проблема
* Дублирование данных: budget, replacements, points, penalty_points, captain_id, vice_captain_id хранятся и в Squad, и в SquadTour
* Сложная логика синхронизации при переходе между турами
* Костыли: current_tour_id, next_tour_penalty_points
* Риск рассинхронизации данных
* Разная логика для "текущего" vs "исторического" тура
# Итоговая архитектура
## Squad (только метаданные)
```python
class Squad:
    id: int
    name: str
    user_id: int
    league_id: int
    fav_team_id: int
    created_at: datetime
    # Relationships
    user, league, fav_team, tour_history
```
## SquadTour (полное состояние на тур)
```python
class SquadTour:
    id: int
    squad_id: int
    tour_id: int
    
    # Состав (уже есть)
    main_players: List[Player]
    bench_players: List[Player]
    captain_id: int
    vice_captain_id: int
    
    # Финансы и трансферы (НОВОЕ)
    budget: int
    replacements: int
    
    # Очки (уже есть)
    points: int
    penalty_points: int
    
    # Мета
    used_boost: str | None
    is_finalized: bool  # матчи завершены
    created_at: datetime
```
# Этапы рефакторинга
## Этап 1: Подготовка и анализ (Исследование)
### 1.1 Аудит использования полей Squad
Найти все места в коде, где используются поля:
* squad.budget
* squad.replacements
* squad.points
* squad.penalty_points
* squad.captain_id
* squad.vice_captain_id
* squad.next_tour_penalty_points
* squad.current_tour_id
* squad.current_main_players
* squad.current_bench_players
Файлы для проверки:
* app/squads/services.py (все методы)
* app/squads/router.py (все endpoints)
* app/squads/schemas.py (SquadReadSchema и др.)
* app/custom_leagues/ (все использования Squad)
* app/tours/services.py (финализация туров)
### 1.2 Создать документ с инвентаризацией
Создать таблицу:
* Файл:метод/endpoint
* Какое поле используется
* Для чего (чтение/запись)
* Как будет работать после рефакторинга
## Этап 2: Создание миграции БД
### 2.1 Добавить поля в SquadTour
Создать миграцию Alembic:
```python
# alembic/versions/xxx_add_budget_replacements_to_squad_tour.py
def upgrade():
    op.add_column('squad_tours', sa.Column('budget', sa.Integer(), nullable=False, server_default='100000'))
    op.add_column('squad_tours', sa.Column('replacements', sa.Integer(), nullable=False, server_default='2'))
    op.add_column('squad_tours', sa.Column('is_finalized', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('squad_tours', sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()))
```
### 2.2 Миграция данных
В той же миграции:
```python
def upgrade():
    # После добавления колонок
    # Копируем текущие значения из Squad в соответствующие SquadTour
    op.execute("""
        UPDATE squad_tours st
        SET budget = s.budget,
            replacements = s.replacements
        FROM squads s
        WHERE st.squad_id = s.id
    """)
```
### 2.3 Удалить поля из Squad (в отдельной миграции)
Создать вторую миграцию после проверки:
```python
# alembic/versions/xxx_remove_redundant_fields_from_squad.py
def upgrade():
    # Удаляем m2m таблицы текущего состава
    op.drop_table('squad_players_association')
    op.drop_table('squad_bench_players_association')
    
    # Удаляем колонки
    op.drop_column('squads', 'budget')
    op.drop_column('squads', 'replacements')
    op.drop_column('squads', 'points')
    op.drop_column('squads', 'penalty_points')
    op.drop_column('squads', 'captain_id')
    op.drop_column('squads', 'vice_captain_id')
    op.drop_column('squads', 'next_tour_penalty_points')
```
## Этап 3: Обновление моделей
### 3.1 Обновить app/squads/models.py
**Squad:**
* Удалить поля: budget, replacements, points, penalty_points, captain_id, vice_captain_id, next_tour_penalty_points
* Удалить relationships: current_main_players, current_bench_players
* Удалить методы: calculate_players_cost, validate_players, count_different_players, calculate_points
* Оставить: id, name, user_id, league_id, fav_team_id, relationships (user, league, fav_team, tour_history)
**SquadTour:**
* Добавить поля: budget: int, replacements: int, is_finalized: bool, created_at: datetime
* Перенести методы валидации из Squad в SquadService
### 3.2 Добавить хелперы в SquadService
```python
class SquadService:
    @classmethod
    async def get_squad_tour_for_tour(cls, squad_id: int, tour_id: int) -> SquadTour:
        # Получить SquadTour для конкретного тура
        
    @classmethod
    async def get_current_squad_tour(cls, squad_id: int) -> SquadTour:
        # Получить SquadTour для текущего открытого тура
        
    @classmethod
    async def get_or_create_squad_tour(cls, squad_id: int, tour_id: int) -> SquadTour:
        # Получить или создать SquadTour
```
## Этап 4: Обновление схем API
### 4.1 Обновить app/squads/schemas.py
**SquadReadSchema:**
Убрать поля, которые теперь в SquadTour:
* budget → будет в отдельной схеме или через вложенный объект
* replacements
* points
* penalty_points
* next_tour_penalty_points
* captain_id, vice_captain_id
* main_players, bench_players
**Создать новую схему SquadWithCurrentTourSchema:**
```python
class SquadWithCurrentTourSchema(BaseModel):
    # Метаданные команды
    id: int
    name: str
    user_id: int
    username: str
    league_id: int
    fav_team_id: int
    
    # Состояние текущего тура
    current_tour: SquadTourDetailSchema
```
**Обновить SquadTourHistorySchema:**
```python
class SquadTourDetailSchema(BaseModel):
    tour_id: int
    tour_number: int
    
    # Финансы
    budget: int
    replacements: int
    
    # Состав
    captain_id: int
    vice_captain_id: int
    main_players: list[PlayerInSquadSchema]
    bench_players: list[PlayerInSquadSchema]
    
    # Очки
    points: int
    penalty_points: int
    used_boost: str | None
```
## Этап 5: Рефакторинг сервисов
### 5.1 create_squad (app/squads/services.py:26)
**Изменения:**
* Создать Squad только с метаданными (name, user_id, league_id, fav_team_id)
* Создать SquadTour для следующего тура со всеми полями:
    * budget = 100_000 - total_cost
    * replacements = 2
    * main_players, bench_players
    * captain_id, vice_captain_id
    * points = 0, penalty_points = 0
* Убрать логику с current_tour_id
* Убрать добавление в squad_players_association и squad_bench_players_association
### 5.2 replace_players (app/squads/services.py:646)
**Текущая логика:**
* Получает squad
* Работает с squad.budget, squad.replacements, squad.penalty_points
* Обновляет squad.current_main_players, squad.current_bench_players
* Синхронизирует с SquadTour
**Новая логика:**
* Получить squad
* Получить текущий открытый тур для лиги
* Получить SquadTour для этого тура (или создать если нет)
* Работать напрямую с squad_tour.budget, squad_tour.replacements, squad_tour.penalty_points
* Обновлять squad_tour.main_players, squad_tour.bench_players
* Убрать логику синхронизации
### 5.3 get_squad (app/squads/services.py)
**Изменения:**
* Получить Squad
* Получить текущий SquadTour
* Вернуть комбинированные данные
* Если SquadTour нет (команда создана но тур не начался) - вернуть данные из последнего SquadTour или дефолтные значения
### 5.4 calculate_squad_points (app/squads/services.py:688)
**Изменения:**
* Вместо обновления squad.points обновлять squad_tour.points для конкретного тура
* Убрать синхронизацию между Squad и SquadTour
### 5.5 finalize_squad_tours (app/squads/services.py:1034)
**Изменения:**
* Найти все SquadTour для завершенного тура
* Пометить is_finalized = True
* Создать SquadTour для следующего тура, скопировав:
    * main_players, bench_players, captain_id, vice_captain_id
    * budget (рассчитать: 100_000 - стоимость игроков)
    * replacements = 2
    * penalty_points = squad_tour.penalty_points (если были накоплены для след тура)
    * points = 0
### 5.6 get_leaderboard (app/squads/services.py:836)
**Изменения:**
* Для любого тура (текущего или исторического) работать одинаково
* Запрос: `SELECT * FROM squad_tours WHERE tour_id = X`
* Убрать разделение логики на current/historical
* Упростить запросы
### 5.7 get_leaderboard_by_fav_team (app/squads/services.py:1314)
**Изменения:**
* Аналогично get_leaderboard
* Фильтр через JOIN: `squad_tours JOIN squads ON fav_team_id = X`
### 5.8 get_squad_tour_history_with_players (app/squads/services.py:1236)
**Изменения:**
* Минимальные изменения
* Добавить budget и replacements в вывод
## Этап 6: Обновление роутеров
### 6.1 GET /api/squads/get_squad_{squad_id} (app/squads/router.py)
**Изменения:**
* Получить Squad
* Определить текущий открытый тур
* Получить SquadTour для этого тура
* Вернуть SquadWithCurrentTourSchema
### 6.2 PUT /api/squads/replace_players_{squad_id} (app/squads/router.py)
**Изменения:**
* Передать tour_id в метод replace_players (определить из текущего тура)
* Обновить response schema
### 6.3 GET /api/squads/get_replacement_info (app/squads/router.py)
**Изменения:**
* Получить текущий SquadTour
* Вернуть squad_tour.budget и squad_tour.replacements
## Этап 7: Обновление связанных модулей
### 7.1 Custom Leagues
Файлы:
* app/custom_leagues/user_league/services.py
* app/custom_leagues/commercial_league/services.py
* app/custom_leagues/club_league/services.py
**Изменения:**
* Обновить get_leaderboard методы
* Убедиться что используется SquadTour для получения очков
### 7.2 Tours finalization
Файл: app/tours/services.py
**Изменения:**
* При финализации тура вызывать SquadService.finalize_squad_tours
* Убедиться что создаются новые SquadTour для следующего тура
## Этап 8: Тестирование
### 8.1 Unit тесты
* Создание команды
* Трансферы (бесплатные и платные)
* Подсчет штрафов
* Финализация тура
* Создание SquadTour для следующего тура
### 8.2 Integration тесты
* Полный цикл: создание → трансферы → финализация → новый тур
* Лидерборды для текущего и исторических туров
* Просмотр истории команды
### 8.3 Ручное тестирование
* Создать команду
* Сделать несколько трансферов
* Проверить штрафы
* Проверить лидерборды
* Дождаться финализации тура
* Проверить создание SquadTour для нового тура
## Этап 9: Деплой
### 9.1 Подготовка
* Создать backup БД
* Протестировать миграции на копии продакшн БД
* Подготовить rollback план
### 9.2 Деплой в production
* Остановить приложение (maintenance mode)
* Запустить миграции:
    1. Добавление полей в SquadTour
    2. Миграция данных
    3. Удаление полей из Squad
* Задеплоить новый код
* Запустить приложение
* Проверить основные флоу
### 9.3 Мониторинг
* Проверить логи на ошибки
* Проверить что endpoints работают
* Проверить что лидерборды показывают правильные данные
## Этап 10: Cleanup
### 10.1 Удалить мертвый код
* Удалить неиспользуемые методы из Squad модели
* Удалить старые схемы если не используются
* Удалить ссылки на current_tour_id, next_tour_penalty_points
### 10.2 Обновить документацию
* Обновить API docs
* Обновить README если есть описание архитектуры
* Добавить комментарии к новой логике
# Риски и митигация
## Риск: Потеря данных при миграции
**Митигация:**
* Тестировать миграцию на копии БД
* Создать backup перед продакшн миграцией
* Подготовить rollback скрипт
## Риск: Downtime при деплое
**Митигация:**
* Планировать деплой в низкую активность
* Подготовить maintenance page
* Протестировать миграцию локально чтобы знать время выполнения
## Риск: Баги в новой логике
**Митигация:**
* Тщательное тестирование
* Постепенный rollout (если возможно)
* Мониторинг после деплоя
* Возможность быстрого rollback
## Риск: Несовместимость с фронтендом
**Митигация:**
* Координация с фронтенд командой
* Версионирование API если нужно
* Backwards compatibility период если возможно
# Оценка времени
* Этап 1 (Анализ): 2-3 часа
* Этап 2 (Миграции БД): 2-3 часа
* Этап 3 (Модели): 1-2 часа
* Этап 4 (Схемы): 1-2 часа
* Этап 5 (Сервисы): 4-6 часов
* Этап 6 (Роутеры): 2-3 часа
* Этап 7 (Связанные модули): 2-3 часа
* Этап 8 (Тестирование): 3-4 часа
* Этап 9 (Деплой): 1-2 часа
* Этап 10 (Cleanup): 1-2 часа
**ИТОГО: 19-30 часов работы**
# Альтернативные подходы
## Вариант 1: Постепенная миграция
* Сначала добавить поля в SquadTour
* Дублировать запись в оба места
* Постепенно переводить код на SquadTour
* В конце удалить из Squad
**Плюсы:** Меньше риска
**Минусы:** Дольше, больше промежуточного кода
## Вариант 2: Feature flag
* Реализовать обе версии
* Использовать feature flag для переключения
* Постепенно включать новую версию
**Плюсы:** Можно быстро откатиться
**Минусы:** Сложность поддержки двух версий
# Рекомендация
Рекомендую **основной подход** из плана - единовременный рефакторинг с тщательной подготовкой и тестированием. Это чище и быстрее в долгосрочной перспективе.