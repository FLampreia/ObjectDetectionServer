from redis.asyncio import Redis

from app.core.config import config

redis_client = Redis(
    host=config.REDIS_HOST,
    port=config.REDIS_PORT,
    db=0,
    decode_responses=True
)


