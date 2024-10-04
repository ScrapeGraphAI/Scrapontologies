import requests
import logging
from typing import Dict, Any, Optional, List
from typing import Any, Callable
from pydantic_core import CoreSchema, core_schema

logger = logging.getLogger(__name__)

class LLMClient:
    def __init__(self, api_key: str, inference_base_url: str = "https://api.openai.com/v1/chat/completions",
                 model: str = "gpt-4o-2024-08-06", temperature: float = 0.0):
        """
        Initializes the LLMClient with API credentials and settings.

        Args:
            api_key (str): The API key for authentication.
            inference_base_url (str): The base URL for the inference API.
            model (str): The model to use for inference.
            temperature (float): The temperature setting for the model.
        """
        self._api_key = api_key
        self._inference_base_url = inference_base_url
        self._model = model
        self._temperature = temperature

        self._headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._api_key}"
        }

        self.session = requests.Session()

        @classmethod
        def __get_pydantic_core_schema__(cls, _source_type: Any, _handler: Callable) -> CoreSchema:
            return core_schema.any_schema()

    def get_api_key(self) -> str:
        return self._api_key

    def get_headers(self) -> Dict[str, str]:
        return self._headers

    def get_model(self) -> str:
        return self._model

    def get_temperature(self) -> float:
        return self._temperature

    def get_inference_base_url(self) -> str:
        return self._inference_base_url

    def set_api_key(self, api_key: str):
        self._api_key = api_key
        self._headers["Authorization"] = f"Bearer {self._api_key}"

    def set_model(self, model: str):
        self._model = model

    def set_temperature(self, temperature: float):
        self._temperature = temperature

    def set_inference_base_url(self, inference_base_url: str):
        self._inference_base_url = inference_base_url

    def _handle_response(self, response: requests.Response) -> str:
        """Handles the API response, checking for errors and extracting the content."""
        try:
            response.raise_for_status()
            data = response.json()
            return data['choices'][0]['message']['content']
        except requests.HTTPError as e:
            logger.error(f"HTTPError: {e}")
            logger.error(f"Response content: {response.text}")
            raise
        except KeyError as e:
            logger.error(f"KeyError: {e}")
            logger.error(f"Malformed response: {response.text}")
            raise

    def get_response(self, prompt: str, image_url: Optional[str] = None) -> str:
        """Get a response from the language model.

        Args:
            prompt (str): The prompt to send to the language model.
            image_url (Optional[str]): An optional image URL to include in the prompt.

        Returns:
            str: The response from the language model.
        """
        messages = [{"role": "user", "content": prompt}]

        if image_url:
            # Assuming the API supports image URLs in this format
            messages[0]["content"] = [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": image_url}}
            ]

        payload = {
            "model": self._model,
            "temperature": self._temperature,
            "messages": messages,
        }

        try:
            response = self.session.post(
                self._inference_base_url,
                headers=self._headers,
                json=payload,
                timeout=60  # Increase timeout to 60 seconds or more
            )
            return self._handle_response(response)
        except requests.RequestException as e:
            logger.error(f"RequestException: {e}")
            raise