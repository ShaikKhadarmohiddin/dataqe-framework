import os
import pymysql
import logging
from .base_connector import BaseConnector

logger = logging.getLogger(__name__)


class MySQLConnector(BaseConnector):

    def __init__(self, host, port, user, password, database):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.connection = None
        logger.info(f"MySQLConnector initialized for host={host}, database={database}")

    def connect(self):
        logger.info(f"Establishing MySQL connection to {self.host}:{self.port}/{self.database}")
        try:
            self.connection = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
                cursorclass=pymysql.cursors.DictCursor
            )
            logger.info(f"MySQL connection established successfully")
        except Exception as e:
            logger.error(f"Failed to connect to MySQL: {str(e)}")
            raise

    def execute_query(self, query: str):
        if not self.connection:
            self.connect()

        try:
            logger.debug(f"Executing query: {query[:100]}..." if len(query) > 100 else f"Executing query: {query}")
            with self.connection.cursor() as cursor:
                cursor.execute(query)
                result = cursor.fetchall()
            logger.info(f"Query executed successfully, returned {len(result)} rows")
            return result
        except Exception as e:
            logger.error(f"Failed to execute MySQL query: {str(e)}")
            raise

    def close(self):
        if self.connection:
            logger.info("Closing MySQL connection")
            self.connection.close()

