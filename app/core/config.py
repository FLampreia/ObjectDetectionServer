from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class Config(BaseSettings):
    app_name: str = "ObjectDetectionAPI"
    description: str = "A REST API for the central server on ObjectDetection"
    version:str = "1" 
    debug: bool = False

    DB_NAME: str

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )

    @property
    def db_url(self):
        return f"sqlite:///./{self.DB_NAME}"


config = Config()