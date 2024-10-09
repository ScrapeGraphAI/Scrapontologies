from scrapontology import PDFParser
from scrapontology.llm_client import LLMClient
from dotenv import load_dotenv
import os

def main():
    # Load environment variables
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")

    # Path to your PDF file
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    pdf_name = "test.pdf"
    pdf_path = os.path.join(curr_dir, pdf_name)

    # Create an LLMClient instance
    llm_client = LLMClient(api_key)

    # Create a PDFParser instance with the LLMClient
    pdf_parser = PDFParser(llm_client)

    # Generate the JSON schema first
    pdf_parser.generate_json_schema(pdf_path)

    # Extract entities with data from the PDF
    entities_with_data = pdf_parser.extract_entities_from_file(pdf_path)

    # Now you can use entities_with_data to upload to your database
    for entity in entities_with_data:
        print(f"Entity ID: {entity.id}")
        print(f"Attributes: {entity.attributes}")

if __name__ == "__main__":
    main()
