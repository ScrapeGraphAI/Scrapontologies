from dataclasses import dataclass
from typing import Any

@dataclass
class Entity_Type:
    attributes: dict[str, str]
    #confidence: float

@dataclass
class Relation_Type:
    source: Entity_Type
    target: Entity_Type
    type: str
    #confidence: float

@dataclass
class Entity:
    attributes: dict[str, str]  # Dictionary of attribute name (str) to attribute value (str)

@dataclass
class Relation:
    source: Entity
    target: Entity
    type: str