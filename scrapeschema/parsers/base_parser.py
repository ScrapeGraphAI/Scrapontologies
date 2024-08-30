from abc import ABC, abstractmethod
from typing import List
from ..entities import Entity, Relation

class BaseParser(ABC):
    @abstractmethod
    def extract_entities(self, file_path: str) -> List[Entity]:
        pass

    @abstractmethod
    def extract_relations(self, file_path: str) -> List[Relation]:
        pass