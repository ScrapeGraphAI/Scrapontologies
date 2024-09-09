from typing import List, Dict, Any, Optional
from .base_parser import BaseParser
from ..primitives import Entity, Relation
import base64
import os
import tempfile
from pdf2image import convert_from_path
from pdf2image.exceptions import PDFInfoNotInstalledError, PDFPageCountError, PDFSyntaxError
import requests
import json
from .prompts import DIGRAPH_EXAMPLE_PROMPT, JSON_SCHEMA_PROMPT, RELATIONS_PROMPT
from PIL import Image
import inspect

def encode_image(image_path: str) -> str:
    """
    Encodes an image to a base64 string.

    Args:
        image_path (str): The path to the image file.

    Returns:
        str: The base64 encoded string of the image.
    """
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def load_pdf_as_images(pdf_path: str) -> Optional[List[Image.Image]]:
    """
    Converts a PDF file to a list of images, one per page.

    Args:
        pdf_path (str): The path to the PDF file.

    Returns:
        Optional[List[Image.Image]]: A list of images if successful, None otherwise.
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    try:
        images = convert_from_path(pdf_path)
        return images
    except (PDFInfoNotInstalledError, PDFPageCountError, PDFSyntaxError) as e:
        print(f"Error converting PDF: {e}")
        return None

def save_image_to_temp(image: Image.Image) -> str:
    """
    Saves an image to a temporary file.

    Args:
        image (Image.Image): The image to save.

    Returns:
        str: The path to the temporary file.
    """
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
        image.save(temp_file.name, 'JPEG')
        return temp_file.name

def process_pdf(pdf_path: str) -> List[str] or None: # type: ignore
    """
    Processes a PDF file and converts each page to a base64 encoded image.

    Args:
        pdf_path (str): The path to the PDF file.

    Returns:
        List[str] or None: A list of base64 encoded images if successful, None otherwise.
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    images = load_pdf_as_images(pdf_path)
    if not images:
        return None

    base64_images = []
    for page_num, image in enumerate(images, start=1):
        temp_image_path = save_image_to_temp(image)
        base64_image = encode_image(temp_image_path)
        base64_images.append(base64_image)
        os.unlink(temp_image_path)
        print(f"Processed page {page_num}")

    return base64_images

class PDFParser(BaseParser):
    """
    A parser for extracting entities and relations from PDF files.
    """

    ### init in inherited class

    def extract_entities(self, file_path: str) -> List[Entity]:
        """
        Extracts entities from a PDF file.

        Args:
            file_path (str): The path to the PDF file.

        Returns:
            List[Entity]: A list of extracted entities.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"PDF file not found: {file_path}")
        
        entities = []
        entities_json_schema = self.entities_json_schema(file_path)

        def traverse_schema(schema: Dict[str, Any], parent_id: str = None):
            if isinstance(schema, dict):
                entity_id = parent_id if parent_id else schema.get('title', 'root')
                entity_type = schema.get('type', 'object')
                attributes = schema.get('properties', {})

                if attributes:
                    entity = Entity(id=entity_id, type=entity_type, attributes=attributes)
                    entities.append(entity)

                for key, value in attributes.items():
                    traverse_schema(value, key)

        traverse_schema(entities_json_schema)
        self.entities = entities
        return entities

    def extract_relations(self, file_path: str) -> List[Relation]:
        """
        Extracts relations from a PDF file.

        Args:
            file_path (str): The path to the PDF file.

        Returns:
            List[Relation]: A list of extracted relations.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"PDF file not found: {file_path}")
        
        if not self.entities or len(self.entities) == 0:
            self.extract_entities(file_path)

        relation_class_str = inspect.getsource(Relation)
        relations_prompt = RELATIONS_PROMPT.format(entities=self.entities, relation_class=relation_class_str)
        relations_payload = {
            "model": self.model,
            "temperature": self.temperature,
            "messages": [
                {"role": "user", "content": relations_prompt}
            ],
        }



        relations_response = requests.post(self.inference_base_url, headers=self.headers, json=relations_payload)
        relations_answer_code = relations_response.json()['choices'][0]['message']['content']

        # Create a new dictionary to store the local variables
        local_vars = {}
        
        # Execute the code in the context of local_vars
        try:
            exec(relations_answer_code, globals(), local_vars)
        except Exception as e:
            print(f"Error executing relations code: {e}")
            raise ValueError(f"The language model generated invalid code: {e}") from e
        
        # Extract the relations from local_vars
        relations_answer = local_vars.get('relations', [])
        
        self.relations = relations_answer
        print(f"Extracted relations: {relations_answer_code}")

        return  self.relations
  
        
    def plot_entities_schema(self, file_path: str) -> None:
        """
        Plots the entities schema from a PDF file.

        Args:
            file_path (str): The path to the PDF file.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"PDF file not found: {file_path}")
        
        entities = []
        base64_images = process_pdf(file_path)

        if base64_images:
            page_answers = self._generate_digraph(base64_images)
            digraph_code = self._merge_digraphs_for_plot(page_answers)

            print("\nDigraph code for all pages:")
            print(digraph_code[9:-3])
            print("digraph_code_execution----------------------------------")
            exec(digraph_code[9:-3])

    def entities_json_schema(self, file_path: str) -> Dict[str, Any]:
        """
        Generates a JSON schema of entities from a PDF file.

        Args:
            file_path (str): The path to the PDF file.

        Returns:
            Dict[str, Any]: The JSON schema of entities.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"PDF file not found: {file_path}")
        
        base64_images = process_pdf(file_path)

        if base64_images:
            page_answers = self._generate_json_schema(base64_images)
            json_schema = self._merge_json_schemas(page_answers)
            json_schema = json_schema[8:-3]

            print("\n PDF JSON Schema:")
            print(json_schema)
            # json schema is a valid json schema but its a string convert it to a python dict
            entities_json_schema = json.loads(json_schema)
            return entities_json_schema

    def _generate_digraph(self, base64_images: List[str]) -> List[str]:
        """
        Generates digraph code from base64 encoded images.

        Args:
            base64_images (List[str]): A list of base64 encoded images.

        Returns:
            List[str]: A list of digraph codes for each page.
        """
        page_answers = []
        for page_num, base64_image in enumerate(base64_images, start=1):
            payload = {
                "model": self.model,
                "temperature": self.temperature,
                "messages": [
                    {
                        "role": "system",
                        "content": f"You are an AI specialized in creating python code for generating digraph graphviz, you have to create python code for creating a digraph with the relative entities with the relative attributes \
                                   (name_attribute : type) (i.e type is int,float,list[dict],dict,string,etc...) from a PDF screenshot.\
                                    in the digraph you have to represent the entities with their attributes names and types, \
                                    NOT THE VALUES OF THE ATTRIBUTES, IT'S EXTREMELY IMPORTANT. \
                                    you must provide only the code to generate the digraph, without any comments before or after the code.\
                                    Remember you don't have to insert the values of the attribute but only (name)\
                                    Remember the generated digraph must be a tree, following the hierarchy of the entities in the PDF\
                                    Remember to the deduplicate similar entities and to the remove the duplicate edges, you have to provide the best digraph\
                                    that represent the PDF document because the partial digraphs are generated from the same document but from different parts of the PDF\
                                    Remeber to follow a structure like this one: \n\n{DIGRAPH_EXAMPLE_PROMPT}"
                    },
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": f"Here a page to from a PDF screenshot (Page {page_num})"},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                        ]
                    }
                ],
            }

            response = requests.post(self.inference_base_url, headers=self.headers, json=payload)
            answer = response.json()['choices'][0]['message']['content']
            page_answers.append(f"Page {page_num}: {answer}")
            print(f"Processed page {page_num}")

        return page_answers

    def _merge_digraphs_for_plot(self, page_answers: List[str]) -> str:
        """
        Merges partial digraphs into a single digraph for plotting.

        Args:
            page_answers (List[str]): A list of partial digraph codes.

        Returns:
            str: The merged digraph code.
        """
        digraph_prompt = "Merge the partial digraphs that I provide to you merging together all the detected entities, \n\n" + "\n\n".join(page_answers) + \
            "\nYour answer digraph must be a tree and must contain only the code for a valid graphviz graph"
        digraph_payload = {
            "model": "gpt-4o",
            "temperature": 0,
            "messages": [
                {"role": "system", "content": "You are an AI that generates only valid digraph code without any comments \
                 before or after the generated code. At the end, it always shows the generated viz with \
                 dot.render('ontology_graph', format='png'). You have to provide a graph that takes as reference the following graph: {DIGRAPH_EXAMPLE_PROMPT}"},
                {"role": "user", "content": digraph_prompt}
            ],
        }

        digraph_response = requests.post("https://api.openai.com/v1/chat/completions", headers=self.headers, json=digraph_payload)
        digraph_code = digraph_response.json()['choices'][0]['message']['content']
        return digraph_code

    def _generate_json_schema(self, base64_images: List[str]) -> List[str]:
        """
        Generates JSON schema from base64 encoded images.

        Args:
            base64_images (List[str]): A list of base64 encoded images.

        Returns:
            List[str]: A list of JSON schema codes for each page.
        """
        page_answers = []
        for page_num, base64_image in enumerate(base64_images, start=1):
            payload = {
                "model": "gpt-4o",
                "temperature": 0,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": f"{JSON_SCHEMA_PROMPT} (Page {page_num})"},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                        ]
                    }
                ],
            }

            response = requests.post(self.inference_base_url, headers=self.headers, json=payload)
            answer = response.json()['choices'][0]['message']['content']
            page_answers.append(f"Page {page_num}: {answer}")
            print(f"Processed page {page_num}")

        return page_answers

    def _merge_json_schemas(self, page_answers: List[str]) -> str:
        """
        Merges partial JSON schemas into a single JSON schema.

        Args:
            page_answers (List[str]): A list of partial JSON schema codes.

        Returns:
            str: The merged JSON schema code.
        """
        digraph_prompt = "Generate a unique json schema starting from the following \
                          \n\n" + "\n\n".join(page_answers) + "\n\n \
                          Remember to provide only the json schema, without any comments before or after the json schema"

        digraph_payload = {
            "model": self.model,
            "temperature": self.temperature,
            "messages": [
                {"role": "user", "content": digraph_prompt}
            ],
        }

        digraph_response = requests.post("https://api.openai.com/v1/chat/completions", headers=self.headers, json=digraph_payload)
        digraph_code = digraph_response.json()['choices'][0]['message']['content']
        return digraph_code

