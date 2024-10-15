from scrapontologies import FileExtractor, PDFParser
from scrapontologies.llm_client import LLMClient
import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

# Get the OpenAI API key from the environment variables
api_key = os.getenv("OPENAI_API_KEY")

def main():
    # Path to the PDF file
    pdf_name = "test.pdf"
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    pdf_path = os.path.join(curr_dir, pdf_name)

    # Create an LLMClient instance
    # ************************************************
    # Define the configuration for the LLMClient here
    # ************************************************
    llm_client_config = {
        "provider": "openai",
        "api_key": api_key,
        "model": "gpt-4o-2024-08-06",
        "llm_config": {
            "temperature": 0.0,
        }
    }
    
    llm_client = LLMClient(**llm_client_config)

    # Create a PDFParser instance with the LLMClient
    pdf_parser = PDFParser(llm_client)

    # Create a FileExtractor instance with the PDF parser
    pdf_extractor = FileExtractor(pdf_path, pdf_parser)

    # Define a custom prompt to extract only financial-related entities
    custom_prompt = """
    Insert in the schema only info related to the top 10 investment.
    """

    # Extract entities from the PDF using the custom prompt
    entities = pdf_extractor.extract_entities_schema(prompt=custom_prompt)
    print("Extracted Entities:", entities)

if __name__ == "__main__":
    main()
