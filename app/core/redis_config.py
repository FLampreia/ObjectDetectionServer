from redis.asyncio import Redis

from app.exceptions.custom_exceptions import RedisNotAvailable
from app.core.config import config

token_blocklist = Redis(
    host=config.REDIS_HOST,
    port=config.REDIS_PORT,
    db=0
)

async def add_jti_to_blocklist(jti: str) -> None:

    await token_blocklist.set(
        name=jti,
        value="",
        ex=config.JTI_EXPIRY
    )

async def token_in_blocklist(jti: str) -> bool:

    jti = await token_blocklist.get(jti)

    return jti is not None

async def check_redis_connection():
    try:
        await token_blocklist.ping()
    except Exception as e:
        raise RedisNotAvailable()
