from redis.asyncio import Redis

from app.exceptions.custom_exceptions import RedisNotAvailable
from app.core.config import config

redis_client = Redis(
    host=config.REDIS_HOST,
    port=config.REDIS_PORT,
    db=0,
    decode_responses=True
)

async def add_jti_to_blocklist(jti: str) -> None:

    await redis_client.set(
        name=jti,
        value="",
        ex=config.JTI_EXPIRY
    )

async def token_in_blocklist(jti: str) -> bool:

    jti = await redis_client.get(jti)

    return jti is not None

async def check_redis_connection():
    try:
        await redis_client.ping()
    except Exception as e:
        raise RedisNotAvailable()
