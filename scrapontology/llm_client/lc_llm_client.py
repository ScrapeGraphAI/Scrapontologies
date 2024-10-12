from .llm_client import LLMClient
from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import StrOutputParser
from typing import Optional

class LcLLMClient(LLMClient):

    def __init__(self, lc_model: BaseChatModel):
        """Create a client using langchain LLM.

        Args:
            lc_model (BaseChatModel): The langchain model.
        """
        self.lc_model = lc_model | StrOutputParser()
    
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
        
        response = self.lc_model.invoke(messages)
        
        return response
        
    