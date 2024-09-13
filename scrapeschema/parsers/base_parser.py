from abc import ABC, abstractmethod
from typing import List, Dict, Any
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
        self._entities = []
        self._relations = []

    @abstractmethod
    def extract_entities(self, file_path: str) -> List[Entity]:
        pass

    @abstractmethod
    def extract_relations(self, file_path: str) -> List[Relation]:
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
    
    def set_entities(self, entities: List[Entity]):
        if not isinstance(entities, list) or not all(isinstance(entity, Entity) for entity in entities):
            raise TypeError("entities must be a List of Entity objects")
        self._entities = entities
    
    def set_relations(self, relations: List[Relation]):
        if not isinstance(relations, list) or not all(isinstance(relation, Relation) for relation in relations):
            raise TypeError("relations must be a List of Relation objects")
        self._relations = relations
