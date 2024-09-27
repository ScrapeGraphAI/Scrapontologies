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
Extract the schema of the meaningful entities in this document, I want something like:\n
```json
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
```
"""

RELATIONS_PROMPT = """
Given these entitities in this format:
{entities}
Find meaningfull relations among this entities, give the relations with the following structure:
{relation_class}
Remember to give only and exclusively the Python code for generating the relations, nothing else.
You must wrap the code in triple backticks (```) like ```python ... ``` and nothing else.
You must insert the following imports in the code:\n
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

UPDATE_ENTITIES_PROMPT = """
You are tasked with updating a list of entities. You need to integrate new entities with existing ones, 
avoiding duplicates and reconciling any conflicts. Here are the rules:

1. If a new entity has the same ID as an existing entity, update the existing entity with any new or changed attributes.
2. Add any completely new entities that don't match with existing ones.
3. Try to maintain the base structure you have for the existing entities, adding new entities or updating existing entities
4. If exist entities is empty, copy the new entity into the existing entity as they are.


Existing entities:
{existing_entities}

New entities to integrate:
{new_entities}

Please provide the updated list of entities as a JSON array. Each entity should be a JSON object with 'id', 'type', and 'attributes' fields.
Provide only the JSON array, wrapped in backticks (`) like ```json ... ``` and nothing else.
"""

UPDATE_SCHEMA_PROMPT = """
You need to update the json schema with the new one, avoiding duplicates and reconciling any conflicts. Here are the rules:

1. If a new entity has the same ID as an existing entity, update the existing entity with any new or changed attributes.
2. Add any completely new entities that don't match with existing ones.
3. Try to maintain the base structure you have for the existing entities, adding new entities or updating existing entities
4. If exist entities is empty, copy the new entity into the existing entity as they are.
{existing_schema}

With this json schema:
{new_schema}

Please provide the updated json schema as a JSON object.
Provide only the JSON object, wrapped in backticks (`) like ```json ... ``` and nothing else.
"""

EXTRACT_ENTITIES_CODE_PROMPT = """
You only have to create python code for extracting the entities from the \
following json schema:\n\n{json_schema}

You have to extract the entities with the following format:
{entity_class}

Takes as reference the following python code for building the entities:
from scrapeschema import Entity

# Define entities with nested attributes
entities = [
    Entity(id='investorInformation', type='object', attributes={{
        'targetInvestors': 'string', 'investmentConsiderations': 'string'
    }}),
    Entity(id='costInformation', type='object', attributes={{
        'salesCharges': 'string', 'fundExpenses': {{'object', 'properties': {{'managementExpenseRatio': 'number', 'tradingExpenseRatio': 'number', 'totalFundExpenses': 'number'}}}}
    }}),
    Entity(id='fundInformation', type='object', attributes={{
        'fees': {{'array', 'items': 'string', 'contactInformation': {{'object', 'properties': {{'company':'string', 'address': 'string', 'phone': 'string', 'email': 'string', 'website': 'string'}}}}, 'additionalResources': {{'object', 'properties': {{'brochure': 'string', 'website': 'string'}}}}}}
    }}),
]

Remember to generate only the Python code, nothing before or after the code.
"""

FIX_CODE_PROMPT = """
The following Python code has an error. Please fix the code and provide only the corrected code without any explanations.

Error: {error}

Code to fix:
{code}

Please provide only the corrected Python code, nothing else before or after the code.
"""