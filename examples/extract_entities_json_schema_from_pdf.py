from scrapontology import FileExtractor, PDFParser
from scrapontology.llm_client import LLMClient
import os
from dotenv import load_dotenv

def main():
    load_dotenv()  # Load environment variables from .env file
    api_key = os.getenv("OPENAI_API_KEY")

    # get current directory
    curr_dirr = os.path.dirname(os.path.abspath(__file__))
    pdf_name = "test.pdf"
    pdf_path = os.path.join(curr_dirr, pdf_name)

    # Create a LLMClient instance with the API key
    llm_client = LLMClient(api_key)

    # Create a PDFParser instance with the LLMClient
    pdf_parser = PDFParser(llm_client)

    # Create a FileExtractor instance with the PDF parser
    pdf_extractor = FileExtractor(pdf_path, pdf_parser)

    # Extract entities JSON schema from the PDF
    entities_json_schema = pdf_extractor.entities_json_schema()


if __name__ == "__main__":
    main()

# Expected Output:
'''
{
  "$schema": "http://json-schema.org/schema#",
  "title": "Fund Document",
  "type": "object",
  "properties": {
    "fundFacts": {
      "type": "object",
      "properties": {
        "fundName": {
          "type": "string"
        },
        "date": {
          "type": "string",
          "format": "date"
        },
        "fundManager": {
          "type": "string"
        },
        "portfolioManager": {
          "type": "string"
        },
        "subAdvisor": {
          "type": "string"
        },
        "minimumInvestment": {
          "type": "string"
        },
        "fundCode": {
          "type": "string"
        },
        "dateSeriesStarted": {
          "type": "string",
          "format": "date"
        },
        "totalValueOfFund": {
          "type": "string"
        },
        "managementExpenseRatio": {
          "type": "string"
        },
        "top10Investments": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "investmentName": {
                "type": "string"
              },
              "percentage": {
                "type": "string"
              }
            },
            "required": [
              "investmentName",
              "percentage"
            ]
          }
        },
        "totalNumberOfInvestments": {
          "type": "integer"
        },
        "investmentMix": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "category": {
                "type": "string"
              },
              "percentage": {
                "type": "string"
              }
            },
            "required": [
              "category",
              "percentage"
            ]
          }
        },
        "riskRating": {
          "type": "string"
        },
        "performance": {
          "type": "string"
        }
      },
      "required": [
        "fundName",
        "date",
        "fundManager",
        "portfolioManager",
        "subAdvisor",
        "minimumInvestment",
        "fundCode",
        "dateSeriesStarted",
        "totalValueOfFund",
        "managementExpenseRatio",
        "top10Investments",
        "totalNumberOfInvestments",
        "investmentMix",
        "riskRating",
        "performance"
      ]
    },
    "fund": {
      "type": "object",
      "properties": {
        "title": {
          "type": "string"
        },
        "yearByYearReturns": {
          "type": "object",
          "properties": {
            "description": {
              "type": "string"
            },
            "chart": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "year": {
                    "type": "integer"
                  },
                  "returnPercentage": {
                    "type": "number"
                  }
                },
                "required": [
                  "year",
                  "returnPercentage"
                ]
              }
            }
          },
          "required": [
            "description",
            "chart"
          ]
        },
        "bestAndWorst3MonthReturns": {
          "type": "object",
          "properties": {
            "description": {
              "type": "string"
            },
            "returns": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "type": {
                    "type": "string"
                  },
                  "percentage": {
                    "type": "number"
                  },
                  "date": {
                    "type": "string",
                    "format": "date"
                  },
                  "investmentValue": {
                    "type": "string"
                  }
                },
                "required": [
                  "type",
                  "percentage",
                  "date",
                  "investmentValue"
                ]
              }
            }
          },
          "required": [
            "description",
            "returns"
          ]
        },
        "averageReturn": {
          "type": "object",
          "properties": {
            "description": {
              "type": "string"
            },
            "value": {
              "type": "string"
            }
          },
          "required": [
            "description",
            "value"
          ]
        },
        "whoIsThisFor": {
          "type": "object",
          "properties": {
            "description": {
              "type": "string"
            },
            "criteria": {
              "type": "array",
              "items": {
                "type": "string"
              }
            }
          },
          "required": [
            "description",
            "criteria"
          ]
        },
        "taxInformation": {
          "type": "object",
          "properties": {
            "description": {
              "type": "string"
            }
          },
          "required": [
            "description"
          ]
        },
        "costInformation": {
          "type": "object",
          "properties": {
            "description": {
              "type": "string"
            },
            "salesCharges": {
              "type": "string"
            },
            "fundExpenses": {
              "type": "object",
              "properties": {
                "description": {
                  "type": "string"
                },
                "MER": {
                  "type": "object",
                  "properties": {
                    "description": {
                      "type": "string"
                    },
                    "rate": {
                      "type": "number"
                    }
                  },
                  "required": [
                    "description",
                    "rate"
                  ]
                },
                "TER": {
                  "type": "object",
                  "properties": {
                    "description": {
                      "type": "string"
                    },
                    "rate": {
                      "type": "number"
                    }
                  },
                  "required": [
                    "description",
                    "rate"
                  ]
                },
                "totalExpenses": {
                  "type": "number"
                }
              },
              "required": [
                "description",
                "MER",
                "TER",
                "totalExpenses"
              ]
            },
            "trailingCommission": {
              "type": "string"
            }
          },
          "required": [
            "description",
            "salesCharges",
            "fundExpenses",
            "trailingCommission"
          ]
        }
      },
      "required": [
        "title",
        "yearByYearReturns",
        "bestAndWorst3MonthReturns",
        "averageReturn",
        "whoIsThisFor",
        "taxInformation",
        "costInformation"
      ]
    },
    "otherFees": {
      "type": "object",
      "properties": {
        "switchFee": {
          "type": "string",
          "description": "Fee for switching units"
        },
        "shortTermTradingFee": {
          "type": "string",
          "description": "Fee for short-term trading"
        },
        "feeBasedAccountFee": {
          "type": "string",
          "description": "Fee for fee-based accounts"
        }
      },
      "required": [
        "switchFee",
        "shortTermTradingFee",
        "feeBasedAccountFee"
      ]
    },
    "changeOfMind": {
      "type": "object",
      "properties": {
        "withdrawalRights": {
          "type": "string",
          "description": "Rights to withdraw from an agreement"
        },
        "cancellationRights": {
          "type": "string",
          "description": "Rights to cancel a purchase"
        }
      },
      "required": [
        "withdrawalRights",
        "cancellationRights"
      ]
    },
    "contactInformation": {
      "type": "object",
      "properties": {
        "companyName": {
          "type": "string",
          "description": "Name of the company"
        },
        "address": {
          "type": "string",
          "description": "Company address"
        },
        "phone": {
          "type": "string",
          "description": "Contact phone number"
        },
        "email": {
          "type": "string",
          "description": "Contact email"
        },
        "website": {
          "type": "string",
          "description": "Company website"
        }
      },
      "required": [
        "companyName",
        "address",
        "phone",
        "email",
        "website"
      ]
    },
    "additionalInformation": {
      "type": "object",
      "properties": {
        "brochure": {
          "type": "string",
          "description": "Information about the brochure"
        },
        "website": {
          "type": "string",
          "description": "Website for additional information"
        }
      },
      "required": [
        "brochure",
        "website"
      ]
    }
  },
  "required": [
    "fundFacts",
    "fund",
    "otherFees",
    "changeOfMind",
    "contactInformation",
    "additionalInformation"
  ]
}
'''