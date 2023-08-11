from pydantic_settings import BaseSettings


class Config(BaseSettings):
    gay: bool = False


settings = Config()

print(settings.gay)
