# ScrapeOntology

ScrapeOntology is a Python-based libraey designed to extract entities and relationship from files. 
The generate schemas can be used to infer from document to use for tables in a database or for generating knowledge graph.

## Features

- **Entity Extraction**: Automatically identifies and extracts entities from PDF files.
- **Schema Generation**: Constructs a schema based and structure of the extracted entities.
- **Visualization**: Leverages Graphviz to visualize the extracted schema.

## Quick Start

### Prerequisites

Before you begin, ensure you have the following installed on your system:

- **Python**: Make sure Python 3.9+ is installed.
- **Graphviz**: This tool is necessary for visualizing the extracted schema.

#### MacOS Installation

To install Graphviz on MacOS, use the following command:

```bash
brew install graphviz
```

#### Linux Installation

To install Graphviz on Linux, use the following command:

```bash
sudo apt install graphviz
```
#### Installation
After installing the prerequisites and dependencies, you can start using ScrapeSchema to extract entities and their schema from PDFs.

Here’s a basic example:
```bash
git clone https://github.com/ScrapeGraphAI/ScrapeSchema
pip install -r requirements.txt
```

## Usage

```python
from scrapeschema import FileExtractor, PDFParser
import os
from dotenv import load_dotenv

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
```
## Output
```json
{
  "ROOT": {
    "portfolio": {
      "type": "object",
      "properties": {
        "name": {
          "type": "string"
        },
        "series": {
          "type": "string"
        },
        "fees": {
          "type": "object",
          "properties": {
            "salesCharges": {
              "type": "string"
            },
            "fundExpenses": {
              "type": "object",
              "properties": {
                "managementExpenseRatio": {
                  "type": "string"
                },
                "tradingExpenseRatio": {
                  "type": "string"
                },
                "totalExpenses": {
                  "type": "string"
                }
              }
            },
            "trailingCommissions": {
              "type": "string"
            }
          }
        },
        "withdrawalRights": {
          "type": "object",
          "properties": {
            "timeLimit": {
              "type": "string"
            },
            "conditions": {
              "type": "array",
              "items": {
                "type": "string"
              }
            }
          }
        },
        "contactInformation": {
          "type": "object",
          "properties": {
            "companyName": {
              "type": "string"
            },
            "address": {
              "type": "string"
            },
            "phone": {
              "type": "string"
            },
            "email": {
              "type": "string"
            },
            "website": {
              "type": "string"
            }
          }
        },
        "yearByYearReturns": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "year": {
                "type": "string"
              },
              "return": {
                "type": "string"
              }
            }
          }
        },
        "bestWorstReturns": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "type": {
                "type": "string"
              },
              "return": {
                "type": "string"
              },
              "date": {
                "type": "string"
              },
              "investmentValue": {
                "type": "string"
              }
            }
          }
        },
        "averageReturn": {
          "type": "string"
        },
        "targetInvestors": {
          "type": "array",
          "items": {
            "type": "string"
          }
        },
        "taxInformation": {
          "type": "string"
        }
      }
    }
  }
}
```
