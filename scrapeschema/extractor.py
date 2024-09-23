import logging
from abc import ABC, abstractmethod
from typing import List, Tuple, Dict, Any
from .primitives import Entity, Relation
from .parsers.base_parser import BaseParser
from .parsers.prompts import DELETE_PROMPT, UPDATE_ENTITIES_PROMPT, UPDATE_SCHEMA_PROMPT
from .llm_client import LLMClient
from .parsers.prompts import UPDATE_SCHEMA_PROMPT
import json

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Extractor(ABC):
    @abstractmethod
    def extract_entities(self) -> List[Entity]:
        pass

    @abstractmethod
    def extract_relations(self) -> List[Relation]:
        pass
    
    @abstractmethod
    def entities_json_schema(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def update_entities(self, new_entities: List[Entity]) -> List[Entity]:
        pass

    @abstractmethod
    def merge_schemas(self, other_schema: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    def delete_entity_or_relation(self, item_description: str) -> None:
        pass

    @abstractmethod
    def set_entities(self, entities: List[Entity]) -> None:
        pass

    @abstractmethod
    def set_relations(self, relations: List[Relation]) -> None:
        pass

    @abstractmethod
    def set_json_schema(self, schema: Dict[str, Any]) -> None:
        pass

class FileExtractor(Extractor):
    def __init__(self, file_path: str, parser: BaseParser):
        self.file_path = file_path
        self.parser = parser

    def extract_entities(self) -> List[Entity]:
        new_entities = self.parser.extract_entities(self.file_path)
        return new_entities

    def extract_relations(self) -> List[Relation]:
        return self.parser.extract_relations(self.file_path)
    

    def entities_json_schema(self) -> Dict[str, Any]:
        return self.parser.entities_json_schema(self.file_path)

    def delete_entity_or_relation(self, item_description: str) -> None:
        entities_ids = [e.id for e in self.parser.get_entities()]
        relations_ids = [(r.source, r.target, r.name) for r in self.parser.get_relations()]
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
        entities = self.parser.get_entities()
        relations = self.parser.get_relations()
        
        entities = [e for e in entities if e.id != entity_id]
        relations = [r for r in relations if r.source != entity_id and r.target != entity_id]
        
        self.parser.set_entities(entities)
        self.parser.set_relations(relations)
        logger.info(f"Entity '{entity_id}' and its related relations have been deleted.")

    def _delete_relation(self, relation_id: str) -> None:
        """Delete a relation."""
        relations = self.parser.get_relations()
        
        source, target, name = eval(relation_id)
        relations = [r for r in relations if not (r.source == source and r.target == target and r.name == name)]
        
        self.parser.set_relations(relations)
        logger.info(f"Relation '{name}' between '{source}' and '{target}' has been deleted.")

    def update_entities(self, new_entities: List[Entity]) -> List[Entity]:
        """
        Update the existing entities with new entities, integrating and deduplicating as necessary.
        
        :param new_entities: List of new entities to be integrated
        :return: Updated list of entities
        """
        existing_entities = self.parser.get_entities()
        
        # Prepare the prompt for the LLM
        prompt = UPDATE_ENTITIES_PROMPT.format(
            existing_entities=json.dumps([e.__dict__ for e in existing_entities], indent=2),
            new_entities=json.dumps([e.__dict__ for e in new_entities], indent=2)
        )

        # Get the LLM response
        response = self._get_llm_response(prompt)
        
        try:
            updated_entities_data = json.loads(response)
            updated_entities = [Entity(**entity_data) for entity_data in updated_entities_data]
            
            # Update the parser's entities
            self.parser.set_entities(updated_entities)
            
            logger.info(f"Entities updated. New count: {len(updated_entities)}")
            return updated_entities
        except json.JSONDecodeError:
            logger.error("Error: Unable to parse the LLM response.")
            return existing_entities

    def set_json_schema(self, schema: Dict[str, Any]) -> None:
        """
        Set the JSON schema for the parser.

        Args:
            schema (Dict[str, Any]): The JSON schema to set.
        """
        self.parser.set_json_schema(schema)

    def set_entities(self, entities: List[Entity]) -> None:
        """
        Set the entities for the parser.

        Args:
            entities (List[Entity]): The list of entities to set.
        """
        self.parser.set_entities(entities)

    def set_relations(self, relations: List[Relation]) -> None:
        """
        Set the relations for the parser.

        Args:
            relations (List[Relation]): The list of relations to set.
        """
        self.parser.set_relations(relations)
    
    def get_entities(self) -> List[Entity]:
        """
        Get the entities from the parser.

        Returns:
            List[Entity]: The list of entities.
        """
        return self.parser.get_entities()

    def get_relations(self) -> List[Relation]:
        """
        Get the relations from the parser.

        Returns:
            List[Relation]: The list of relations.
        """
        return self.parser.get_relations()

    def get_json_schema(self) -> Dict[str, Any]:
        """
        Get the JSON schema from the parser.

        Returns:
            Dict[str, Any]: The JSON schema.
        """
        return self.parser.get_json_schema()
        
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
        new_entities = self.parser.extract_entities_from_json_schema(merged_schema)
        new_relations = self.parser.extract_relations()

        return self.get_json_schema()


        ###########################################################################################
       