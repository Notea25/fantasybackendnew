logger = logging.getLogger(__name__)

async def get_current_user(request: Request) -> User:
    """
    Зависимость для получения текущего пользователя.
    Ожидает данные в теле запроса в формате query string.
    """
    try:
        # Получаем сырые данные из тела запроса
        init_data = await request.body()
        init_data_str = init_data.decode("utf-8")

        logger.debug(f"Received init data for current user: {init_data_str}")

        # Валидируем данные
        data = validate_telegram_data(init_data_str)
        user_data = data.get("user", {})

        if not user_data or "id" not in user_data:
            logger.warning("User data is missing or invalid")
            raise ValueError("invalid user data")

        # Ищем пользователя в базе
        user = await UserService.find_one_or_none(id=int(user_data["id"]))

        # Если пользователь не найден, создаём его
        if not user:
            logger.info(f"Creating new user: {user_data['id']}")
            user = await UserService.add_one(
                id=int(user_data["id"]),
                username=user_data.get("username"),
                first_name=user_data.get("first_name"),
                last_name=user_data.get("last_name"),
                photo_url=user_data.get("photo_url", "").replace("\\/", "/")
            )

        return user

    except ValueError as e:
        logger.error(f"Validation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to get current user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )