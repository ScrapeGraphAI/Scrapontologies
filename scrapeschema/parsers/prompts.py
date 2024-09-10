DIGRAPH_EXAMPLE_PROMPT = """
    from graphviz import Digraph

    dot = Digraph(comment='Portfolio Structure')

    # Root
    dot.node('ROOT', 'ROOT\\nportfolio: object')

    # Portfolio node
    dot.node('portfolio', 'portfolio\\nname: string\\nseries: string\\nfees: object\\nwithdrawalRights: object\\n'
                        'contactInformation: object\\nyearByYearReturns: object[]\\nbestWorstReturns: object[]\\n'
                        'averageReturn: string\\ntargetInvestors: string[]\\ntaxInformation: string')

    # Connect Root to Portfolio
    dot.edge('ROOT', 'portfolio')

    # Nodes under Portfolio
    dot.node('fees', 'fees\\nsalesCharges: string\\nfundExpenses: object\\ntrailingCommissions: string')
    dot.node('withdrawalRights', 'withdrawalRights\\ntimeLimit: string\\nconditions: string[]')
    dot.node('contactInformation', 'contactInformation\\ncompanyName: string\\naddress: string\\nphone: string\\n'
                                    'email: string\\nwebsite: string')
    dot.node('yearByYearReturns', 'yearByYearReturns\\nyear: string\\nreturn: string')
    dot.node('bestWorstReturns', 'bestWorstReturns\\ntype: string\\nreturn: string\\ndate: string\\ninvestmentValue: string')

    # Connect Portfolio to its components
    dot.edge('portfolio', 'fees')
    dot.edge('portfolio', 'withdrawalRights')
    dot.edge('portfolio', 'contactInformation')
    dot.edge('portfolio', 'yearByYearReturns')
    dot.edge('portfolio', 'bestWorstReturns')

    # Sub-components
    dot.node('fundExpenses', 'fundExpenses\\nmanagementExpenseRatio: string\\ntradingExpenseRatio: string\\n'
                            'totalExpenses: string')

    # Connect sub-components
    dot.edge('fees', 'fundExpenses')
"""

JSON_SCHEMA_PROMPT = """
Extract the schema of the meaningful entities in this document, I want something like:
{ 
    "$schema": "http://json-schema.org/schema#",
    "title": "Payslip",
  "type": "object",
  "properties": {
    "payslip": {
      "type": "object",
      "properties": {
        "employee": {
          "type": "object",
          "properties": {
            "name": {
              "type": "string"
            },
            "qualification": {
              "type": "string"
            },
            "position": {
              "type": "string"
            }
          },
          "required": [
            "name",
            "qualification",
            "position"
          ]
        },
        "workDetails": {
          "type": "object",
          "properties": {
            "workedHours": {
              "type": "integer"
            },
            "holidayHours": {
              "type": "integer"
            },
            "workedDays": {
              "type": "integer"
            }
          },
          "required": [
            "workedHours",
            "holidayHours",
            "workedDays"
          ]
        },
        "basePay": {
          "type": "number"
        },
        "contingency": {
          "type": "number"
        },
        "levelContract": {
          "type": "number"
        },
        "totalCompensation": {
          "type": "number"
        },
        "deductions": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "description": {
                "type": "string"
              },
              "percentage": {
                "type": "number"
              },
              "taxableAmount": {
                "type": "number"
              },
              "withholdings": {
                "type": "number"
              },
              "earnings": {
                "type": "number"
              }
            },
            "required": [
              "description",
              "percentage",
              "taxableAmount",
              "withholdings",
              "earnings"
            ]
          }
        },
        "netIncome": {
          "type": "number"
        },
        "totalNet": {
          "type": "number"
        }
      },
      "required": [
        "employee",
        "workDetails",
        "basePay",
        "contingency",
        "levelContract",
        "totalCompensation",
        "deductions",
        "netIncome",
        "totalNet"
      ]
    }
  },
  "required": [
    "payslip"
  ]
}
"""

RELATIONS_PROMPT = """
Given these entitities in this format:
{entities}
Find meaningfull relations among this entities, give the relations with the following structure:
{relation_class}
Remember to give only and exclusively the Python code for generating the relations, nothing else.
No intro, no code block, no nothing, just the code and remember to insert the following imports:
from dataclasses import dataclass
from typing import Any, Dict, List
"""

DELETE_PROMPT = """
Based on the following description, determine if the user wants to delete an entity or a relation,
and provide the ID of the item to be deleted. If it's not clear, ask for clarification.

Current entities: {entities}
Current relations: {relations}

User description: {item_description}

Respond with the following JSON structure:
    Type: "[Entity/Relation]",
    ID: "[ID of the item to delete, or 'None' if unclear]",
    Clarification: "[Any necessary clarification question, or 'None' if clear]"

Remember to provide only the JSON, nothing else before or after the JSON.
"""