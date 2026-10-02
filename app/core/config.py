from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()

class Config(BaseSettings):
    app_name: str = "ObjectDetectionAPI"
    description: str = "A REST API for the central server on ObjectDetection"
    version:str = "1" 
    debug: bool = False

    DB_NAME: str
    JWT_SECRET: str
    JWT_ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    JTI_EXPIRY: int = 3600

    PROCESSOR_HOST: str = "localhost"
    PROCESSOR_PORT: int = 8001

    CLOUDINARY_CLOUD_NAME: str
    CLOUDINARY_API_KEY: str
    CLOUDINARY_API_SECRET: str

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )

    @property
    def db_url(self):
        return f"sqlite:///./{self.DB_NAME}"


config = Config()