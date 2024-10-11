from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union
from ..primitives import Entity, Relation
from ..llm_client import LLMClient

class BaseParser(ABC):
    def __init__(self, llm_client: LLMClient):
        """
        Initializes the BaseParser with an LLMClient.

        Args:
            llm_client (LLMClient): The LLM client for inference.
        """
        self.llm_client = llm_client
        self._headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.llm_client.get_api_key()}"
        }
        self._json_schema = {}
        self._entities_schema = []
        self._relations_schema = []

    @abstractmethod
    def extract_entities_schema(self, file_path: str, prompt: Optional[str] = None) -> List[Entity]:
        """
        Extracts entities from the given file.

        Args:
            file_path (str): The path to the file.
            prompt (Optional[str]): An optional prompt to guide the extraction.

        Returns:
            List[Entity]: A list of extracted entities.
        """
        pass

    @abstractmethod
    def extract_relations_schema(self, file_path: Optional[str] = None, prompt: Optional[str] = None) -> List[Relation]:
        """
        Extracts relations from the given file.

        Args:
            file_path (Optional[str]): The path to the file.
            prompt (Optional[str]): An optional prompt to guide the extraction.

        Returns:
            List[Relation]: A list of extracted relations.
        """
        pass

    @abstractmethod
    def generate_json_schema(self, file_path: str) -> Dict[str, Any]:
        """
        Generates a JSON schema for the entities based on the given file.

        Args:
            file_path (str): The path to the file.

        Returns:
            Dict[str, Any]: The generated JSON schema.
        """
        pass

    @abstractmethod
    def get_entities_schema(self) -> List[Entity]:
        """
        Retrieves the list of entities.

        Returns:
            List[Entity]: The current list of entities.
        """
        pass


    @abstractmethod
    def get_relations_schema(self) -> List[Relation]:
        """
        Retrieves the list of relations.

        Returns:
            List[Relation]: The current list of relations.
        """
        pass


    @abstractmethod
    def get_json_schema(self) -> Dict[str, Any]:
        """
        Retrieves the JSON schema.

        Returns:
            Dict[str, Any]: The current JSON schema.
        """
        pass


    @abstractmethod
    def get_entities_schema_graph(self):
        """
        Retrieves the state graph for entities extraction.

        Returns:
            Any: The entities state graph.
        """
        pass

    @abstractmethod
    def get_relations_schema_graph(self):
        """
        Retrieves the state graph for relations extraction.

        Returns:
            Any: The relations state graph.
        """
        pass

    @abstractmethod
    def extract_entities_from_file(self, file_path: Union[str, List[str]]):
        pass



