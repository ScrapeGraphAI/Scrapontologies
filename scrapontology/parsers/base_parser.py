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



