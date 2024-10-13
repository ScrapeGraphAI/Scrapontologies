from scrapontology import PDFParser
from scrapontology.llm_client import LLMClient
from dotenv import load_dotenv
import os

def main():
    # Load environment variables
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")

    # Get the path to the tests directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    tests_dir = os.path.join(script_dir, 'tests')  # Adjust the path as needed
    
    # Get all files in the tests directory
    test_files = [os.path.join(tests_dir, f) for f in os.listdir(tests_dir) if os.path.isfile(os.path.join(tests_dir, f))]
    
    # Print the paths of all files in the tests directory
    for file_path in test_files:
        print(f"Test file: {file_path}")
    
    # For this example, we'll use the first test file (if any exist)
    pdf_path = test_files[0] if test_files else None
    
    if not pdf_path:
        raise FileNotFoundError("No test files found in the tests directory.")

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
    
    # Create an LLMClient instance
    llm_client = LLMClient(**llm_client_config)

    # Create a PDFParser instance with the LLMClient
    pdf_parser = PDFParser(llm_client)

    # Generate the JSON schema first
    pdf_parser.generate_json_schema(pdf_path)

    # Extract entities with data from the PDF
    entities_with_data = pdf_parser.extract_entities_from_file(test_files)

    # Now you can use entities_with_data to upload to your database
    for record in entities_with_data:
        print(f"Record ID: {record.id}")
        for entity in record.entities:
            print(f"Entity ID: {entity.id}")
            print(f"Attributes: {entity.attributes}")

if __name__ == "__main__":
    main()
