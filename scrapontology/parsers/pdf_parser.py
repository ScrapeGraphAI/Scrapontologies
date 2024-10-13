from typing import List, Dict, Any, Optional, Literal, Union
from .base_parser import BaseParser
from ..primitives import Entity, Relation, Record
import base64
import os
import tempfile
import json
from .prompts import JSON_SCHEMA_PROMPT, RELATIONS_PROMPT, UPDATE_ENTITIES_PROMPT, EXTRACT_ENTITIES_CODE_PROMPT, FIX_CODE_PROMPT, EXTRACT_DATA_PROMPT
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
from collections import defaultdict


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

        class StateEntitiesSchema(BaseModel):
            file_path: Optional[str] = None
            user_prompt_for_filter: Optional[str] = None
            entities_schema_code: Optional[str] = None
            entity_class: Optional[str] = None 
            temp_entities: Optional[List[Entity]] = None
            entities: Optional[List[Entity]] = None
            base64_images: Optional[List[str]] = None
            page_answers: Optional[List[str]] = None
            entities_json_schema: Optional[Dict[str, Any]] = None
            entities_schema: Optional[List[Entity]] = None


        # initialize the state with the avaible field at the start, the entity class definition
        self.state_entities_schema =  StateEntitiesSchema()
        self.state_entities_schema.entity_class = inspect.getsource(Entity)

        #nodes for the entities graph
        builder_for_entities_schema = StateGraph(StateEntitiesSchema)
        builder_for_entities_schema.add_node("process_pdf", self._process_pdf)
        builder_for_entities_schema.add_node("generate_json_schemas", self._generate_json_schemas)
        builder_for_entities_schema.add_node("merge_json_schemas", self._merge_json_schemas)
        builder_for_entities_schema.add_node("generate_entities_schema_code", self._generate_entities_schema_code)
        builder_for_entities_schema.add_node("execute_entities_schema_code", self._execute_entities_schema_code)
        builder_for_entities_schema.add_node("assign_entities_schema", self.update_entities)

        #edges for the entities graph
        builder_for_entities_schema.add_edge(START, "process_pdf")
        builder_for_entities_schema.add_edge("process_pdf", "generate_json_schemas")
        builder_for_entities_schema.add_edge("generate_json_schemas", "merge_json_schemas")
        builder_for_entities_schema.add_edge("merge_json_schemas", "generate_entities_schema_code")
        builder_for_entities_schema.add_edge("generate_entities_schema_code","execute_entities_schema_code")
        builder_for_entities_schema.add_edge("execute_entities_schema_code", "assign_entities_schema")
        builder_for_entities_schema.add_edge("assign_entities_schema", END)

        self.graph_for_entities_schema = builder_for_entities_schema.compile()


        class StateRelations(BaseModel):
            entities: Optional[List[Entity]] = None
            user_prompt_for_filter: Optional[str] = None
            relations_code: Optional[str] = None
            relation_class: Optional[str] = None
            relations: Optional[List[Relation]] = None

        self.state_relations = StateRelations()
        self.state_relations.relation_class = inspect.getsource(Relation)

        builder_for_relations = StateGraph(StateRelations)
        builder_for_relations.add_node("extract_relations_schema", self._extract_relations_schema_code)
        builder_for_relations.add_node("execute_relations_code", self._execute_relations_code)
        builder_for_relations.add_edge(START, "extract_relations_schema")
        builder_for_relations.add_edge("extract_relations_schema", "execute_relations_code")
        builder_for_relations.add_edge("execute_relations_code", END)

        self.graph_for_relations = builder_for_relations.compile()

        class StateEntitiesJsonSchema(BaseModel):
            file_path: Optional[str] = None
            base64_images: Optional[List[str]] = None
            page_answers: Optional[List[str]] = None
            entities_json_schema: Optional[Dict[str, Any]] = None

        self.state_entities_json_schema = StateEntitiesJsonSchema()
    

        builder_for_entities_json_schema = StateGraph(StateEntitiesJsonSchema)
        builder_for_entities_json_schema.add_node("process_pdf", self._process_pdf)
        builder_for_entities_json_schema.add_node("generate_json_schemas", self._generate_json_schemas)
        builder_for_entities_json_schema.add_node("merge_json_schemas", self._merge_json_schemas)
        builder_for_entities_json_schema.add_edge(START, "process_pdf")
        builder_for_entities_json_schema.add_edge("process_pdf", "generate_json_schemas")
        builder_for_entities_json_schema.add_edge("generate_json_schemas", "merge_json_schemas")
        builder_for_entities_json_schema.add_edge("merge_json_schemas", END)

        self.graph_for_entities_schema_json_schema = builder_for_entities_json_schema.compile()

        # State class for extracting entities from files
        class StateExtractEntities(BaseModel):
            file_path: Optional[str] = None
            entities_json_schema: Optional[Dict[str, Any]] = None
            base64_images: Optional[List[str]] = None
            page_answers: Optional[List[str]] = None
            temp_entities: Optional[List[Entity]] = None
            entities: Optional[List[Entity]] = None
            user_prompt_for_filter: Optional[str] = None

        self.state_extract_entities = StateExtractEntities()

        # Build the state graph for extracting entities from files
        builder_for_extract_entities = StateGraph(StateExtractEntities)
        builder_for_extract_entities.add_node("process_pdf", self._process_pdf_for_extraction)
        builder_for_extract_entities.add_node("extract_data_from_pages", self._extract_data_from_pages)
        builder_for_extract_entities.add_node("merge_extracted_data", self._merge_extracted_data)

        # Define edges for the state graph
        builder_for_extract_entities.add_edge(START, "process_pdf")
        builder_for_extract_entities.add_edge("process_pdf", "extract_data_from_pages")
        builder_for_extract_entities.add_edge("extract_data_from_pages", "merge_extracted_data")
        builder_for_extract_entities.add_edge("merge_extracted_data", END)

        self.graph_for_extract_entities = builder_for_extract_entities.compile()

    
    def _generate_entities_schema_code(self, *_) -> str:
        prompt = EXTRACT_ENTITIES_CODE_PROMPT.format(json_schema=str(self.state_entities_schema.entities_json_schema) , entity_class=str(inspect.getsource(Entity)))
        entities_schema_code = self.llm_client.get_response(prompt)

        # extract the python code from the entities_schema_code remove the ```python and ```
        entities_schema_code = entities_schema_code.replace("```python", "").replace("```", "")
        self.state_entities_schema.entities_schema_code = entities_schema_code
        return self.state_entities_schema
    
    def _execute_entities_schema_code(self, *_):
        local_vars = {}
        max_retries = 3
        retry_count = 0
        while retry_count < max_retries:
            try:
                exec(self.state_entities_schema.entities_schema_code, globals(), local_vars)
                break  # If successful, exit the loop
            except Exception as e:
                logging.error(f"Error executing entities code (attempt {retry_count + 1}): {e}")
                if retry_count == max_retries - 1:
                    logging.error("Max retries reached. Unable to execute entities code.")
                    break
                fix_code_prompt = FIX_CODE_PROMPT.format(code=self.state_entities_schema.entities_schema_code, error=str(e))
                fixed_code = self.llm_client.get_response(fix_code_prompt)
                fixed_code = fixed_code.replace("```python", "").replace("```", "")
                self.state_entities_schema.entities_schema_code = fixed_code  # Update entities_schema_code with the fixed version
                retry_count += 1
        
        new_entities = local_vars.get('entities', [])
        self.state_entities_schema.temp_entities = new_entities
        
        return self.state_entities_schema

    
    def extract_entities_schema(self, file_path: str, prompt: Optional[str] = None) -> List[Entity]:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"PDF file not found: {file_path}")
        
        self.state_entities_schema.file_path = file_path

        if prompt:
            self.state_entities_schema.user_prompt_for_filter = prompt


        self.graph_for_entities_schema.invoke(self.state_entities_schema)

        return self.state_entities_schema.entities_schema

    

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
        existing_entities = self._entities_schema

        prompt = UPDATE_ENTITIES_PROMPT.format(
            existing_entities=json.dumps([e.__dict__ for e in existing_entities], indent=2),
            new_entities=json.dumps([e.__dict__ for e in self.state_entities_schema.temp_entities], indent=2)
        )

        response = self.llm_client.get_response(prompt)
        response = response.strip().strip('```json').strip('```')

        try:
            updated_entities_data = json.loads(response)
            updated_entities = [Entity(**entity_data) for entity_data in updated_entities_data]
            
            # Update the parser's entities
            self.state_entities_schema.entities_schema = updated_entities
            self._entities_schema = updated_entities
            
            # print the updated entities
            logging.info("Updated entities:")
            for entity in updated_entities:
                logging.info(entity.__dict__)
            logging.info(f"Entities updated. New count: {len(updated_entities)}")
            return self.state_entities_schema
        except json.JSONDecodeError as e:
            logging.error(f"JSONDecodeError: {e}")
            logging.error("Error: Unable to parse the LLM response.")
            return self.state_entities_schema

    def extract_relations_schema(self, file_path: Optional[str] = None, prompt: Optional[str] = None) -> List[Relation]:
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
        
        if not self._entities_schema or len(self._entities_schema) == 0:
            logging.error("Entities not found. Please extract entities first.")
            raise ValueError("Entities not found. Please extract entities first.")

        self.graph_for_relations.invoke(self.state_relations)

        return self.state_relations.relations


    def _extract_relations_schema_code(self, *_):
        relation_class_str = inspect.getsource(Relation)
        relations_prompt = RELATIONS_PROMPT.format(
            entities=json.dumps([e.__dict__ for e in self._entities_schema], indent=2),
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
        self._relations_schema = relations_answer
        self.state_relations.relations = relations_answer
        logging.info(f"Extracted relations: {self.state_relations.relations}")

        return self.state_relations
  

    def _generate_json_schemas(self,*_):
        page_answers = []
        for page_num, base64_image in enumerate(self.state_entities_schema.base64_images, start=1):
            if self.state_entities_schema.user_prompt_for_filter:
                customized_prompt = f"{JSON_SCHEMA_PROMPT} extract only what is required from the following prompt:\
                      {self.state_entities_schema.user_prompt_for_filter} (Page {page_num})"
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

        self.state_entities_schema.page_answers = page_answers
        return self.state_entities_schema

    def _merge_json_schemas(self,*_):
        json_schema_prompt = "Generate a unique json schema starting from the following \
                          \n\n" + "\n\n".join(self.state_entities_schema.page_answers) + "\n\n \
                          Remember to provide only the json schema without any comments, wrapped in backticks (`) like ```json ... ``` and nothing else."

        json_schema_answer = self.llm_client.get_response(json_schema_prompt)
        json_schema = self._extract_json_content(json_schema_answer)
        logging.info("\n PDF JSON Schema:")
        logging.info(json_schema)
        # json schema is a valid json schema but its a string convert it to a python dict
        entities_json_schema = json.loads(json_schema) 

        self.state_entities_schema.entities_json_schema = entities_json_schema
        self._json_schema = entities_json_schema
        return self.state_entities_schema
    
    def _process_pdf(self, *_):  #Optional[List[str]]:
        """
        Processes a PDF file and converts each page to a base64 encoded image.

        Args:
            pdf_path (str): The path to the PDF file.

        Returns:
            List[str] or None: A list of base64 encoded images if successful, None otherwise.
        """
        if (self.state_entities_schema.file_path is None and 
            self.state_entities_json_schema.file_path is None):
            raise FileNotFoundError(f"PDF file not found")
        elif self.state_entities_schema.file_path is None:
            # check if the file exists
            if not os.path.exists(self.state_entities_json_schema.file_path):
                raise FileNotFoundError(f"PDF file not found: {self.state_entities_json_schema.file_path}")
            file_path = self.state_entities_json_schema.file_path
        elif self.state_entities_json_schema.file_path is None:
            # check if the file exists
            if not os.path.exists(self.state_entities_schema.file_path):
                raise FileNotFoundError(f"PDF file not found: {self.state_entities_schema.file_path}")
            file_path = self.state_entities_schema.file_path
        
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

        self.state_entities_schema.base64_images = base64_images
        return self.state_entities_schema
    
    def get_entities_schema_graph(self) -> StateGraph:
        """
        Get the graph for entities schema.

        Returns:
            StateGraph: The graph object for entities schema.
        """
        return self.graph_for_entities_schema
    
    def get_relations_schema_graph(self) -> StateGraph:
        """
        Get the graph for relations schema.

        Returns:
            StateGraph: The graph object for relations schema.
        """
        return self.graph_for_relations
    
    def generate_json_schema(self, file_path: str) -> Dict[str, Any]:
        """
        Generate JSON schema from the given PDF file.

        Args:
            file_path (str): Path to the PDF file.

        Returns:
            Dict[str, Any]: The generated JSON schema.

        Raises:
            FileNotFoundError: If the specified PDF file is not found.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"PDF file not found: {file_path}")
        
        self.state_entities_json_schema.file_path = file_path  
        self.graph_for_entities_schema_json_schema.invoke(self.state_entities_json_schema)

        logging.info(f"Entities JSON Schema: {self._json_schema}")
        return self._json_schema

    def get_json_schema_graph(self) -> StateGraph:
        """
        Get the graph for JSON schema generation.

        Returns:
            StateGraph: The graph object for JSON schema generation.
        """
        return self.graph_for_entities_schema_json_schema

    def get_json_schema(self) -> Dict[str, Any]:
        """
        Get the generated JSON schema.

        Returns:
            Dict[str, Any]: The generated JSON schema.
        """
        return self._json_schema
    
    def get_entities_schema(self) -> Dict[str, Any]:
        """
        Get the entities schema.

        Returns:
            Dict[str, Any]: The entities schema.
        """
        return self._entities_schema
    
    def get_relations_schema(self) -> Dict[str, Any]:
        """
        Get the relations schema.

        Returns:
            Dict[str, Any]: The relations schema.
        """
        return self._relations_schema

    
    
    def extract_entities_from_file(self, file_path: Union[str, List[str]], prompt: Optional[str] = None) -> List[Record]:
        """
        Extract entities from the given file(s) using the entities_json_schema.

        Args:
            file_path (Union[str, List[str]]): Path to the PDF file or list of PDF files.
            prompt (Optional[str]): Additional prompt for filtering or guiding the extraction.

        Returns:
            List[Entity]: A list of extracted entities with data.
        """
        # Check if JSON schema is available
        if not self._json_schema:
            raise ValueError("JSON schema is not generated. Please generate JSON schema first.")

        # Convert file_path to list if it's a string
        if isinstance(file_path, str):
            file_path = [file_path]

        self.state_extract_entities.entities_json_schema = self._json_schema
        self.state_extract_entities.user_prompt_for_filter = prompt

        records = []

        for path in file_path:
            if not os.path.exists(path):
                logging.error(f"PDF file not found: {path}")
                continue  # Skip this file and proceed to the next one

            self.state_extract_entities.file_path = path
            self.state_extract_entities.base64_images = None
            self.state_extract_entities.page_answers = None
            self.state_extract_entities.temp_entities = None
            self.state_extract_entities.entities = None

            # Invoke the state graph
            self.graph_for_extract_entities.invoke(self.state_extract_entities)

            if self.state_extract_entities.entities:
                record = Record(id=path, entities=self.state_extract_entities.entities) 
                records.append(record)

        return records

    # Additional methods will be implemented below

    def _process_pdf_for_extraction(self, *_):
        """
        Process a PDF file for entity extraction.

        This method loads the PDF file as images, converts each page to base64 format,
        and stores the results in the state_extract_entities object.

        Args:
            *_: Unused arguments.

        Returns:
            The updated state_extract_entities object or None if no images were loaded.

        Raises:
            FileNotFoundError: If the PDF file path is not provided.
        """
        if not self.state_extract_entities.file_path:
            raise FileNotFoundError("PDF file path is not provided.")

        file_path = self.state_extract_entities.file_path

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

        self.state_extract_entities.base64_images = base64_images
        return self.state_extract_entities
    
    
    def _extract_data_from_pages(self, *_):
        """
        Extract data from images using the entities_json_schema.
        """
        page_answers = []
        for page_num, base64_image in enumerate(self.state_extract_entities.base64_images, start=1):
            # Prepare the prompt
            json_schema_str = json.dumps(self.state_extract_entities.entities_json_schema, indent=2)
            prompt = EXTRACT_DATA_PROMPT.format(json_schema=json_schema_str)

            if self.state_extract_entities.user_prompt_for_filter:
                prompt += f"\n\nAdditional instructions: {self.state_extract_entities.user_prompt_for_filter}"

            image_data = f"data:image/jpeg;base64,{base64_image}"

            try:
                answer = self.llm_client.get_response(prompt, image_url=image_data)
                answer = self._extract_json_content(answer)
                page_answers.append(answer)
                logging.info(f"Extracted data from page {page_num}")
            except Exception as e:
                logging.error(f"Error extracting data from page {page_num}: {e}")

        self.state_extract_entities.page_answers = page_answers
        return self.state_extract_entities
    
    def _merge_extracted_data(self, *_):
        """
        Merge the extracted data from all pages into entities.
        """
        all_entities_data = []
        for page_answer in self.state_extract_entities.page_answers:
            try:
                entities_data = json.loads(page_answer)
                all_entities_data.append(entities_data)
            except json.JSONDecodeError as e:
                logging.error(f"JSONDecodeError: {e}")
                raise ValueError(f"Error merging extracted data: {e}") from e

        # Merge all entities data
        merged_entities_data = self._combine_entities_data(all_entities_data)

        entities = []
        # Create Entity instances
        for entity_id, attributes in merged_entities_data.items():
            entity = Entity(id=entity_id, type='object', attributes=attributes)
            entities.append(entity)

        self.state_extract_entities.entities = entities
        return self.state_extract_entities

    def _combine_entities_data(self, all_entities_data):
        """
        Combines entity data from multiple sources into a single dictionary.

        Args:
            all_entities_data (list): A list of dictionaries, each containing entity data.

        Returns:
            dict: A combined dictionary of entity data, with non-NA values preferred.
        """
        combined_data = {}
        for entities_data in all_entities_data:
            combined_data = self.merge_dicts_preferring_non_na(combined_data, entities_data)
        return combined_data

    def merge_dicts_preferring_non_na(self, d1, d2):
        """
        Merges two dictionaries, preferring non-NA values from d2 over d1.

        Args:
            d1 (dict): The first dictionary to merge.
            d2 (dict): The second dictionary to merge, whose non-NA values take precedence.

        Returns:
            dict: A merged dictionary with non-NA values preferred.

        Notes:
            - NA values are considered to be None, 'NA', or empty string.
            - For nested dictionaries, the merge is performed recursively.
            - For lists, values from d2 are appended to d1, excluding NA values.
            - For other types, existing non-NA values in d1 are not overwritten.
        """
        for key, value in d2.items():
            if value in (None, 'NA', ''):
                continue
            if key not in d1 or d1[key] in (None, 'NA', ''):
                d1[key] = value
            else:
                if isinstance(d1[key], dict) and isinstance(value, dict):
                    d1[key] = self.merge_dicts_preferring_non_na(d1[key], value)
                elif isinstance(d1[key], list) and isinstance(value, list):
                    # Extend the list, excluding 'NA' values
                    d1[key].extend([v for v in value if v not in (None, 'NA', '')])
                else:
                    # Do not overwrite existing non-'NA' values
                    pass
        return d1