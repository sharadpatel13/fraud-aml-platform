from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    db_server: str
    db_name: str
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    class Config:
        env_file = ".env"


settings = Settings()