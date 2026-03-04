from pydantic import BaseModel, Field

class Settings(BaseModel):
    database_url: str = Field(..., description="Database connection URL")
    log_level: str = Field('INFO', description="Logging level")
    ui_settings: dict = Field(..., description="UI settings such as theme, language")
    supported_languages: list = Field(..., description="List of supported languages")
    paths: dict = Field(..., description="Application paths for various resources")

    class Config:
        env_file = '.env'  # Load environment variables

# Example of instantiating Settings
# settings = Settings(
#     database_url='sqlite:///db.sqlite3',
#     ui_settings={'theme': 'light'},
#     supported_languages=['en', 'es', 'fr', 'de', 'jp', 'cn', 'ru', 'pt', 'it'],
#     paths={'assets': 'src/assets', 'logs': 'log'}
# )