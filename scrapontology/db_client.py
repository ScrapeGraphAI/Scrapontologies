import os
from abc import ABC, abstractmethod
import psycopg2
from psycopg2.extras import RealDictCursor
import logging

logger = logging.getLogger(__name__)

class DBClient(ABC):
    @abstractmethod
    def connect(self):
        pass

    @abstractmethod
    def disconnect(self):
        pass

    @abstractmethod
    def execute_query(self, query, params=None):
        pass

class PostgresDBClient(DBClient):
    def __init__(self, host=None, port=None, database=None, user=None, password=None):
        self.conn = None
        self.cursor = None
        self.host = host or os.getenv('POSTGRES_HOST', 'localhost')
        self.port = port or os.getenv('POSTGRES_PORT', '5432')
        self.database = database or os.getenv('POSTGRES_DB', 'scrapontology_test')
        self.user = user or os.getenv('POSTGRES_USER', 'lurens')
        self.password = password or os.getenv('POSTGRES_PASSWORD', 'cicciopasticco')

    def connect(self):
        try:
            self.conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password
            )
            self.cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            logger.info("Successfully connected to PostgreSQL database")
        except (Exception, psycopg2.Error) as error:
            logger.error(f"Error while connecting to PostgreSQL: {error}")

    def disconnect(self):
        if self.conn:
            self.cursor.close()
            self.conn.close()
            logger.info("PostgreSQL connection is closed")

    def execute_query(self, query, params=None):
        try:
            self.cursor.execute(query, params)
            self.conn.commit()
            return self.cursor.fetchall()
        except (Exception, psycopg2.Error) as error:
            logger.error(f"Error executing query: {error}")
            self.conn.rollback()
            return None

class Neo4jDBClient(DBClient):
    def __init__(self):
        # Placeholder for future implementation
        pass

    def connect(self):
        # Placeholder for future implementation
        logger.info("Neo4j connection not yet implemented")

    def disconnect(self):
        # Placeholder for future implementation
        pass

    def execute_query(self, query, params=None):
        # Placeholder for future implementation
        logger.info("Neo4j query execution not yet implemented")
        return None

# Factory function to get the appropriate DB client
def get_db_client(db_type='postgres'):
    if db_type.lower() == 'postgres':
        return PostgresDBClient()
    elif db_type.lower() == 'neo4j':
        return Neo4jDBClient()
    else:
        raise ValueError(f"Unsupported database type: {db_type}")