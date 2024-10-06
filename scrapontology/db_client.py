import os
from abc import ABC, abstractmethod
import psycopg2
from psycopg2.extras import RealDictCursor
import logging
from pydantic_core import CoreSchema, core_schema
from typing import Any, Callable
from neo4j import GraphDatabase

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
        self.port = port or os.getenv('POSTGRE1S_PORT', '5432')
        self.database = database or os.getenv('POSTGRES_DB', 'scrapontology_test')
        self.user = user or os.getenv('POSTGRES_USER', 'lurens')
        self.password = password or os.getenv('POSTGRES_PASSWORD', 'cicciopasticco')

        @classmethod
        def __get_pydantic_core_schema__(cls, _source_type: Any, _handler: Callable) -> CoreSchema:
            return core_schema.any_schema()

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
            raise error  # Re-raise the exception to propagate it


class Neo4jDBClient(DBClient):
    def __init__(self, uri=None, user=None, password=None):
        self.driver = None
        self.uri = uri or os.getenv('NEO4J_URI', 'bolt://localhost:7687')
        self.user = user or os.getenv('NEO4J_USER', 'neo4j')
        self.password = password or os.getenv('NEO4J_PASSWORD', 'password')

    def connect(self):
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            logger.info("Successfully connected to Neo4j database")
        except Exception as error:
            logger.error(f"Error while connecting to Neo4j: {error}")
            raise error

    def disconnect(self):
        if self.driver:
            self.driver.close()
            logger.info("Neo4j connection is closed")

    def execute_query(self, query, params=None):
        try:
            with self.driver.session() as session:
                result = session.run(query, params)
                return [record.data() for record in result]
        except Exception as error:
            logger.error(f"Error executing Neo4j query: {error}")
            raise error
