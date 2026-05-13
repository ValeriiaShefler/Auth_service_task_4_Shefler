import redis
from app.config import settings

# подключение к Redis серверу
redis_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
    decode_responses=True
)

#[ранение недействительных токенов в Redis
class TokenBlacklist:
   #класс для управления черным списком токенов через Redis
   #использует Singleton через статические методы
   #токены хранятся с автоматическим истечением времени жизни, чтобы очищать память
    @staticmethod
    def add_to_blacklist(jti: str, expires_in: int) -> bool:
        #добавляет токен в черный список по его идентификатору и времени жизни, а возвращаетуспешность эьой операции
        #токен хранится только сколько ему осталось жить
        try:
            redis_client.setex(f"blacklist:{jti}", expires_in, "revoked")
            return True
        except Exception:
            return False
    
    @staticmethod
    def is_blacklisted(jti: str) -> bool:
        # проверка есть ли токен в черном списке
        return redis_client.exists(f"blacklist:{jti}") > 0
    
    @staticmethod
    def add_active_refresh_token(user_id: int, jti: str, expires_in: int) -> bool:
        # добавляет refresh токен в список активных для пользователя
        try:
            redis_client.setex(f"refresh:{user_id}:{jti}", expires_in, "active")
            return True
        except Exception:
            return False
    
    @staticmethod
    def remove_user_refresh_tokens(user_id: int) -> None:
        # удаляет все ферфреш токены пользователя
        pattern = f"refresh:{user_id}:*"
        keys = redis_client.keys(pattern)
        if keys:
            redis_client.delete(*keys)
    
    @staticmethod
    def is_refresh_token_active(user_id: int, jti: str) -> bool:
        #проверяет активность рефреш токена
        return redis_client.exists(f"refresh:{user_id}:{jti}") > 0


token_blacklist = TokenBlacklist()