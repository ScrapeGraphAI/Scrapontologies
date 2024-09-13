from ..primitives import Entity, Relation

from abc import ABC, abstractmethod
from typing import List


class BaseRenderer(ABC):
    @abstractmethod
    def render(self, entities: List[Entity], relations: List[Relation]) -> None:
        pass
