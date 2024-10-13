import requests
import logging
from typing import Dict, Any, Optional, List
from typing import Any, Callable
from pydantic_core import CoreSchema, core_schema
from langchain_core.output_parsers import StrOutputParser
from langchain_core.language_models.chat_models import BaseChatModel

logger = logging.getLogger(__name__)


class LLMClient:
    def __init__(
        self,
        provider: str,
        api_key: str,
        model: str,
        base_url: str | None = None,
        llm_config: Dict[str, Any] | None = None,
    ):
        """
        Initializes the LLMClient with API credentials and settings.

        Args:
            api_key (str): The API key for authentication.
            provider (str): The provider of the language model. It should be one of "openai", "anthropic", "azure_openai", "google_vertexai", "google_genai".
            model (str): The model name to use for the language model.
            base_url (str | None): The base URL for the API. Defaults to None. It will be defaulted to the provider's base URL if not provided.
            llm_config (Dict[str, Any] | None): Additional configuration for the language model. It will be passed to the creation of the langchain language model. When using the Azure OpenAI provider, it should contain the "azure_deployment" key.
        """
        self._api_key = api_key
        self._model = model
        self._provider = provider.lower()
        self._llm_config = llm_config if llm_config is not None else {}
        self._base_url = base_url
        self._llm = self._create_llm(
            provider, api_key, model=model, base_url=base_url, llm_config=llm_config
        )

    def _create_llm(
        self,
        provider: str,
        api_key: str,
        model: str | None = None,
        base_url: str | None = None,
        llm_config: Dict[str, Any] | None = None,
    ) -> BaseChatModel:
        supported_providers = {
            "openai",
            "anthropic",
            "azure_openai",
            "google_vertexai",
            "google_genai",
        }
        if provider not in supported_providers:
            raise ValueError(
                f"provider {provider} is not supported. Supported providers are: {supported_providers}"
            )
        if provider == "openai":
            try:
                from langchain_openai import ChatOpenAI
            except ImportError:
                raise ImportError(
                    "To use the OpenAI provider, please install the langchain_openai package."
                )
            return ChatOpenAI(
                model=model, api_key=api_key, base_url=base_url, **llm_config
            )
        elif provider == "anthropic":
            try:
                from langchain_anthropic import ChatAnthropic
            except ImportError:
                raise ImportError(
                    "To use the Anthropic provider, please install the langchain_anthropic package."
                )
            return ChatAnthropic(
                model=model,
                api_key=api_key,
                **llm_config,
            )
        elif provider == "google_vertexai":
            try:
                from langchain_google_vertexai import ChatGoogleVertexAI
            except ImportError:
                raise ImportError(
                    "To use the Google Vertex AI provider, please install the langchain_google package."
                )
            return ChatGoogleVertexAI(
                model=model,
                api_key=api_key,
                base_url=base_url,
                **llm_config,
            )
        elif provider == "google_genai":
            try:
                from langchain_google_genai import ChatGoogleGenAI
            except ImportError:
                raise ImportError(
                    "To use the Google GenAI provider, please install the langchain_google package."
                )
            return ChatGoogleGenAI(
                model=model,
                api_key=api_key,
                base_url=base_url,
                **llm_config,
            )
        elif provider == "azure_openai":
            try:
                from langchain_openai import AzureChatOpenAI
            except ImportError:
                raise ImportError(
                    "To use the Azure OpenAI provider, please install the langchain_azure package."
                )
            if "azure_deployment" not in llm_config:
                raise ValueError(
                    "Azure OpenAI provider requires 'azure_deployment' in llm_config."
                )
            return AzureChatOpenAI(
                azure_deployment=llm_config["azure_deployment"],
                model=model,
                api_key=api_key,
                base_url=base_url,
                **llm_config,
            )
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    def get_api_key(self) -> str:
        return self._api_key

    def set_api_key(self, api_key: str) -> None:
        self._api_key = api_key

    def get_model(self) -> str:
        return self._model

    def set_model(self, model: str) -> None:
        self._model = model

    def get_provider(self) -> str:
        return self._provider

    def set_provider(self, provider: str) -> None:
        self._provider = provider

    def get_llm_config(self) -> Dict[str, Any]:
        return self._llm_config

    def set_llm_config(self, llm_config: Dict[str, Any]) -> None:
        self._llm_config = llm_config

    def get_base_url(self) -> str | None:
        return self._base_url

    def set_base_url(self, base_url: str | None) -> None:
        self._base_url = base_url

    def get_llm(self) -> BaseChatModel:
        return self._llm

    def set_llm(self, llm: BaseChatModel) -> None:
        self._llm = llm

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
                {"type": "image_url", "image_url": {"url": image_url}},
            ]

        try:
            chain = self._llm | StrOutputParser()
            return chain.invoke(messages)
        except requests.RequestException as e:
            logger.error(f"RequestException: {e}")
            raise
