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
from .prompts import DIGRAPH_EXAMPLE_PROMPT, JSON_SCHEMA_PROMPT, RELATIONS_PROMPT, UPDATE_ENTITIES_PROMPT
from PIL import Image
import inspect
import subprocess
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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

def is_poppler_installed() -> bool:
    """Check if pdftoppm is available in the system's PATH."""
    try:
        subprocess.run(['pdftoppm', '-v'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except FileNotFoundError:
        return False

def list_directory(path: str):
    """List contents of a directory."""
    try:
        files = os.listdir(path)
        for f in files:
            logging.info(f"File in directory: {os.path.join(path, f)}")
    except Exception as e:
        logging.error(f"Error listing directory {path}: {e}")

def load_pdf_as_images(pdf_path: str) -> Optional[List[Image.Image]]:
    """
    Converts a PDF file to a list of images, one per page, using pdftoppm.

    Args:
        pdf_path (str): The path to the PDF file.

    Returns:
        Optional[List[Image.Image]]: A list of images if successful, None otherwise.
    """
    logging.info(f"Processing PDF: {pdf_path}")
    
    if not os.path.exists(pdf_path):
        logging.error(f"PDF file not found: {pdf_path}")
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    if not is_poppler_installed():
        logging.error("Poppler is not installed.")
        raise EnvironmentError("Poppler is not installed. Please install it to use this functionality.")

    with tempfile.TemporaryDirectory() as temp_dir:
        output_prefix = os.path.join(temp_dir, 'pdf_page')
        logging.info(f"Output prefix: {output_prefix}")

        command = ['pdftoppm', pdf_path, output_prefix, '-png']
        logging.info(f"Running command: {' '.join(command)}")

        try:
            subprocess.run(command, check=True, capture_output=True, text=True)
            logging.info("PDF conversion completed successfully")

            logging.info("Listing directory contents after conversion:")
            list_directory(temp_dir)

            images = []
            page_num = 1
            while True:
                image_path = f"{output_prefix}-{page_num}.png"
                if not os.path.exists(image_path):
                    break
                logging.info(f"Loading image: {image_path}")
                images.append(Image.open(image_path))
                page_num += 1

            logging.info(f"Total pages processed: {page_num - 1}")
            return images

        except subprocess.CalledProcessError as e:
            logging.error(f"Error converting PDF: {e}")
            logging.error(f"Command output: {e.output}")
            logging.error(f"Command error: {e.stderr}")
            return None

    # The temporary directory and its contents are automatically cleaned up
    # when exiting the 'with' block

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
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"PDF file not found: {file_path}")
        
        new_entities = self._extract_entities_from_pdf(file_path)
        return self.update_entities(new_entities)

    def _extract_entities_from_pdf(self, file_path: str) -> List[Entity]:
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
        return entities

    def update_entities(self, new_entities: List[Entity]) -> List[Entity]:
        existing_entities = self._entities

        # Prepare the prompt for the LLM
        prompt = UPDATE_ENTITIES_PROMPT.format(
            existing_entities=json.dumps([e.__dict__ for e in existing_entities], indent=2),
            new_entities=json.dumps([e.__dict__ for e in new_entities], indent=2)
        )

        # Use _get_llm_response instead of direct API call
        response = self._get_llm_response(prompt)
        response = response[8:-3]  # Remove ```json and ``` if present
        
        try:
            updated_entities_data = json.loads(response)
            updated_entities = [Entity(**entity_data) for entity_data in updated_entities_data]
            
            # Update the parser's entities
            self._entities = updated_entities
            
            print(f"Entities updated. New count: {len(updated_entities)}")
            return updated_entities
        except json.JSONDecodeError:
            print("Error: Unable to parse the LLM response.")
            return existing_entities

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
        
        if not self._entities or len(self._entities) == 0:
            self.extract_entities(file_path)

        relation_class_str = inspect.getsource(Relation)
        relations_prompt = RELATIONS_PROMPT.format(entities=self._entities, relation_class=relation_class_str)
        
        # Use _get_llm_response instead of direct API call
        relations_answer_code = self._get_llm_response(relations_prompt)

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
        
        self._relations = relations_answer
        print(f"Extracted relations: {relations_answer_code}")

        return  self._relations
  
        
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
        page_answers = []
        for page_num, base64_image in enumerate(base64_images, start=1):
            prompt = f"You are an AI specialized in creating python code for generating digraph graphviz, you have to create python code for creating a digraph with the relative entities with the relative attributes \
                       (name_attribute : type) (i.e type is int,float,list[dict],dict,string,etc...) from a PDF screenshot.\
                        in the digraph you have to represent the entities with their attributes names and types, \
                        NOT THE VALUES OF THE ATTRIBUTES, IT'S EXTREMELY IMPORTANT. \
                        you must provide only the code to generate the digraph, without any comments before or after the code.\
                        Remember you don't have to insert the values of the attribute but only (name)\
                        Remember the generated digraph must be a tree, following the hierarchy of the entities in the PDF\
                        Remember to the deduplicate similar entities and to the remove the duplicate edges, you have to provide the best digraph\
                        that represent the PDF document because the partial digraphs are generated from the same document but from different parts of the PDF\
                        Remeber to follow a structure like this one: \n\n{DIGRAPH_EXAMPLE_PROMPT}\n\nHere a page to from a PDF screenshot (Page {page_num})"

            # Use _get_llm_response with image
            answer = self._get_llm_response(prompt, image_url=f"data:image/jpeg;base64,{base64_image}")
            page_answers.append(f"Page {page_num}: {answer}")
            print(f"Processed page {page_num}")

        return page_answers

    def _merge_digraphs_for_plot(self, page_answers: List[str]) -> str:
        digraph_prompt = "Merge the partial digraphs that I provide to you merging together all the detected entities, \n\n" + "\n\n".join(page_answers) + \
            "\nYour answer digraph must be a tree and must contain only the code for a valid graphviz graph"
        
        # Use _get_llm_response instead of direct API call
        digraph_code = self._get_llm_response(digraph_prompt)
        return digraph_code

    def _generate_json_schema(self, base64_images: List[str]) -> List[str]:
        page_answers = []
        for page_num, base64_image in enumerate(base64_images, start=1):
            prompt = f"{JSON_SCHEMA_PROMPT} (Page {page_num})"
            
            # Use _get_llm_response with image
            answer = self._get_llm_response(prompt, image_url=f"data:image/jpeg;base64,{base64_image}")
            page_answers.append(f"Page {page_num}: {answer}")
            print(f"Processed page {page_num}")

        return page_answers

    def _merge_json_schemas(self, page_answers: List[str]) -> str:
        digraph_prompt = "Generate a unique json schema starting from the following \
                          \n\n" + "\n\n".join(page_answers) + "\n\n \
                          Remember to provide only the json schema, without any comments before or after the json schema"

        # Use _get_llm_response instead of direct API call
        digraph_code = self._get_llm_response(digraph_prompt)
        return digraph_code

    def _get_llm_response(self, prompt: str, image_url: str = None) -> str:
        """Get a response from the language model."""
        messages = [{"role": "user", "content": prompt}]
        
        if image_url:
            messages[0]["content"] = [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": image_url}}
            ]

        payload = {
            "model": self._model,
            "temperature": self._temperature,
            "messages": messages,
        }
        response = requests.post(self._inference_base_url, headers=self._headers, json=payload)
        return response.json()['choices'][0]['message']['content']

