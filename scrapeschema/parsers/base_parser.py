from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from ..primitives import Entity, Relation
from ..llm_client import LLMClient

class BaseParser(ABC):
    def __init__(self, llm_client: LLMClient):
        """
        Initializes the PDFParser with an API key.

        Args:
            api_key (str): The API key for authentication.
        """
        self.llm_client = llm_client
        self._headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.llm_client.get_api_key()}"
        }
        self._json_schema = {}
        self._entities = []
        self._relations = []

    @abstractmethod
    def extract_entities(self, file_path: str, prompt: Optional[str] = None) -> List[Entity]:
        pass

    @abstractmethod
    def extract_relations(self, file_path: Optional[str] = None, prompt: Optional[str] = None) -> List[Relation]:
        pass

    @abstractmethod
    def entities_json_schema(self, file_path: str) -> Dict[str, Any]:
        pass

    def get_api_key(self):
        return self._api_key
    
    def get_headers(self):
        return self._headers
    
    def get_model(self):
        return self._model
    
    def get_temperature(self):
        return self._temperature
    
    def get_inference_base_url(self):
        return self._inference_base_url
    
    def set_api_key(self, api_key: str):
        self._api_key = api_key
    
    def set_headers(self, headers: Dict[str, str]):
        self._headers = headers
    
    def set_inference_base_url(self, inference_base_url: str):
        self.inference_base_url = inference_base_url

    def get_entities(self):
        return self._entities
    
    def get_relations(self):
        return self._relations
    
    def get_json_schema(self):
        return self._json_schema
    
    def set_entities(self, entities: List[Entity]):
        if not isinstance(entities, list) or not all(isinstance(entity, Entity) for entity in entities):
            raise TypeError("entities must be a List of Entity objects")
        self._entities = entities
    
    def set_relations(self, relations: List[Relation]):
        if not isinstance(relations, list) or not all(isinstance(relation, Relation) for relation in relations):
            raise TypeError("relations must be a List of Relation objects")
        self._relations = relations

    def set_json_schema(self, schema: Dict[str, Any]):
        self._json_schema = schema

    def extract_entities_from_json_schema(self, json_schema: Dict[str, Any]) -> List[Entity]:
        """
        Extracts entities from a given JSON schema.

        Args:
            json_schema (Dict[str, Any]): The JSON schema to extract entities from.

        Returns:
            List[Entity]: A list of extracted entities.
        """
        entities = []

        def traverse_schema(schema: Dict[str, Any], parent_id: str = None):
            if isinstance(schema, dict):
                entity_id = parent_id if parent_id else schema.get('title', 'root')
                entity_type = schema.get('type', 'object')
                attributes = schema.get('properties', {})

                if attributes:
                    entity = Entity(id=entity_id, type=entity_type, attributes=attributes)
                    entities.append(entity)

                for key, value in attributes.items():
                    traverse_schema(value, key)

        traverse_schema(json_schema)
        self.set_entities(entities)
        return entities
