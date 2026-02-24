import pandas as pd
import psycopg2
from odps import ODPS
from src.core.base_engine import BaseEngine
from src.config import settings, DBConfig
from src.utils.logger import logger

class ODPSEngine(BaseEngine):
    def __init__(self, config: DBConfig):
        self.config = config

    def fetch(self, sql: str, **kwargs) -> pd.DataFrame:
        logger.info(f"Connecting to ODPS Project: {self.config.project}...")
        o = ODPS(
            self.config.access_id, 
            self.config.access_key, 
            self.config.project, 
            endpoint=self.config.endpoint
        )
        hints = {"odps.sql.submit.mode": "script"}
        with o.execute_sql(sql, hints=hints).open_reader() as reader:
            return reader.to_pandas()

class HoloEngine(BaseEngine):
    def __init__(self, config: DBConfig):
        self.config = config

    def fetch(self, sql: str, **kwargs) -> pd.DataFrame:
        logger.info(f"Connecting to Hologres: {self.config.host}...")
        conn = psycopg2.connect(
            host=self.config.host, 
            port=self.config.port,
            dbname=self.config.dbname, 
            user=self.config.user,
            password=self.config.password
        )
        try:
            return pd.read_sql(sql, conn)
        finally:
            conn.close()
