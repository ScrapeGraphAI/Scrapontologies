from scrapeschema # import what you need from the library
import os
from dotenv import load_dotenv

def main():
    load_dotenv()  # Load environment variables from .env file
    api_key = os.getenv("OPENAI_API_KEY")

    # Path to your file
    file_path = "path/to/your/file"


if __name__ == "__main__":
    main()