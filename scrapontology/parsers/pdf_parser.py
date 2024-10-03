from typing import List, Dict, Any, Optional, Literal
from .base_parser import BaseParser
from ..primitives import Entity, Relation
import base64
import os
import tempfile
import json
from .prompts import DIGRAPH_EXAMPLE_PROMPT, JSON_SCHEMA_PROMPT, RELATIONS_PROMPT, UPDATE_ENTITIES_PROMPT, EXTRACT_ENTITIES_CODE_PROMPT, FIX_CODE_PROMPT
from PIL import Image
import inspect
import subprocess
import logging
import re
from ..llm_client import LLMClient
from requests.exceptions import ReadTimeout
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel
from typing import Optional, List

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
                
                # Using context manager to ensure the file is closed properly after use
                with Image.open(image_path) as img:
                    # Append a copy of the image to the list, closing the original image
                    images.append(img.copy())
                page_num += 1

            return images

        except subprocess.CalledProcessError as e:
            logging.error(f"Error converting PDF: {e}")
            logging.error(f"Command output: {e.output}")
            logging.error(f"Command error: {e.stderr}")
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


class PDFParser(BaseParser):
    """
    A parser for extracting entities and relations from PDF files.
    """

    def __init__(self, llm_client: LLMClient):
        """
        Initializes the PDFParser with an API key and LLM settings.

        Args:
            api_key (str): The API key for authentication.
            inference_base_url (str): The base URL for the inference API.
            model (str): The model to use for inference.
            temperature (float): The temperature setting for the model.
        """

        super().__init__(llm_client)

        class State_Entities(BaseModel):
            file_path: Optional[str] = None
            user_prompt_for_filter: Optional[str] = None
            entities_code: Optional[str] = None
            entity_class: Optional[str] = None 
            temp_entities: Optional[List[Entity]] = None
            entities: Optional[List[Entity]] = None
            base64_images: Optional[List[str]] = None
            page_answers: Optional[List[str]] = None
            entities_json_schema: Optional[Dict[str, Any]] = None

        # initialize the state with the avaible field at the start, the entity class definition
        self.state_entities =  State_Entities()
        self.state_entities.entity_class = inspect.getsource(Entity)

        #nodes for the entities graph
        builder_for_entities = StateGraph(State_Entities)
        builder_for_entities.add_node("process_pdf", self._process_pdf)
        builder_for_entities.add_node("generate_json_schemas", self._generate_json_schemas)
        builder_for_entities.add_node("merge_json_schemas", self._merge_json_schemas)
        builder_for_entities.add_node("generate_entities_code", self._generate_entities_code)
        builder_for_entities.add_node("execute_entities_code", self._execute_entities_code)
        builder_for_entities.add_node("assign_entities", self.update_entities)

        #edges for the entities graph
        builder_for_entities.add_edge(START, "process_pdf")
        builder_for_entities.add_edge("process_pdf", "generate_json_schemas")
        builder_for_entities.add_edge("generate_json_schemas", "merge_json_schemas")
        builder_for_entities.add_edge("merge_json_schemas", "generate_entities_code")
        builder_for_entities.add_edge("generate_entities_code","execute_entities_code")
        builder_for_entities.add_edge("execute_entities_code", "assign_entities")
        builder_for_entities.add_edge("assign_entities", END)

        self.graph_for_entities = builder_for_entities.compile()

        class State_Relations(BaseModel):
            entities: Optional[List[Entity]] = None
            user_prompt_for_filter: Optional[str] = None
            relations_code: Optional[str] = None
            relation_class: Optional[str] = None
            relations: Optional[List[Relation]] = None

        self.state_relations = State_Relations()
        self.state_relations.relation_class = inspect.getsource(Relation)

        builder_for_relations = StateGraph(State_Relations)
        builder_for_relations.add_node("extract_relations", self._extract_relations_code)
        builder_for_relations.add_node("execute_relations_code", self._execute_relations_code)
        builder_for_relations.add_edge(START, "extract_relations")
        builder_for_relations.add_edge("extract_relations", "execute_relations_code")
        builder_for_relations.add_edge("execute_relations_code", END)

        self.graph_for_relations = builder_for_relations.compile()

        class State_Entities_Json_Schema(BaseModel):
            file_path: Optional[str] = None
            base64_images: Optional[List[str]] = None
            page_answers: Optional[List[str]] = None
            entities_json_schema: Optional[Dict[str, Any]] = None

        self.state_entities_json_schema = State_Entities_Json_Schema()
    

        builder_for_entities_json_schema = StateGraph(State_Entities_Json_Schema)
        builder_for_entities_json_schema.add_node("process_pdf", self._process_pdf)
        builder_for_entities_json_schema.add_node("generate_json_schemas", self._generate_json_schemas)
        builder_for_entities_json_schema.add_node("merge_json_schemas", self._merge_json_schemas)
        builder_for_entities_json_schema.add_edge(START, "process_pdf")
        builder_for_entities_json_schema.add_edge("process_pdf", "generate_json_schemas")
        builder_for_entities_json_schema.add_edge("generate_json_schemas", "merge_json_schemas")
        builder_for_entities_json_schema.add_edge("merge_json_schemas", END)

        self.graph_for_entities_json_schema = builder_for_entities_json_schema.compile()

    
    def _generate_entities_code(self, *_) -> str:
        prompt = EXTRACT_ENTITIES_CODE_PROMPT.format(json_schema=str(self.state_entities.entities_json_schema) , entity_class=str(inspect.getsource(Entity)))
        entities_code = self.llm_client.get_response(prompt)

        # extract the python code from the entities_code remove the ```python and ```
        entities_code = entities_code.replace("```python", "").replace("```", "")
        self.state_entities.entities_code = entities_code
        return self.state_entities
    
    def _execute_entities_code(self, *_):
        local_vars = {}
        max_retries = 3
        retry_count = 0
        while retry_count < max_retries:
            try:
                exec(self.state_entities.entities_code, globals(), local_vars)
                break  # If successful, exit the loop
            except Exception as e:
                logging.error(f"Error executing entities code (attempt {retry_count + 1}): {e}")
                if retry_count == max_retries - 1:
                    logging.error("Max retries reached. Unable to execute entities code.")
                    break
                fix_code_prompt = FIX_CODE_PROMPT.format(code=self.state_entities.entities_code, error=str(e))
                fixed_code = self.llm_client.get_response(fix_code_prompt)
                fixed_code = fixed_code.replace("```python", "").replace("```", "")
                self.state_entities.entities_code = fixed_code  # Update entities_code with the fixed version
                retry_count += 1
        
        new_entities = local_vars.get('entities', [])
        self.state_entities.temp_entities = new_entities
        
        return self.state_entities

    
    def extract_entities(self, file_path: str, prompt: Optional[str] = None) -> List[Entity]:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"PDF file not found: {file_path}")
        
        self.state_entities.file_path = file_path

        if prompt:
            self.state_entities.user_prompt_for_filter = prompt


        self.graph_for_entities.invoke(self.state_entities)

        return self.state_entities.entities

    

    def _extract_json_content(self, input_string: str) -> str:
    # Use regex to match content between ```json and ```
        match = re.search(r"```json\s*(.*?)\s*```", input_string, re.DOTALL)
        if match:
            return match.group(1).strip()
        return ""
    
    def _extract_python_content(self, input_string: str) -> str:
        # Use regex to match content between ```python and ```
        match = re.search(r"```python\s*(.*?)\s*```", input_string, re.DOTALL)
        if match:
            return match.group(1).strip()
        return ""

    def update_entities(self, *_):
        existing_entities = self._entities

        prompt = UPDATE_ENTITIES_PROMPT.format(
            existing_entities=json.dumps([e.__dict__ for e in existing_entities], indent=2),
            new_entities=json.dumps([e.__dict__ for e in self.state_entities.temp_entities], indent=2)
        )

        response = self.llm_client.get_response(prompt)
        response = response.strip().strip('```json').strip('```')

        try:
            updated_entities_data = json.loads(response)
            updated_entities = [Entity(**entity_data) for entity_data in updated_entities_data]
            
            # Update the parser's entities
            self.state_entities.entities = updated_entities
            self._entities = updated_entities
            
            # print the updated entities
            logging.info("Updated entities:")
            for entity in updated_entities:
                logging.info(entity.__dict__)
            logging.info(f"Entities updated. New count: {len(updated_entities)}")
            return self.state_entities
        except json.JSONDecodeError as e:
            logging.error(f"JSONDecodeError: {e}")
            logging.error("Error: Unable to parse the LLM response.")
            return self.state_entities

    def extract_relations(self, file_path: Optional[str] = None, prompt: Optional[str] = None) -> List[Relation]:
        """
        Extracts relations from a PDF file.

        Args:
            file_path (str): The path to the PDF file.

        Returns:
            List[Relation]: A list of extracted relations.
        """
        if file_path is not None and not os.path.exists(file_path):
            logging.error(f"PDF file not found: {file_path}")
            raise FileNotFoundError(f"PDF file not found: {file_path}")
        
        if not self._entities or len(self._entities) == 0:
            logging.error("Entities not found. Please extract entities first.")
            raise ValueError("Entities not found. Please extract entities first.")

        self.graph_for_relations.invoke(self.state_relations)

        return self.state_relations.relations


    def _extract_relations_code(self, *_):
        relation_class_str = inspect.getsource(Relation)
        relations_prompt = RELATIONS_PROMPT.format(
            entities=json.dumps([e.__dict__ for e in self._entities], indent=2),
            relation_class=self.state_relations.relation_class
        )
        if self.state_relations.user_prompt_for_filter:
            #append to the relations_prompt the prompt
            relations_prompt += f"\n\n Extract only the relations that are required from the following user prompt:\n\n{self.state_relations.user_prompt_for_filter}"


        relations_code_answer = self.llm_client.get_response(relations_prompt)
        relations_code = self._extract_python_content(relations_code_answer)
        self.state_relations.relations_code = relations_code
        return self.state_relations

    def _execute_relations_code(self, *_):
        local_vars = {}
        try:
            exec(self.state_relations.relations_code, globals(), local_vars)
        except Exception as e:
            logging.error(f"Error executing relations code: {e}")
            raise ValueError(f"The language model generated invalid code: {e}") from e

        relations_answer = local_vars.get('relations', [])
        self._relations = relations_answer
        self.state_relations.relations = relations_answer
        logging.info(f"Extracted relations: {self.state_relations.relations}")

        return self.state_relations
  
    def plot_entities_schema(self, file_path: str) -> None:
        """
        Plots the entities schema from a PDF file.

        Args:
            file_path (str): The path to the PDF file.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"PDF file not found: {file_path}")
        
        entities = []
        base64_images = self._process_pdf(file_path)

        if base64_images:
            page_answers = self._generate_digraph(base64_images)
            digraph_code = self._merge_digraphs_for_plot(page_answers)

            logging.info("\nDigraph code for all pages:")
            logging.info(digraph_code[9:-3])
            logging.info("digraph_code_execution----------------------------------")
            exec(digraph_code[9:-3])


    def _generate_json_schemas(self,*_):
        page_answers = []
        for page_num, base64_image in enumerate(self.state_entities.base64_images, start=1):
            if self.state_entities.user_prompt_for_filter:
                customized_prompt = f"{JSON_SCHEMA_PROMPT} extract only what is required from the following prompt:\
                      {self.state_entities.user_prompt_for_filter} (Page {page_num})"
            else:
                customized_prompt = f"{JSON_SCHEMA_PROMPT} (Page {page_num})"
            
            image_data = f"data:image/jpeg;base64,{base64_image}"
            try:
                answer = self.llm_client.get_response(customized_prompt, image_url=image_data)
            except ReadTimeout:
                logging.warning("Request to OpenAI API timed out. Retrying...")
                continue
            answer = self._extract_json_content(answer)
            page_answers.append(f"Page {page_num}: {answer}")
            logging.info(f"Processed page {page_num}")

        self.state_entities.page_answers = page_answers
        return self.state_entities

    def _merge_json_schemas(self,*_):
        json_schema_prompt = "Generate a unique json schema starting from the following \
                          \n\n" + "\n\n".join(self.state_entities.page_answers) + "\n\n \
                          Remember to provide only the json schema without any comments, wrapped in backticks (`) like ```json ... ``` and nothing else."

        json_schema_answer = self.llm_client.get_response(json_schema_prompt)
        json_schema = self._extract_json_content(json_schema_answer)
        logging.info("\n PDF JSON Schema:")
        logging.info(json_schema)
        # json schema is a valid json schema but its a string convert it to a python dict
        entities_json_schema = json.loads(json_schema) 

        self.state_entities.entities_json_schema = entities_json_schema
        self._json_schema = entities_json_schema
        return self.state_entities
    
    def _process_pdf(self, *_):  #Optional[List[str]]:
        """
        Processes a PDF file and converts each page to a base64 encoded image.

        Args:
            pdf_path (str): The path to the PDF file.

        Returns:
            List[str] or None: A list of base64 encoded images if successful, None otherwise.
        """
        if (self.state_entities.file_path is None and 
            self.state_entities_json_schema.file_path is None):
            raise FileNotFoundError(f"PDF file not found")
        elif self.state_entities.file_path is None:
            # check if the file exists
            if not os.path.exists(self.state_entities_json_schema.file_path):
                raise FileNotFoundError(f"PDF file not found: {self.state_entities_json_schema.file_path}")
            file_path = self.state_entities_json_schema.file_path
        elif self.state_entities_json_schema.file_path is None:
            # check if the file exists
            if not os.path.exists(self.state_entities.file_path):
                raise FileNotFoundError(f"PDF file not found: {self.state_entities.file_path}")
            file_path = self.state_entities.file_path
        
        # Load PDF as images
        images = load_pdf_as_images(file_path)
        if not images:
            return None

        base64_images = []

        for page_num, image in enumerate(images, start=1):
            temp_image_path = None
            try:
                # Save image to temporary file
                temp_image_path = save_image_to_temp(image)
                
                # Convert image to base64
                base64_image = encode_image(temp_image_path)
                base64_images.append(base64_image)

            except Exception as e:
                logging.error(f"Error processing page {page_num}: {e}")
            finally:
                # Ensure temp file is deleted even in case of an error
                if temp_image_path and os.path.exists(temp_image_path):
                    os.unlink(temp_image_path)

        self.state_entities.base64_images = base64_images
        return self.state_entities
    
    def get_entities_graph(self):
        return self.graph_for_entities
    
    def get_relations_graph(self):
        return self.graph_for_relations
    
    def generate_json_schema(self, file_path: str) -> Dict[str, Any]:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"PDF file not found: {file_path}")
        
        self.state_entities_json_schema.file_path = file_path  
        self.graph_for_entities_json_schema.invoke(self.state_entities_json_schema)

        logging.info(f"Entities JSON Schema: {self._json_schema}")
        return self._json_schema

    def get_json_schema_graph(self):
        return self.graph_for_entities_json_schema

    def get_json_schema(self):
        return self._json_schema
    
    def get_entities(self):
        return self._entities
    
    def get_relations(self):
        return self._relations
    


