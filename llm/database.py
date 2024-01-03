from functools import lru_cache
import os

from langchain.sql_database import SQLDatabase


@lru_cache
def load_db() -> SQLDatabase:
    return SQLDatabase.from_uri(os.environ['DB_URI'])
