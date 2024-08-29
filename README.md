# ScrapeSchema

ScrapeSchema is a Python-based tool designed to extract entities and their associated schema from PDF files. This tool is particularly useful for those who need to analyze and organize the structure of data embedded within PDFs, enabling efficient data extraction for further processing or analysis.

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
#### Usage
After installing the prerequisites and dependencies, you can start using ScrapeSchema to extract entities and their schema from PDFs.

Here’s a basic example:
```bash
git clone https://github.com/ScrapeGraphAI/ScrapeSchema
cd ./ScrapeSchema
pip install -r requirements.txt
streamlit run main.py
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
<p align="center">
  <img src="https://i.ibb.co/7RPpsjV/temp.png" alt="example">
</p>
