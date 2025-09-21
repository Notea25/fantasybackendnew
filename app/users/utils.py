import hashlib
import hmac
import json
import logging
import time
from urllib.parse import parse_qsl, unquote
from app.config import settings

logger = logging.getLogger(__name__)

def validate_telegram_data(init_data: str) -> dict:
    """
    Проверяет подлинность данных от Telegram Login Widget.
    Ожидает строку в формате query string.
    """
    logger.debug(f"Raw init data: {init_data}")

    # Парсим строку как query string
    pairs = parse_qsl(init_data, keep_blank_values=True)
    hash_val = None
    filtered = []

    for k, v in pairs:
        if k == "hash":
            hash_val = v
        else:
            filtered.append((k, v))

    if not hash_val:
        logger.warning("Hash is missing in init data")
        raise ValueError("hash missing")

    # Сортируем данные и формируем строку для проверки
    filtered.sort(key=lambda kv: kv[0])
    data_check_string = "\n".join(f"{k}={v}" for k, v in filtered)
    logger.debug(f"Data check string: {data_check_string}")

    # Вычисляем хеш с использованием секретного ключа
    secret_key = hmac.new(b"WebAppData", settings.TELEGRAM_BOT_TOKEN.encode("utf-8"), hashlib.sha256).digest()
    calc_hash = hmac.new(secret_key, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()
    logger.debug(f"Calculated hash: {calc_hash}")
    logger.debug(f"Received hash: {hash_val}")

    if not hmac.compare_digest(calc_hash, hash_val):
        logger.warning("Hash verification failed")
        raise ValueError("invalid signature")

    # Проверяем auth_date
    auth_date = None
    for k, v in filtered:
        if k == "auth_date":
            try:
                auth_date = int(v)
            except:
                pass

    if auth_date is None:
        logger.warning("auth_date is missing")
        raise ValueError("auth_date missing")

    now = int(time.time())
    if abs(now - auth_date) > 3600:  # 1 час
        logger.warning(f"Init data expired. Current time: {now}, auth_date: {auth_date}")
        raise ValueError("init data expired")

    # Преобразуем результат в словарь
    result = {k: v for k, v in filtered}

    # Парсим поле user если оно есть
    if "user" in result:
        try:
            result["user"] = json.loads(unquote(result["user"]))
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse user JSON: {e}")
            raise ValueError("invalid user data")

    return result
