from typing import List
from .base_parser import BaseParser
from ..entities import Entity, Relation
import base64
import os
import tempfile
from pdf2image import convert_from_path
from pdf2image.exceptions import PDFInfoNotInstalledError, PDFPageCountError, PDFSyntaxError
import requests
import json
from .prompts import DIGRAPH_EXAMPLE_PROMPT, JSON_SCHEMA_PROMPT

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def load_pdf_as_images(pdf_path):
    try:
        images = convert_from_path(pdf_path)
        return images
    except (PDFInfoNotInstalledError, PDFPageCountError, PDFSyntaxError) as e:
        print(f"Error converting PDF: {e}")
        return None

def save_image_to_temp(image):
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
        image.save(temp_file.name, 'JPEG')
        return temp_file.name

def process_pdf(pdf_path):
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
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

    def extract_entities(self, file_path: str) -> dict:
        entities = []
        base64_images = process_pdf(file_path)

        if base64_images:
            page_answers = self._generate_json_schema(base64_images)
            json_schema = self._merge_json_schemas(page_answers)
            json_schema = json_schema[8:-3]

            print("\n PDF JSON Schema:")
            print(json_schema)
            # json schema is a valid json schema but its a string convert it to a python dict
            json_schema = json.loads(json_schema)
            return json_schema

    def extract_relations(self, file_path: str) -> List[Relation]:
        relations = []
        # Implement relation extraction logic here
        # This is a placeholder for the actual implementation
        return relations
    


    def plot_entities_schema(self, file_path: str):
        entities = []
        base64_images = process_pdf(file_path)

        if base64_images:
            page_answers = self._generate_digraph(base64_images)
            digraph_code = self._merge_digraphs_for_plot

            print("\nDigraph code for all pages:")
            print(digraph_code[9:-3])
            print("digraph_code_execution----------------------------------")
            exec(digraph_code[9:-3])

    def _generate_digraph(self, base64_images):
        page_answers = []
        for page_num, base64_image in enumerate(base64_images, start=1):
            payload = {
                "model": "gpt-4o",
                "temperature": 0,
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

            response = requests.post("https://api.openai.com/v1/chat/completions", headers=self.headers, json=payload)
            answer = response.json()['choices'][0]['message']['content']
            page_answers.append(f"Page {page_num}: {answer}")
            print(f"Processed page {page_num}")

        return page_answers

    def _merge_digraphs_for_plot(self, page_answers):
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
    

    def _generate_json_schema(self, base64_images):
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

            response = requests.post("https://api.openai.com/v1/chat/completions", headers=self.headers, json=payload)
            answer = response.json()['choices'][0]['message']['content']
            page_answers.append(f"Page {page_num}: {answer}")
            print(f"Processed page {page_num}")

        return page_answers

    def _merge_json_schemas(self, page_answers):
        digraph_prompt = "Generate a unique json schema starting from the following \
                          \n\n" + "\n\n".join(page_answers) + "\n\n \
                          Remember to provide only the json schema, without any comments before or after the json schema"

        
        digraph_payload = {
            "model": "gpt-4o",
            "temperature": 0,
            "messages": [
                {"role": "user", "content": digraph_prompt}
            ],
        }

        digraph_response = requests.post("https://api.openai.com/v1/chat/completions", headers=self.headers, json=digraph_payload)
        digraph_code = digraph_response.json()['choices'][0]['message']['content']
        return digraph_code

