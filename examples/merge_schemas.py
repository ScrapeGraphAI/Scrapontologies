from scrapontology import FileExtractor, PDFParser
from scrapontology.llm_client import LLMClient
import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

# Get the OpenAI API key from the environment variables
api_key = os.getenv("OPENAI_API_KEY")

# get current directory
curr_dirr = os.path.dirname(os.path.abspath(__file__))

def main():
    # Path to the PDF file
    pdf_name = "test.pdf"
    pdf_path = os.path.join(curr_dirr, pdf_name)

    # Create a PDFParser instance with the API key
    llm_client = LLMClient(api_key)
    pdf_parser = PDFParser(llm_client)

    # Create a FileExtractor instance with the PDF parser
    pdf_extractor = FileExtractor(pdf_path, pdf_parser)

    # Extract entities from the PDF
    entities = pdf_extractor.extract_entities()
    print("Extracted Entities:", entities)

    # Hardcoded schema to merge with
    hardcoded_schema = {
        "title": "Fund",
        "type": "object",
        "properties": {
            "costCategory": {
                "type": "object",
                "properties": {
                    "costFlag": {"type": "string"},

                }
            }
        }
    }

    # Perform merge schema function
    updated_schema = pdf_extractor.merge_schemas(hardcoded_schema)

    print("Updated Schema:", updated_schema)

if __name__ == "__main__":
    main()
