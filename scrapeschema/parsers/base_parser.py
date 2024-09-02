from abc import ABC, abstractmethod
from typing import List, Dict, Any
from ..entities import Entity, Relation

class BaseParser(ABC):
    @abstractmethod
    def extract_entities(self, file_path: str) -> List[Entity]:
        pass

    @abstractmethod
    def extract_relations(self, file_path: str) -> List[Relation]:
        pass

    @abstractmethod
    def entities_json_schema(self, file_path: str) -> Dict[str, Any]:
        pass