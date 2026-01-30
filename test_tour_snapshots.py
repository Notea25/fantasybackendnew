"""
Тестовый скрипт для проверки логики исторических snapshots туров.

Этот скрипт демонстрирует, как должна работать логика:
1. Создание сквада в туре 1
2. Переход к туру 2 и изменение состава
3. Проверка, что история тура 1 не изменилась
"""

import asyncio
import sys
from pathlib import Path

# Добавляем путь к проекту
sys.path.insert(0, str(Path(__file__).parent))

from app.squads.services import SquadService
from app.database import async_session_maker
from sqlalchemy import select
from app.squads.models import Squad, SquadTour


async def test_tour_snapshots():
    """Тестирование логики snapshots туров."""
    
    print("\n" + "="*80)
    print("ТЕСТ: Историческая целостность snapshots туров")
    print("="*80 + "\n")
    
    # Параметры для теста (замените на реальные значения из вашей БД)
    TEST_SQUAD_ID = 1  # ID существующего сквада
    
    async with async_session_maker() as session:
        # 1. Получаем текущий сквад
        print("1. Загружаем тестовый сквад...")
        stmt = select(Squad).where(Squad.id == TEST_SQUAD_ID)
        result = await session.execute(stmt)
        squad = result.scalars().first()
        
        if not squad:
            print(f"❌ Сквад с ID {TEST_SQUAD_ID} не найден!")
            print("   Создайте сквад через API и обновите TEST_SQUAD_ID в скрипте.")
            return
        
        print(f"✅ Сквад загружен: {squad.name} (ID: {squad.id})")
        print(f"   Текущий тур: {squad.current_tour_id}")
        print(f"   Игроков в основе: {len(squad.current_main_players)}")
        print(f"   Игроков на скамейке: {len(squad.current_bench_players)}")
        
        # 2. Получаем историю туров
        print("\n2. Загружаем историю туров...")
        history = await SquadService.get_squad_tour_history_with_players(TEST_SQUAD_ID)
        
        if not history:
            print("⚠️  История туров пуста!")
            print("   Это нормально для нового сквада.")
            print("   Создайте несколько туров и сделайте трансферы для полноценного теста.")
            return
        
        print(f"✅ Найдено туров в истории: {len(history)}")
        
        # 3. Выводим информацию о каждом туре
        print("\n3. Детали истории туров:\n")
        
        for idx, tour_snapshot in enumerate(history, 1):
            print(f"   ┌─ Тур #{tour_snapshot['tour_number']} (ID: {tour_snapshot['tour_id']})")
            print(f"   │  Очки тура: {tour_snapshot['points']}")
            print(f"   │  Капитан ID: {tour_snapshot['captain_id']}")
            print(f"   │  Вице-капитан ID: {tour_snapshot['vice_captain_id']}")
            print(f"   │  Буст: {tour_snapshot['used_boost'] or 'нет'}")
            print(f"   │")
            print(f"   │  Основной состав ({len(tour_snapshot['main_players'])} игроков):")
            
            for player in tour_snapshot['main_players'][:3]:  # Показываем первых 3
                print(f"   │    • {player['name']} ({player['position']}) - "
                      f"{player['tour_points']} очков за тур")
            
            if len(tour_snapshot['main_players']) > 3:
                print(f"   │    ... и еще {len(tour_snapshot['main_players']) - 3} игроков")
            
            print(f"   │")
            print(f"   │  Скамейка ({len(tour_snapshot['bench_players'])} игроков):")
            
            for player in tour_snapshot['bench_players'][:2]:  # Показываем первых 2
                print(f"   │    • {player['name']} ({player['position']}) - "
                      f"{player['tour_points']} очков за тур")
            
            if idx < len(history):
                print(f"   │")
            else:
                print(f"   └─")
        
        # 4. Проверяем независимость туров
        print("\n4. Проверка независимости туров:")
        
        if len(history) >= 2:
            tour1 = history[0]
            tour2 = history[1]
            
            tour1_player_ids = {p['id'] for p in tour1['main_players']}
            tour2_player_ids = {p['id'] for p in tour2['main_players']}
            
            if tour1_player_ids != tour2_player_ids:
                print(f"✅ Составы туров отличаются!")
                print(f"   Игроков только в Туре {tour1['tour_number']}: "
                      f"{len(tour1_player_ids - tour2_player_ids)}")
                print(f"   Игроков только в Туре {tour2['tour_number']}: "
                      f"{len(tour2_player_ids - tour1_player_ids)}")
                print(f"   Общих игроков: {len(tour1_player_ids & tour2_player_ids)}")
            else:
                print(f"⚠️  Составы туров идентичны.")
                print(f"   Это нормально, если не было трансферов между турами.")
        else:
            print(f"⚠️  Недостаточно туров для сравнения (найдено: {len(history)})")
        
        # 5. Проверяем текущий состав
        print("\n5. Сравнение с текущим составом:")
        
        current_player_ids = {p.id for p in squad.current_main_players}
        
        if history:
            last_tour = history[-1]
            last_tour_player_ids = {p['id'] for p in last_tour['main_players']}
            
            if current_player_ids == last_tour_player_ids:
                print(f"✅ Текущий состав совпадает с последним туром")
            else:
                print(f"⚠️  Текущий состав отличается от последнего тура!")
                print(f"   Это может означать, что были сделаны трансферы,")
                print(f"   но snapshot для нового тура еще не создан.")
        
        print("\n" + "="*80)
        print("ТЕСТ ЗАВЕРШЕН")
        print("="*80 + "\n")
        
        print("📋 Рекомендации для полноценного тестирования:")
        print("   1. Создайте сквад через API")
        print("   2. Дождитесь завершения тура (или смените current_tour_id вручную)")
        print("   3. Сделайте несколько трансферов")
        print("   4. Снова смените тур")
        print("   5. Запустите этот скрипт для проверки истории")
        print()


if __name__ == "__main__":
    try:
        asyncio.run(test_tour_snapshots())
    except KeyboardInterrupt:
        print("\n\nТест прерван пользователем")
    except Exception as e:
        print(f"\n❌ Ошибка при выполнении теста: {e}")
        import traceback
        traceback.print_exc()
