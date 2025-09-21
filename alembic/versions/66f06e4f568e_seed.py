"""seed

Revision ID: 66f06e4f568e
Revises: 86ac78290ca0
Create Date: 2025-09-08 22:55:33.461143

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import column, table

# revision identifiers, used by Alembic.
revision: str = '66f06e4f568e'
down_revision: Union[str, Sequence[str], None] = '86ac78290ca0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


positions_table = table('positions',
    column('id', sa.Integer),
    column('name', sa.String)
)

sport_types_table = table('sport_types',
    column('id', sa.Integer),
    column('name', sa.String)
)

competitions_table = table('competitions',
    column('id', sa.String),
    column('name', sa.String),
    column('sport_type_id', sa.Integer)
)

clubs_table = table('clubs',
    column('id', sa.String),
    column('name', sa.String),
    column('competition_id', sa.String)
)

players_table = table('players',
    column('id', sa.String),
    column('name', sa.String),
    column('position_id', sa.Integer),
    column('age', sa.Integer),
    column('height', sa.Integer),
    column('market_value', sa.Integer),
    column('club_id', sa.String),
    column('points', sa.Integer),
    column('sport_type_id', sa.Integer),
    column('appearances', sa.Integer),
    column('goals', sa.Integer),
    column('assists', sa.Integer),
    column('yellow_cards', sa.Integer),
    column('red_cards', sa.Integer),
    column('minutes_played', sa.Integer)
)

def upgrade():
    op.execute('DELETE FROM positions')
    op.execute('DELETE FROM sport_types')
    op.execute('DELETE FROM players')
    op.execute('DELETE FROM competitions')
    op.execute('DELETE FROM clubs')
    op.execute('DELETE FROM players')

    op.bulk_insert(positions_table, [
        {'id': 1, 'name': 'Goalkeeper'},
        {'id': 2, 'name': 'Defender'},
        {'id': 3, 'name': 'Midfielder'},
        {'id': 4, 'name': 'Striker'},
        {'id': 5, 'name': 'Forward'},
        {'id': 6, 'name': 'Winger'}
    ])

    op.bulk_insert(sport_types_table, [
        {'id': 1, 'name': 'Football'},
        {'id': 2, 'name': 'Basketball'},
        {'id': 3, 'name': 'Hockey'},
        {'id': 4, 'name': 'Rugby'}
    ])

    op.bulk_insert(competitions_table, [
        {'id': 'WER1', 'name': 'Vysheyshaya Liga', 'sport_type_id': 1},
        {'id': 'WER2', 'name': 'Pershaya Liga', 'sport_type_id': 1},
    ])


    clubs_data = [
        {"id": "10694", "name": "FC Gomel", "competition_id": "WER1"},
        {"id": "1180", "name": "Dinamo Minsk", "competition_id": "WER1"},
        {"id": "118446", "name": "BATE 2 Borisov", "competition_id": "WER2"},
        {"id": "118448", "name": "ABFF U19", "competition_id": "WER2"},
        {"id": "14178", "name": "Neman Grodno", "competition_id": "WER1"},
        {"id": "17224", "name": "FK Smorgon", "competition_id": "WER1"},
        {"id": "17959", "name": "FC Vitebsk", "competition_id": "WER1"},
        {"id": "23664", "name": "FK Minsk", "competition_id": "WER1"},
        {"id": "24009", "name": "FC Baranovichi", "competition_id": "WER2"},
        {"id": "24015", "name": "FC Molodechno", "competition_id": "WER1"},
        {"id": "24174", "name": "FK Lida", "competition_id": "WER2"},
        {"id": "24175", "name": "FC Slonim 2017", "competition_id": "WER2"},
        {"id": "24177", "name": "Volna Pinsk", "competition_id": "WER2"},
        {"id": "27238", "name": "FK Slutsk", "competition_id": "WER1"},
        {"id": "32474", "name": "FK Osipovichi", "competition_id": "WER2"},
        {"id": "32976", "name": "FC Orsha", "competition_id": "WER2"},
        {"id": "32978", "name": "Lokomotiv Gomel", "competition_id": "WER2"},
        {"id": "32985", "name": "Dinamo- BGUFK Minsk", "competition_id": "WER2"},
        {"id": "36596", "name": "ML Vitebsk", "competition_id": "WER1"},
        {"id": "36755", "name": "Isloch Minsk Region", "competition_id": "WER1"},
        {"id": "3886", "name": "Belshina Bobruisk", "competition_id": "WER2"},
        {"id": "4394", "name": "Dnepr Mogilev", "competition_id": "WER2"},
        {"id": "6131", "name": "Dynamo Brest", "competition_id": "WER1"},
        {"id": "6423", "name": "Slavia Mozyr", "competition_id": "WER1"},
        {"id": "713", "name": "BATE Borisov", "competition_id": "WER1"},
        {"id": "72822", "name": "Arsenal Dzerzhinsk", "competition_id": "WER1"},
        {"id": "7964", "name": "Torpedo-BelAZ Zhodino", "competition_id": "WER1"},
        {"id": "80108", "name": "Bumprom Gomel", "competition_id": "WER2"},
        {"id": "81228", "name": "FC Ostrovets", "competition_id": "WER2"},
        {"id": "81367", "name": "FC Minsk 2", "competition_id": "WER2"},
        {"id": "8563", "name": "Naftan Novopolotsk", "competition_id": "WER1"},
        {"id": "87637", "name": "FC Gomel 2", "competition_id": "WER2"},
        {"id": "90685", "name": "Niva Dolbizno", "competition_id": "WER2"},
        {"id": "98588", "name": "Uni X Labs Minsk", "competition_id": "WER2"}
    ]

    op.bulk_insert(clubs_table, clubs_data)

    players_data = [
        {'id': '1003307', 'name': 'Egor Bozhko', 'position_id': 2, 'age': 19, 'height': 180, 'market_value': 4950, 'club_id': '36596', 'appearances': 1, 'goals': 0, 'assists': 0, 'minutes_played': 3, 'points': 1, 'red_cards': 0, 'yellow_cards': 0, 'sport_type_id': 1},
        {'id': '1118395', 'name': 'Pavel Kotlyarov', 'position_id': 3, 'age': 20, 'height': 180, 'market_value': 9723, 'club_id': '6423', 'appearances': 1, 'goals': 0, 'assists': 0, 'minutes_played': 1, 'points': 1, 'red_cards': 0, 'yellow_cards': 0, 'sport_type_id': 1},
        {'id': '1123815', 'name': 'Vladimir Tonkevich', 'position_id': 2, 'age': 20, 'height': 180, 'market_value': 5090, 'club_id': '17224', 'appearances': 4, 'goals': 0, 'assists': 0, 'minutes_played': 146, 'points': 5, 'red_cards': 0, 'yellow_cards': 1, 'sport_type_id': 1},
        {'id': '1156564', 'name': 'Artur Nazarenko', 'position_id': 3, 'age': 21, 'height': 180, 'market_value': 9955, 'club_id': '14178', 'appearances': 2, 'goals': 0, 'assists': 0, 'minutes_played': 49, 'points': 2, 'red_cards': 0, 'yellow_cards': 0, 'sport_type_id': 1},
        {'id': '116881', 'name': 'Andrey Zaleskiy', 'position_id': 2, 'age': 34, 'height': 180, 'market_value': 5685, 'club_id': '36755', 'appearances': 1, 'goals': 0, 'assists': 0, 'minutes_played': 19, 'points': 1, 'red_cards': 0, 'yellow_cards': 0, 'sport_type_id': 1},
        {'id': '118462', 'name': 'Aleksandr Makas', 'position_id': 4, 'age': 33, 'height': 180, 'market_value': 13150, 'club_id': '23664', 'appearances': 4, 'goals': 2, 'assists': 0, 'minutes_played': 177, 'points': 15, 'red_cards': 0, 'yellow_cards': 1, 'sport_type_id': 1},
        {'id': '1252570', 'name': 'Ilya Brelunenko', 'position_id': 2, 'age': 19, 'height': 180, 'market_value': 5721, 'club_id': '118446', 'appearances': 0, 'goals': 0, 'assists': 0, 'minutes_played': 0, 'points': 0, 'red_cards': 0, 'yellow_cards': 0, 'sport_type_id': 1},
        {'id': '1252579', 'name': 'Egor Chuevskiy', 'position_id': 2, 'age': 19, 'height': 180, 'market_value': 6907, 'club_id': '118446', 'appearances': 0, 'goals': 0, 'assists': 0, 'minutes_played': 0, 'points': 0, 'red_cards': 0, 'yellow_cards': 0, 'sport_type_id': 1},
        {'id': '1252585', 'name': 'Zakhar Shevchik', 'position_id': 2, 'age': 18, 'height': 190, 'market_value': 6394, 'club_id': '118446', 'appearances': 0, 'goals': 0, 'assists': 0, 'minutes_played': 0, 'points': 0, 'red_cards': 0, 'yellow_cards': 0, 'sport_type_id': 1},
        {'id': '174049', 'name': 'Pavel Okhremchuk', 'position_id': 1, 'age': 31, 'height': 190, 'market_value': 5740, 'club_id': '24015', 'appearances': 0, 'goals': 0, 'assists': 0, 'minutes_played': 0, 'points': 0, 'red_cards': 0, 'yellow_cards': 0, 'sport_type_id': 1},
        {'id': '187020', 'name': 'Mikhail Bashilov', 'position_id': 3, 'age': 32, 'height': 180, 'market_value': 5247, 'club_id': '17959', 'appearances': 4, 'goals': 1, 'assists': 0, 'minutes_played': 360, 'points': 14, 'red_cards': 0, 'yellow_cards': 1, 'sport_type_id': 1},
        {'id': '187532', 'name': 'Aleksandr Selyava', 'position_id': 3, 'age': 32, 'height': 180, 'market_value': 9668, 'club_id': '7964', 'appearances': 4, 'goals': 0, 'assists': 0, 'minutes_played': 296, 'points': 8, 'red_cards': 0, 'yellow_cards': 0, 'sport_type_id': 1},
        {'id': '351726', 'name': 'Aleksey Butarevich', 'position_id': 3, 'age': 28, 'height': 180, 'market_value': 7188, 'club_id': '7964', 'appearances': 3, 'goals': 0, 'assists': 0, 'minutes_played': 228, 'points': 6, 'red_cards': 0, 'yellow_cards': 0, 'sport_type_id': 1},
        {'id': '399894', 'name': 'Aleksandr Ksenofontov', 'position_id': 3, 'age': 25, 'height': 180, 'market_value': 7800, 'club_id': '17959', 'appearances': 4, 'goals': 1, 'assists': 0, 'minutes_played': 265, 'points': 13, 'red_cards': 0, 'yellow_cards': 0, 'sport_type_id': 1},
        {'id': '409662', 'name': 'Aleksandr Anufriev', 'position_id': 3, 'age': 29, 'height': 180, 'market_value': 7707, 'club_id': '713', 'appearances': 4, 'goals': 1, 'assists': 0, 'minutes_played': 204, 'points': 11, 'red_cards': 0, 'yellow_cards': 1, 'sport_type_id': 1},
        {'id': '470256', 'name': 'Aleksandr Svirepa', 'position_id': 3, 'age': 25, 'height': 180, 'market_value': 7109, 'club_id': '713', 'appearances': 4, 'goals': 0, 'assists': 0, 'minutes_played': 263, 'points': 8, 'red_cards': 0, 'yellow_cards': 0, 'sport_type_id': 1},
        {'id': '470265', 'name': 'Kirill Kirilenko', 'position_id': 3, 'age': 24, 'height': 180, 'market_value': 9718, 'club_id': '72822', 'appearances': 4, 'goals': 2, 'assists': 1, 'minutes_played': 332, 'points': 21, 'red_cards': 0, 'yellow_cards': 1, 'sport_type_id': 1},
        {'id': '510898', 'name': 'Nikita Vlasenko', 'position_id': 2, 'age': 24, 'height': 190, 'market_value': 5716, 'club_id': '72822', 'appearances': 3, 'goals': 0, 'assists': 0, 'minutes_played': 209, 'points': 5, 'red_cards': 0, 'yellow_cards': 1, 'sport_type_id': 1},
        {'id': '533784', 'name': 'Yaroslav Oreshkevich', 'position_id': 3, 'age': 24, 'height': 180, 'market_value': 9451, 'club_id': '72822', 'appearances': 3, 'goals': 0, 'assists': 0, 'minutes_played': 166, 'points': 5, 'red_cards': 0, 'yellow_cards': 0, 'sport_type_id': 1},
        {'id': '538389', 'name': 'Denis Sadovskiy', 'position_id': 1, 'age': 27, 'height': 190, 'market_value': 4592, 'club_id': '24015', 'appearances': 4, 'goals': 0, 'assists': 0, 'minutes_played': 360, 'points': 10, 'red_cards': 0, 'yellow_cards': 0, 'sport_type_id': 1},
        {'id': '541901', 'name': 'Igor Malashchitskiy', 'position_id': 1, 'age': 22, 'height': 190, 'market_value': 4492, 'club_id': '7964', 'appearances': 0, 'goals': 0, 'assists': 0, 'minutes_played': 0, 'points': 0, 'red_cards': 0, 'yellow_cards': 0, 'sport_type_id': 1},
        {'id': '546976', 'name': 'Stanislav Letsko', 'position_id': 1, 'age': 24, 'height': 180, 'market_value': 5655, 'club_id': '24177', 'appearances': 3, 'goals': 0, 'assists': 0, 'minutes_played': 270, 'points': 7, 'red_cards': 0, 'yellow_cards': 0, 'sport_type_id': 1},
        {'id': '546979', 'name': 'Oleg Nikiforenko', 'position_id': 3, 'age': 24, 'height': 180, 'market_value': 5972, 'club_id': '36596', 'appearances': 1, 'goals': 0, 'assists': 0, 'minutes_played': 39, 'points': 1, 'red_cards': 0, 'yellow_cards': 0, 'sport_type_id': 1},
        {'id': '546982', 'name': 'Roman Davyskiba', 'position_id': 3, 'age': 24, 'height': 180, 'market_value': 8055, 'club_id': '10694', 'appearances': 1, 'goals': 0, 'assists': 0, 'minutes_played': 68, 'points': 2, 'red_cards': 0, 'yellow_cards': 0, 'sport_type_id': 1},
        {'id': '550696', 'name': 'Ibrahim Kargbo Jr.', 'position_id': 4, 'age': 25, 'height': 190, 'market_value': 9980, 'club_id': '713', 'appearances': 3, 'goals': 0, 'assists': 1, 'minutes_played': 146, 'points': 8, 'red_cards': 0, 'yellow_cards': 0, 'sport_type_id': 1},
        {'id': '553388', 'name': 'Dmitriy Nekrashevich', 'position_id': 3, 'age': 23, 'height': 180, 'market_value': 10556, 'club_id': '24009', 'appearances': 0, 'goals': 0, 'assists': 0, 'minutes_played': 0, 'points': 0, 'red_cards': 0, 'yellow_cards': 0, 'sport_type_id': 1},
        {'id': '565170', 'name': 'Vladislav Rusenchik', 'position_id': 3, 'age': 23, 'height': 190, 'market_value': 10360, 'club_id': '713', 'appearances': 3, 'goals': 0, 'assists': 0, 'minutes_played': 85, 'points': 4, 'red_cards': 0, 'yellow_cards': 0, 'sport_type_id': 1},
        {'id': '569432', 'name': 'Dusan Bakic', 'position_id': 4, 'age': 26, 'height': 190, 'market_value': 10556, 'club_id': '1180', 'appearances': 1, 'goals': 0, 'assists': 0, 'minutes_played': 90, 'points': 2, 'red_cards': 0, 'yellow_cards': 0, 'sport_type_id': 1},
        {'id': '59373', 'name': 'Oleg Veretilo', 'position_id': 2, 'age': 36, 'height': 180, 'market_value': 5406, 'club_id': '36755', 'appearances': 4, 'goals': 0, 'assists': 0, 'minutes_played': 296, 'points': 8, 'red_cards': 0, 'yellow_cards': 0, 'sport_type_id': 1},
        {'id': '602695', 'name': 'Gleb Zherdev', 'position_id': 3, 'age': 24, 'height': 180, 'market_value': 7121, 'club_id': '36596', 'appearances': 0, 'goals': 0, 'assists': 0, 'minutes_played': 0, 'points': 0, 'red_cards': 0, 'yellow_cards': 0, 'sport_type_id': 1},
        {'id': '607571', 'name': 'Ruslan Lisakovich', 'position_id': 3, 'age': 23, 'height': 170, 'market_value': 5565, 'club_id': '36596', 'appearances': 4, 'goals': 2, 'assists': 1, 'minutes_played': 360, 'points': 23, 'red_cards': 0, 'yellow_cards': 0, 'sport_type_id': 1},
        {'id': '625124', 'name': 'Sergey Sazonchik', 'position_id': 3, 'age': 24, 'height': 180, 'market_value': 7784, 'club_id': '6423', 'appearances': 1, 'goals': 0, 'assists': 0, 'minutes_played': 1, 'points': 1, 'red_cards': 0, 'yellow_cards': 0, 'sport_type_id': 1},
        {'id': '659570', 'name': 'Vladislav Solanovich', 'position_id': 2, 'age': 25, 'height': 180, 'market_value': 5973, 'club_id': '3886', 'appearances': 2, 'goals': 0, 'assists': 0, 'minutes_played': 180, 'points': 5, 'red_cards': 0, 'yellow_cards': 0, 'sport_type_id': 1},
        {'id': '661161', 'name': 'Arsen Azatov', 'position_id': 2, 'age': 21, 'height': 180, 'market_value': 6727, 'club_id': '24015', 'appearances': 4, 'goals': 0, 'assists': 0, 'minutes_played': 348, 'points': 9, 'red_cards': 0, 'yellow_cards': 0, 'sport_type_id': 1},
        {'id': '662058', 'name': 'Andrey Rum', 'position_id': 2, 'age': 23, 'height': 180, 'market_value': 6964, 'club_id': '27238', 'appearances': 5, 'goals': 0, 'assists': 1, 'minutes_played': 261, 'points': 11, 'red_cards': 0, 'yellow_cards': 1, 'sport_type_id': 1},
        {'id': '67855', 'name': 'Sergey Politevich', 'position_id': 2, 'age': 35, 'height': 190, 'market_value': 5063, 'club_id': '7964', 'appearances': 1, 'goals': 0, 'assists': 0, 'minutes_played': 90, 'points': 2, 'red_cards': 0, 'yellow_cards': 0, 'sport_type_id': 1},
        {'id': '684383', 'name': 'Yuriy Klochkov', 'position_id': 3, 'age': 26, 'height': 180, 'market_value': 5239, 'club_id': '14178', 'appearances': 3, 'goals': 1, 'assists': 0, 'minutes_played': 99, 'points': 9, 'red_cards': 0, 'yellow_cards': 0, 'sport_type_id': 1},
        {'id': '686339', 'name': 'Daniil Polyanskiy', 'position_id': 1, 'age': 24, 'height': 190, 'market_value': 4252, 'club_id': '72822', 'appearances': 0, 'goals': 0, 'assists': 0, 'minutes_played': 0, 'points': 0, 'red_cards': 0, 'yellow_cards': 0, 'sport_type_id': 1},
        {'id': '687590', 'name': 'Dmitriy Girs', 'position_id': 3, 'age': 27, 'height': 180, 'market_value': 9122, 'club_id': '17959', 'appearances': 4, 'goals': 0, 'assists': 0, 'minutes_played': 212, 'points': 7, 'red_cards': 0, 'yellow_cards': 0, 'sport_type_id': 1},
        {'id': '730974', 'name': 'Artur Chuduk', 'position_id': 2, 'age': 28, 'height': 190, 'market_value': 4753, 'club_id': '36596', 'appearances': 0, 'goals': 0, 'assists': 0, 'minutes_played': 0, 'points': 0, 'red_cards': 0, 'yellow_cards': 0, 'sport_type_id': 1},
        {'id': '740550', 'name': 'Vladislav Davydov', 'position_id': 2, 'age': 25, 'height': 180, 'market_value': 6675, 'club_id': '6423', 'appearances': 3, 'goals': 0, 'assists': 1, 'minutes_played': 138, 'points': 8, 'red_cards': 0, 'yellow_cards': 0, 'sport_type_id': 1},
        {'id': '740753', 'name': 'Gleb Vershinin', 'position_id': 3, 'age': 23, 'height': 190, 'market_value': 10229, 'club_id': '4394', 'appearances': 3, 'goals': 0, 'assists': 0, 'minutes_played': 215, 'points': 5, 'red_cards': 0, 'yellow_cards': 1, 'sport_type_id': 1},
        {'id': '747240', 'name': 'Andrey Kabyshev', 'position_id': 3, 'age': 21, 'height': 180, 'market_value': 10941, 'club_id': '4394', 'appearances': 2, 'goals': 0, 'assists': 0, 'minutes_played': 93, 'points': 3, 'red_cards': 0, 'yellow_cards': 0, 'sport_type_id': 1},
        {'id': '755709', 'name': 'Aleksandr Puzach', 'position_id': 3, 'age': 29, 'height': 180, 'market_value': 9842, 'club_id': '24177', 'appearances': 2, 'goals': 0, 'assists': 0, 'minutes_played': 79, 'points': 3, 'red_cards': 0, 'yellow_cards': 0, 'sport_type_id': 1},
        {'id': '768911', 'name': 'Ivan Sanko', 'position_id': 1, 'age': 26, 'height': 190, 'market_value': 5187, 'club_id': '72822', 'appearances': 0, 'goals': 0, 'assists': 0, 'minutes_played': 0, 'points': 0, 'red_cards': 0, 'yellow_cards': 0, 'sport_type_id': 1},
        {'id': '790641', 'name': 'Aleksandr Naumovich', 'position_id': 1, 'age': 23, 'height': 190, 'market_value': 4903, 'club_id': '8563', 'appearances': 0, 'goals': 0, 'assists': 0, 'minutes_played': 0, 'points': 0, 'red_cards': 0, 'yellow_cards': 0, 'sport_type_id': 1},
        {'id': '811244', 'name': 'Igor Monich', 'position_id': 4, 'age': 25, 'height': 180, 'market_value': 7374, 'club_id': '24015', 'appearances': 3, 'goals': 0, 'assists': 0, 'minutes_played': 41, 'points': 3, 'red_cards': 0, 'yellow_cards': 0, 'sport_type_id': 1},
        {'id': '818396', 'name': 'Kirill Tsepenkov', 'position_id': 4, 'age': 20, 'height': 170, 'market_value': 9759, 'club_id': '1180', 'appearances': 1, 'goals': 0, 'assists': 0, 'minutes_played': 14, 'points': 1, 'red_cards': 0, 'yellow_cards': 0, 'sport_type_id': 1},
        {'id': '826681', 'name': 'Andrey Kren', 'position_id': 3, 'age': 21, 'height': 170, 'market_value': 5078, 'club_id': '27238', 'appearances': 3, 'goals': 0, 'assists': 0, 'minutes_played': 131, 'points': 5, 'red_cards': 0, 'yellow_cards': 0, 'sport_type_id': 1},
        {'id': '858396', 'name': 'Miras Kobeev', 'position_id': 3, 'age': 20, 'height': 170, 'market_value': 10862, 'club_id': '36755', 'appearances': 4, 'goals': 0, 'assists': 0, 'minutes_played': 339, 'points': 9, 'red_cards': 0, 'yellow_cards': 0, 'sport_type_id': 1},
        {'id': '86269', 'name': 'Aleksandr Gutor', 'position_id': 1, 'age': 35, 'height': 190, 'market_value': 4382, 'club_id': '23664', 'appearances': 5, 'goals': 0, 'assists': 0, 'minutes_played': 450, 'points': 9, 'red_cards': 0, 'yellow_cards': 2, 'sport_type_id': 1},
        {'id': '864614', 'name': 'Kirill Volkov', 'position_id': 2, 'age': 19, 'height': 180, 'market_value': 5612, 'club_id': '72822', 'appearances': 1, 'goals': 0, 'assists': 0, 'minutes_played': 27, 'points': 1, 'red_cards': 0, 'yellow_cards': 0, 'sport_type_id': 1},
        {'id': '869529', 'name': 'Arthur Bougnone', 'position_id': 3, 'age': 24, 'height': 180, 'market_value': 9877, 'club_id': '27238', 'appearances': 4, 'goals': 1, 'assists': 0, 'minutes_played': 200, 'points': 12, 'red_cards': 0, 'yellow_cards': 0, 'sport_type_id': 1},
        {'id': '871940', 'name': 'Yamoussa Camara', 'position_id': 3, 'age': 24, 'height': 170, 'market_value': 8827, 'club_id': '8563', 'appearances': 4, 'goals': 0, 'assists': 1, 'minutes_played': 360, 'points': 14, 'red_cards': 0, 'yellow_cards': 1, 'sport_type_id': 1},
        {'id': '877135', 'name': 'Amantur Shamurzaev', 'position_id': 2, 'age': 25, 'height': 180, 'market_value': 4714, 'club_id': '14178', 'appearances': 3, 'goals': 0, 'assists': 0, 'minutes_played': 270, 'points': 7, 'red_cards': 0, 'yellow_cards': 0, 'sport_type_id': 1},
        {'id': '884519', 'name': 'Artem Drabatovich', 'position_id': 2, 'age': 21, 'height': 180, 'market_value': 4705, 'club_id': '8563', 'appearances': 4, 'goals': 0, 'assists': 1, 'minutes_played': 360, 'points': 15, 'red_cards': 0, 'yellow_cards': 0, 'sport_type_id': 1},
        {'id': '918054', 'name': 'Vadim Harutyunyan', 'position_id': 3, 'age': 19, 'height': 170, 'market_value': 8706, 'club_id': '72822', 'appearances': 4, 'goals': 0, 'assists': 0, 'minutes_played': 350, 'points': 9, 'red_cards': 0, 'yellow_cards': 0, 'sport_type_id': 1},
        {'id': '946386', 'name': 'Matvey Kovruk', 'position_id': 1, 'age': 20, 'height': 190, 'market_value': 4015, 'club_id': '27238', 'appearances': 0, 'goals': 0, 'assists': 0, 'minutes_played': 0, 'points': 0, 'red_cards': 0, 'yellow_cards': 0, 'sport_type_id': 1},
        {'id': '946680', 'name': 'Arseniy Ageev', 'position_id': 2, 'age': 20, 'height': 170, 'market_value': 4932, 'club_id': '7964', 'appearances': 0, 'goals': 0, 'assists': 0, 'minutes_played': 0, 'points': 0, 'red_cards': 0, 'yellow_cards': 0, 'sport_type_id': 1},
        {'id': '951642', 'name': 'Vladislav Melko', 'position_id': 2, 'age': 20, 'height': 180, 'market_value': 6130, 'club_id': '7964', 'appearances': 3, 'goals': 0, 'assists': 0, 'minutes_played': 243, 'points': 7, 'red_cards': 0, 'yellow_cards': 0, 'sport_type_id': 1},
        {'id': '981865', 'name': 'Dmitriy Denisenko', 'position_id': 3, 'age': 18, 'height': 190, 'market_value': 9473, 'club_id': '23664', 'appearances': 1, 'goals': 0, 'assists': 0, 'minutes_played': 45, 'points': 1, 'red_cards': 0, 'yellow_cards': 0, 'sport_type_id': 1},
        {'id': '992935', 'name': 'Vladislav Karpenya', 'position_id': 2, 'age': 24, 'height': 190, 'market_value': 4794, 'club_id': '24009', 'appearances': 0, 'goals': 0, 'assists': 0, 'minutes_played': 0, 'points': 0, 'red_cards': 0, 'yellow_cards': 0, 'sport_type_id': 1}
    ]

    op.bulk_insert(players_table, players_data)

def downgrade():
    op.execute('DELETE FROM sport_types')
    op.execute('DELETE FROM positions')
    op.execute('DELETE FROM competitions')
    op.execute('DELETE FROM clubs')
    op.execute('DELETE FROM players')
