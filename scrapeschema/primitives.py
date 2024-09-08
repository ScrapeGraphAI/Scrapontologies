from dataclasses import dataclass
from typing import Any, Dict, List

@dataclass
class Entity:
    id: str
    type: str
    attributes: Dict[str, Any]

@dataclass
class Relation:
    source: str
    target: str
    name: str
    type: str = None
    attributes: Dict[str, Any] = None