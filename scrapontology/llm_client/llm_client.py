import requests
import logging
from typing import Dict, Any, Optional, List
from typing import Any, Callable
from pydantic_core import CoreSchema, core_schema
from abc import ABC

logger = logging.getLogger(__name__)

class LLMClient(ABC):

    def get_response(self, prompt: str, image_url: Optional[str] = None) -> str:
        """Get a response from the language model.

        Args:
            prompt (str): The prompt to send to the language model.
            image_url (Optional[str]): An optional image URL to include in the prompt.

        Returns:
            str: The response from the language model.
        """
        pass