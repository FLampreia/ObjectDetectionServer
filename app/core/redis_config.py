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


async def revoke_session(session_id: str):
    await redis_client.set(
        f"revoked:session:{session_id}",
        "true",
        ex=60 * 60 * 24 * config.REFRESH_TOKEN_EXPIRE_DAYS
    )

async def is_session_revoked(session_id: str) -> bool:
    return await redis_client.exists(f"revoked:session:{session_id}") > 0