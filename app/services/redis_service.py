from app.core.config import config
from app.core.redis_config import redis_client
from app.exceptions.custom_exceptions import RedisNotAvailable
import math
import time


async def add_jti_to_blocklist(jti: str, expires_at: float | None = None) -> None:

    await redis_client.set(
        name=jti,
        value="",
        ex=max(1, math.ceil(expires_at - time.time())) if expires_at is not None else config.JTI_EXPIRY
    )


async def consume_refresh_token(jti: str, session_id: str, expires_at: float) -> bool:
    """Consume a refresh token once and revoke its session on detected reuse."""
    script = """
    if redis.call('EXISTS', KEYS[2]) == 1 then return 0 end
    if redis.call('EXISTS', KEYS[1]) == 1 then
        redis.call('SET', KEYS[2], 'true', 'EX', ARGV[2])
        return 0
    end
    redis.call('SET', KEYS[1], 'used', 'EX', ARGV[1])
    return 1
    """
    return bool(await redis_client.eval(
        script, 2, jti, f"revoked:session:{session_id}",
        max(1, math.ceil(expires_at - time.time())),
        60 * 60 * 24 * config.REFRESH_TOKEN_EXPIRE_DAYS,
    ))


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

async def register_socket_session(
        session_id: str,
        user_id: str
)-> None:
    await redis_client.set(
        name=f"socket:pending:{session_id}",
        value=user_id,
        ex=60
    )

async def consume_socket_session(session_id: str) -> str | None:
    return await redis_client.getdel(
        f"socket:pending:{session_id}"
    )
