import os
import pymysql
import logging
from .base_connector import BaseConnector
execution_env = os.environ['SPRING_PROFILES_ACTIVE']
if (execution_env.upper() != "MYLOCAL"):
    import castlight_common_lib.configfunctions as cfg
    config_details = cfg.Config('dataqeteam', [os.environ.get('SPRING_PROFILES_ACTIVE')])
else:
    config_details = None
logger = logging.getLogger(__name__)


class MySQLConnector(BaseConnector):

    def __init__(self, host=None, port=None, user=None, password=None, database=None, k8_db_details=None):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.connection = None
        if k8_db_details is None or config_details is None:
            logger.info(f"Locally MySQLConnector initialized for host={host}, database={database}")
        else:
            try:
                project, db_name = k8_db_details.split('_')
                self.host = config_details.data['mysql'][project][db_name]['db_host']
                self.port = config_details.data['mysql'][project][db_name]['db_port']
                self.user = config_details.data['mysql'][project][db_name]['db_user']
                self.password = config_details.data['mysql'][project][db_name]['db_password']
                self.database = config_details.data['mysql'][project][db_name]['db_name']
            except (ValueError, KeyError) as e:
                logger.error(f"Failed to extract Kubernetes configuration: {str(e)}")
                raise ValueError(f"Invalid k8_db_details format or missing configuration: {str(e)}")

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

