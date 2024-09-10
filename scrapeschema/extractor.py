from abc import ABC, abstractmethod
from typing import List, Tuple, Dict, Any
from .primitives import Entity, Relation
from .parsers.base_parser import BaseParser
from .parsers.prompts import DELETE_PROMPT
import requests
import json

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
    def __init__(self, file_path: str, parser: BaseParser):
        self.file_path = file_path
        self.parser = parser

    def extract_entities(self) -> List[Entity]:
        return self.parser.extract_entities(self.file_path)

    def extract_relations(self) -> List[Relation]:
        return self.parser.extract_relations(self.file_path)
    
    def entities_json_schema(self) -> Dict[str, Any]:
        return self.parser.entities_json_schema(self.file_path)

    def delete_entity_or_relation(self, item_description: str) -> None:
        """
        Delete an entity or relation based on user description.
        
        :param item_description: User's description of the entity or relation to delete
        """
        entities_ids = [e.id for e in self.parser.get_entities()]
        relations_ids = [(r.source, r.target, r.name) for r in self.parser.get_relations()]
        prompt = DELETE_PROMPT.format(
            entities=entities_ids,
            relations=relations_ids,
            item_description=item_description
        )

        response = self._get_llm_response(prompt)[8:-3]
        response_dict = json.loads(response)

        for key, value in response_dict.items():
            if key == 'Type':
                if value == 'Entity':
                    self._delete_entity(response_dict['ID'])
                elif value == 'Relation':
                    self._delete_relation(response_dict['ID'])


    def _delete_entity(self, entity_id: str) -> None:
        """Delete an entity and its related relations."""
        entities = self.parser.get_entities()
        relations = self.parser.get_relations()
        
        entities = [e for e in entities if e.id != entity_id]
        relations = [r for r in relations if r.source != entity_id and r.target != entity_id]
        
        self.parser.set_entities(entities)
        self.parser.set_relations(relations)
        print(f"Entity '{entity_id}' and its related relations have been deleted.")

    def _delete_relation(self, relation_id: str) -> None:
        """Delete a relation."""
        relations = self.parser.get_relations()
        
        source, target, name = eval(relation_id)
        relations = [r for r in relations if not (r.source == source and r.target == target and r.name == name)]
        
        self.parser.set_relations(relations)
        print(f"Relation '{name}' between '{source}' and '{target}' has been deleted.")

    def _get_llm_response(self, prompt: str) -> str:
        """Get a response from the language model."""
        payload = {
            "model": self.parser.get_model(),
            "temperature": self.parser.get_temperature(),
            "messages": [
                {"role": "user", "content": prompt}
            ],
        }
        response = requests.post(self.parser.get_inference_base_url(), headers=self.parser.get_headers(), json=payload)
        return response.json()['choices'][0]['message']['content']