from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    db_server: str
    db_name: str
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    jira_base_url: str = ""
    jira_email: str = ""
    jira_api_token: str = ""
    jira_project_key: str = "FRAUD"

    class Config:
        env_file = ".env"


settings = Settings()