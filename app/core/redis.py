from redis.asyncio import Redis
from config import Config

token_blocklist = Redis(
    host=Config.REDIS_HOST,
    port=Config.REDIS_PORT,
    db=0
)

async def add_jti_to_blocklist(jti: str) -> None:

    await token_blocklist.set(
        name=jti,
        value="",
        ex=Config.JTI_EXPIRY
    )

async def token_in_blocklist(jti: str) -> bool:

    jti = await token_blocklist.get(jti)

    return jti is not None

#TODO verificar o dockerfile com o redis