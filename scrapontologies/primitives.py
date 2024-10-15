from dataclasses import dataclass
from typing import Any, Dict, List

@dataclass
class Entity:
    id: str
    type: str
    attributes: Dict[str, Any]

@dataclass
class Relation:
    id: str
    source: str
    target: str
    name: str
    type: str = None
    attributes: Dict[str, Any] = None

@dataclass
class Record:
    id: str
    entities: List[Entity]
