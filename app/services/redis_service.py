from app.core.config import config
from app.core.redis_config import redis_client
from app.exceptions.custom_exceptions import RedisNotAvailable


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
