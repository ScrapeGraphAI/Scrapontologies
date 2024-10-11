import logging
from abc import ABC, abstractmethod
from typing import List, Tuple, Dict, Any, Optional
from .primitives import Entity, Relation
from .parsers.base_parser import BaseParser
from .parsers.prompts import DELETE_PROMPT, UPDATE_ENTITIES_PROMPT, UPDATE_SCHEMA_PROMPT, CREATE_TABLES_PROMPT
from .llm_client import LLMClient
from .parsers.prompts import UPDATE_SCHEMA_PROMPT
from .db_client import DBClient, PostgresDBClient
import json
from langgraph.graph import StateGraph, END, START
from typing import TypedDict, Literal
from scrapontology.db_client import PostgresDBClient
from scrapontology.llm_client import LLMClient
from pydantic import BaseModel
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Extractor(ABC):
    @abstractmethod
    def extract_entities_schema(self) -> List[Entity]:
        pass

    @abstractmethod
    def extract_relations_schema(self) -> List[Relation]:
        pass

    def extract_entities_schema(self) -> List[Entity]:
        pass

    
    @abstractmethod
    def generate_entities_json_schema(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def merge_schemas(self, other_schema: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    def delete_entity_or_relation(self, item_description: str) -> None:
        pass

    @abstractmethod
    def get_entities_schema(self) -> List[Entity]:
        pass

    @abstractmethod
    def get_relations_schema(self) -> List[Relation]:
        pass

    @abstractmethod
    def get_json_schema(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_entities_schema_graph(self):
        pass

    @abstractmethod
    def get_relations_schema_graph(self):
        pass

    @abstractmethod
    def get_json_schema(self):
        pass

    @abstractmethod
    def get_db_client(self):
        pass

    @abstractmethod
    def set_db_client(self, db_client: DBClient):
        pass

    @abstractmethod
    def create_tables(self):
        pass

class FileExtractor(Extractor):
    def __init__(self, file_path: str, parser: BaseParser, db_client: Optional[DBClient] = None):
        """
        Initialize the FileExtractor.

        Args:
            file_path (str): The path to the file to be processed.
            parser (BaseParser): The parser to be used for extraction.
            db_client (Optional[DBClient]): The database client. Defaults to None.
        """
        self.file_path = file_path
        self.parser = parser
        self.db_client = db_client

    def extract_entities_schema(self, prompt: Optional[str] = None) -> List[Entity]:
        """
        Extract entities from the file.

        Args:
            prompt (Optional[str]): An optional prompt to guide the extraction.

        Returns:
            List[Entity]: A list of extracted entities.
        """
        new_entities = self.parser.extract_entities_schema(self.file_path, prompt)
        return new_entities

    def extract_relations_schema(self, prompt: Optional[str] = None) -> List[Relation]:
        """
        Extract relations from the file.

        Args:
            prompt (Optional[str]): An optional prompt to guide the extraction.

        Returns:
            List[Relation]: A list of extracted relations.
        """
        return self.parser.extract_relations_schema(self.file_path, prompt)
    
    def generate_entities_json_schema(self) -> Dict[str, Any]:
        """
        Generate a JSON schema for the entities.

        Returns:
            Dict[str, Any]: The generated JSON schema.
        """
        self.parser.generate_json_schema(self.file_path)
        return self.parser.get_json_schema()

    def delete_entity_or_relation(self, item_description: str) -> None:
        entities_ids = [e.id for e in self.parser.get_entities_schema()]
        relations_ids = [(r.source, r.target, r.name) for r in self.parser.get_relations_schema()]
        prompt = DELETE_PROMPT.format(
            entities=entities_ids,
            relations=relations_ids,
            item_description=item_description
        )

        response = self.parser.llm_client.get_response(prompt)
        response = response.strip().strip('```json').strip('```')
        response_dict = json.loads(response)

        item_type = response_dict.get('Type')
        item_id = response_dict.get('ID')

        if item_type == 'Entity':
            self._delete_entity(item_id)
        elif item_type == 'Relation':
            self._delete_relation(item_id)
        else:
            logger.error("Invalid type returned from LLM.")

    def _delete_entity(self, entity_id: str) -> None:
        """Delete an entity and its related relations."""
        entities = self.parser.get_entities_schema()
        relations = self.parser.get_relations_schema()
        
        entities = [e for e in entities if e.id != entity_id]
        relations = [r for r in relations if r.source != entity_id and r.target != entity_id]
        
        self.parser.set_entities(entities)
        self.parser.set_relations(relations)
        logger.info(f"Entity '{entity_id}' and its related relations have been deleted.")

    def _delete_relation(self, relation_id: str) -> None:
        """Delete a relation."""
        relations = self.parser.get_relations_schema()
        
        source, target, name = eval(relation_id)
        relations = [r for r in relations if not (r.source == source and r.target == target and r.name == name)]
        
        self.parser.set_relations(relations)
        logger.info(f"Relation '{name}' between '{source}' and '{target}' has been deleted.")

  
    
    def get_entities_schema(self) -> List[Entity]:
        """
        Get the entities from the parser.

        Returns:
            List[Entity]: The list of entities.
        """
        return self.parser.get_entities_schema()

    def get_relations_schema(self) -> List[Relation]:
        """
        Get the relations from the parser.

        Returns:
            List[Relation]: The list of relations.
        """
        return self.parser.get_relations_schema()

        
    def merge_schemas(self, other_schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merges the current parser's schema with another schema.

        Args:
            other_schema (Dict[str, Any]): The schema to merge with.
        """
        def _merge_json_schemas(self, schema1: Dict[str, Any], schema2: Dict[str, Any]) -> Dict[str, Any]:
            """
            Merges two JSON schemas using an API call to OpenAI.

            Args:
                schema1 (Dict[str, Any]): The first JSON schema.
                schema2 (Dict[str, Any]): The second JSON schema.

            Returns:
                Dict[str, Any]: The merged JSON schema.
            """

            # Initialize the LLMClient (assuming the API key is set in the environment)

            llm_client = self.parser.llm_client

            # Prepare the prompt
            prompt = UPDATE_SCHEMA_PROMPT.format(
                existing_schema=json.dumps(schema1, indent=2),
                new_schema=json.dumps(schema2, indent=2)
            )

            # Get the response from the LLM
            response = llm_client.get_response(prompt)

            # Extract the JSON schema from the response
            response = response.strip().strip('```json').strip('```')
            try:
                merged_schema = json.loads(response)
                return merged_schema
            except json.JSONDecodeError as e:
                logger.error(f"JSONDecodeError: {e}")
                logger.error("Error: Unable to parse the LLM response.")
                return schema1  # Return the original schema in case of an error


        if not self.parser.get_json_schema():
            logger.error("No JSON schema found in the parser.")
            return

        # Merge JSON schemas
        merged_schema = _merge_json_schemas(self, self.get_json_schema(), other_schema)

        self.set_json_schema(merged_schema)
        # Re-extract entities and relations based on the merged schema
        new_entities = self.parser.extract_entities_schema_from_json_schema(merged_schema)
        new_relations = self.parser.extract_relations_schema()

        return self.get_json_schema()


    def get_entities_schema_graph(self):
        """
        Retrieves the state graph for entities extraction.

        Returns:
            Any: The entities state graph from the parser.
        """
        return self.parser.get_entities_schema_graph()

    def get_relations_schema_graph(self):
        """
        Retrieves the state graph for relations extraction.

        Returns:
            Any: The relations state graph from the parser.
        """
        return self.parser.get_relations_schema_graph()

    def get_json_schema(self):
        """
        Retrieves the JSON schema.

        Returns:
            Dict[str, Any]: The current JSON schema from the parser.
        """
        return self.parser.get_json_schema()
    
    def get_db_client(self):
        """
        Retrieves the DB client.

        Returns:
            DBClient: The DB client.
        """
        if not isinstance(self.db_client, PostgresDBClient):
            logger.error("DB client is not a relational database client.")
            raise ValueError("DB client is not a relational database client.")\

        return self.db_client

    def set_db_client(self, db_client: DBClient):
        """
        Sets the DB client.

        Args:
            db_client (DBClient): The DB client.
        """
        if not isinstance(db_client, DBClient):
            logger.error("DB client is not a valid DB client.")
            raise ValueError("DB client is not a valid DB client.")

        self.db_client = db_client

    def create_tables(self):
        """
        Creates the tables in a relational database.
        """
        # checks if the db_client is a PostgresDBClient
        if not isinstance(self.db_client, PostgresDBClient):
            logger.error("DB client is not a relational database client.")
            raise ValueError("DB client is not a relational database client.")
        
        # get the json schema
        json_schema = self.get_json_schema()

        self.db_client.connect()

        class StateCreateTables(BaseModel):
            json_schema: Optional[str] = None
            sql_code: Optional[str] = None
            retry: Optional[bool] = None
            error: Optional[str] = None
            retry_count: Optional[int] = 0

        state_create_tables = StateCreateTables()
        state_create_tables.json_schema = str(json_schema)

        
        def generate_sql_code(state: StateCreateTables, *_) -> StateCreateTables:
            if state.sql_code is None:
                create_tables_prompt = CREATE_TABLES_PROMPT.format(
                    json_schema=json.dumps(state.json_schema, indent=2)
                )
                sql_code = self.parser.llm_client.get_response(create_tables_prompt)
                sql_code = sql_code.replace("```sql", "").replace("```", "").strip()
                state.sql_code = sql_code
            else:
                create_tables_prompt_fixed = CREATE_TABLES_PROMPT.format(
                json_schema=json.dumps(state.json_schema, indent=2)
                ) + "You generated previously the following erroneous code: " + state.sql_code + "With the following error: " + state.error + " Please fix it, if the relation already exists in the database please just ignore it and do not create it again."

                state.retry_count += 1
                sql_code = self.parser.llm_client.get_response(create_tables_prompt_fixed)
                sql_code = sql_code.replace("```sql", "").replace("```", "").strip()
                state.sql_code = sql_code
            return state

        def execute_sql_code(state: StateCreateTables, *_) -> Literal["success", "failure"]:
            try:
                self.db_client.execute_query(state.sql_code)
                state.retry = False
                return state
            except Exception as e:
                print(f"Error executing SQL: {e}")
                state.error = str(e)
                state.retry = True
                return state
        
        def retry_or_not(state: StateCreateTables, *_):
            if state.retry and state.retry_count < 2:
                return "generate_sql_code"
            else:   
                return END

        # Build the graph
        workflow = StateGraph(StateCreateTables)

        # Add nodes
        workflow.add_node("generate_sql_code", generate_sql_code)
        workflow.add_node("execute_sql_code", execute_sql_code)

        # Add edges
        workflow.add_edge(START, "generate_sql_code")
        workflow.add_edge("generate_sql_code", "execute_sql_code")
        workflow.add_conditional_edges(
            "execute_sql_code",
            retry_or_not
        )
        workflow.add_edge("execute_sql_code", END)

        # Compile the graph
        graph = workflow.compile()

        # Execute the graph
        graph.invoke(state_create_tables)
        self.db_client.disconnect()
        logger.info("Tables created successfully.")

    def extract_entities(self):
        return self.parser.extract_entities_schema()
