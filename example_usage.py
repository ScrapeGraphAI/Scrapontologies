from scrapeschema import FileExtractor, PDFParser
import os
from dotenv import load_dotenv

def main():
    load_dotenv()  # Load environment variables from .env file
    api_key = os.getenv("OPENAI_API_KEY")

    # Path to your PDF file
    pdf_path = "./test.pdf"

    # Create a PDFParser instance with the API key
    pdf_parser = PDFParser(api_key)

    # Create a FileExtraxctor instance with the PDF parser
    scraper = FileExtractor(pdf_path, pdf_parser)

    # Extract entities from the PDF
    entities = scraper.extract_entities()

    print(entities)


    TODO = """"    # Print the extracted entities
    print("Extracted Entities:")
    for entity in entities:
        print(f"Entity: {entity}")

    # Extract relations from the PDF
    relations = scraper.extract_relations()

    # Print the extracted relations
    print("\nExtracted Relations:")
    for relation in relations:
        print(f"Relation: {relation}")
"""
if __name__ == "__main__":
    main()