from abc import ABC, abstractmethod
from typing import List, Tuple, Dict, Any
from .primitives import Entity, Relation

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

class FileExtractor(Extractor):
    def __init__(self, file_path: str, parser):
        self.file_path = file_path
        self.parser = parser

    def extract_entities(self) -> List[Entity]:
        return self.parser.extract_entities(self.file_path)

    def extract_relations(self) -> List[Relation]:
        return self.parser.extract_relations(self.file_path)
    
    def entities_json_schema(self) -> Dict[str, Any]:
        return self.parser.entities_json_schema(self.file_path)