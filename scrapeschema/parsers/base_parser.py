from abc import ABC, abstractmethod
from typing import List, Dict, Any
from ..primitives import Entity, Relation

class BaseParser(ABC):
    def __init__(self, api_key: str, inference_base_url: str = "https://api.openai.com/v1/chat/completions", model: str = "gpt-4o", temperature: float = 0.0):
        """
        Initializes the PDFParser with an API key.

        Args:
            api_key (str): The API key for authentication.
        """
        self.api_key = api_key
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        self.inference_base_url = inference_base_url
        self.model = model
        self.temperature = temperature
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
        return self.api_key
    
    def get_headers(self):
        return self.headers
    
    def get_inference_base_url(self):
        return self.inference_base_url
    
    def set_api_key(self, api_key: str):
        self.api_key = api_key
    
    def set_headers(self, headers: Dict[str, str]):
        self.headers = headers
    
    def set_inference_base_url(self, inference_base_url: str):
        self.inference_base_url = inference_base_url
    