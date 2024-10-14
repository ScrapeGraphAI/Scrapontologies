from scrapontology import FileExtractor, PDFParser
from scrapontology.llm_client import LLMClient
from scrapontology.db_client import PostgresDBClient
import os
from dotenv import load_dotenv

def main():
    # Load environment variables
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")

    # Get current directory and set PDF path
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    test_dir = os.path.join(curr_dir, 'tests')
    pdf_name = "test.pdf"
    pdf_path = os.path.join(test_dir, pdf_name)

    # Create LLMClient and PDFParser instances
    llm_client = LLMClient(api_key)
    pdf_parser = PDFParser(llm_client)

    # Create DBClient instance
    postgres_host = os.getenv("POSTGRES_HOST")
    postgres_port = os.getenv("POSTGRES_PORT")
    postgres_db = os.getenv("POSTGRES_DB")
    postgres_user = os.getenv("POSTGRES_USER")
    postgres_password = os.getenv("POSTGRES_PASSWORD")
    db_client = PostgresDBClient(postgres_host, postgres_port, postgres_db, postgres_user, postgres_password)

    # Create FileExtractor instance
    pdf_extractor = FileExtractor(pdf_path, pdf_parser, db_client)

    # Generate JSON schema from the PDF
    json_schema = pdf_extractor.generate_entities_json_schema()
    print("Generated JSON Schema:")
    print(json_schema)

    # Create tables in the database
    pdf_extractor.create_tables()

    print("Tables created successfully in the PostgreSQL database.")

if __name__ == "__main__":
    main()