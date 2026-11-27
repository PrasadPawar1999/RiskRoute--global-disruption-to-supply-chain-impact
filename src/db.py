"""
Shared database connection for all RiskRoute scripts.

Reads settings from .env. Uses URL.create so passwords containing
special characters (@, #, :, / ...) work correctly.
"""
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import URL

load_dotenv()


def get_engine(with_database: bool = True):
    url = URL.create(
        drivername="mysql+pymysql",
        username=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "3306")),
        database=os.getenv("DB_NAME", "chainsight") if with_database else None,
    )
    return create_engine(url)


DB_NAME = os.getenv("DB_NAME", "chainsight")
