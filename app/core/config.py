from typing import List, Union
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl, validator

class Settings(BaseSettings):
    PROJECT_NAME: str = "PredictPix"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    
    # PostgreSQL Database settings
    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    SQLALCHEMY_DATABASE_URI: str | None = None

    @validator("SQLALCHEMY_DATABASE_URI", pre=True)
    def assemble_db_connection(cls, v: str | None, values: dict) -> str:
        if v:
            return v
        return f"postgresql://{values['POSTGRES_USER']}:{values['POSTGRES_PASSWORD']}@{values['POSTGRES_SERVER']}/{values['POSTGRES_DB']}"

    # Pi Network SDK Configuration
    PI_API_KEY: str
    PI_NETWORK_URL: str = "https://api.minepi.com"
    PI_SANDBOX_MODE: bool = True

    # Security settings
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # CORS Configuration
    ALLOWED_ORIGINS: Union[str, List[AnyHttpUrl]] = ""

    @validator("ALLOWED_ORIGINS")
    def parse_allowed_origins(cls, v: Union[str, List]) -> List[AnyHttpUrl]:
        if isinstance(v, str) and v:
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v if isinstance(v, list) else []

    # Redis Configuration
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Fee Configuration
    PLATFORM_FEE_PERCENTAGE: float = 2.0  # 2% platform fee
    CREATOR_FEE_PERCENTAGE: float = 1.0    # 1% creator fee
    
    # Prediction Market Configuration
    MIN_PREDICTION_AMOUNT: float = 1.0     # Minimum prediction amount in PI
    MAX_PREDICTION_AMOUNT: float = 1000.0   # Maximum prediction amount in PI
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100         # Number of requests
    RATE_LIMIT_WINDOW: int = 60            # Time window in seconds

    # Web3 Configuration
    WEB3_PROVIDER_URL: str
    CONTRACT_ADDRESS: str
    ADMIN_PRIVATE_KEY: str

    # Admin user settings
    ADMIN_USERNAME: str = "admin"
    ADMIN_EMAIL: str = "admin@predictpix.com"
    ADMIN_PASSWORD: str = "password"

    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings() 