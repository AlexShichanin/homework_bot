class HTTPStatusError(Exception):
    """Ошибка статуса в get_api_answer."""
    pass


class ApiError(Exception):
    """Ошибка API в функции get_api_answer."""
    pass


class WerdictStatusError(Exception):
    """Ошибка status в функции parsre_status."""
    pass
