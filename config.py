"""Configuration management for Yandex Metrika to PostgreSQL data loader."""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration."""

    # Database configuration
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '5432')
    DB_NAME = os.getenv('DB_NAME', 'default_db')
    DB_USER = os.getenv('DB_USER', 'cloud_user')
    DB_PASSWORD = os.getenv('DB_PASSWORD')

    # Yandex Metrika configuration
    YM_TOKEN = os.getenv('YM_TOKEN')
    YM_COUNTER_ID = os.getenv('YM_COUNTER_ID')

    # Data export settings
    START_DATE = os.getenv('START_DATE', '2024-01-01')
    END_DATE = os.getenv('END_DATE', '2024-12-31')

    # Table name
    TABLE_NAME = 'yandex_metrika_visits'

    @classmethod
    def validate(cls):
        """Validate required configuration."""
        required_vars = {
            'DB_PASSWORD': cls.DB_PASSWORD,
            'YM_TOKEN': cls.YM_TOKEN,
            'YM_COUNTER_ID': cls.YM_COUNTER_ID
        }

        missing_vars = [var for var, value in required_vars.items() if not value]

        if missing_vars:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing_vars)}. "
                "Please check your .env file."
            )
