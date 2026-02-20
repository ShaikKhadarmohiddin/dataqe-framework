import pymysql
from .base_connector import BaseConnector


class MySQLConnector(BaseConnector):

    def __init__(self, host, port, user, password, database):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.connection = None

    def connect(self):
        self.connection = pymysql.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            database=self.database,
            cursorclass=pymysql.cursors.DictCursor
        )

    def execute_query(self, query: str):
        if not self.connection:
            self.connect()

        with self.connection.cursor() as cursor:
            cursor.execute(query)
            result = cursor.fetchall()

        return result

    def close(self):
        if self.connection:
            self.connection.close()

