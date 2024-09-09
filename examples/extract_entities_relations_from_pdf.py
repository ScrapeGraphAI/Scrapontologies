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
    pdf_extractor = FileExtractor(pdf_path, pdf_parser)

    # Extract entities from the PDF
    entities = pdf_extractor.extract_entities()

    print(entities)

    relations = pdf_extractor.extract_relations()
    print(relations)
    

if __name__ == "__main__":
    main()