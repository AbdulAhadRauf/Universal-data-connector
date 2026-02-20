
from pydantic_settings import BaseSettings
from pydantic import ConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Universal Data Connector"
    MAX_RESULTS: int = 10

    model_config = ConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
