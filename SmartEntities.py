import requests
from pdf_processor import process_pdf
from config import HEADERS, DIGRAPH_EXAMPLE

def generate_digraph(base64_images):
    page_answers = []
    for page_num, base64_image in enumerate(base64_images, start=1):
        payload = {
            "model": "gpt-4o",
            "messages": [
                {
                    "role": "system",
                    "content": "You are an AI specialized in extracting structured information from documents. Your task is to analyze the provided image and generate a Graphviz digraph that represents the entities and their relationships found within. Focus on identifying key concepts, hierarchical structures, and relevant data points regardless of the document type. The digraph should be clear, well-organized, and follow the structure of the example provided. Ensure that all entities are properly connected, labeled, and reflect the content and relationships present in the document."
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": f"Generate a digraph like the following for the meaningful entities in this image, following this example: {DIGRAPH_EXAMPLE} (Page {page_num})"},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ]
                }
            ],
        }

        response = requests.post("https://api.openai.com/v1/chat/completions", headers=HEADERS, json=payload)
        answer = response.json()['choices'][0]['message']['content']
        page_answers.append(f"Page {page_num}: {answer}")
        print(f"Processed page {page_num}")

    return page_answers

def merge_digraphs(page_answers):
    digraph_prompt = "Merge the partial digraphs that I provide to you merging together all the detected entities, \n\n" + "\n\n".join(page_answers) + \
        "\nYour answer digraph must be a tree and must contain only the code for a valid graphviz graph"
    digraph_payload = {
        "model": "gpt-4o",
        "messages": [
            {"role": "system", "content": "You are an AI that generates only valid digraph code without any comments before or after the generated code. At the end, it always shows the generated viz with dot.render('ontology_graph', format='png'). You have to provide a graph that takes as reference the following graph: {DIGRAPH_EXAMPLE}"},
            {"role": "user", "content": digraph_prompt}
        ],
    }

    digraph_response = requests.post("https://api.openai.com/v1/chat/completions", headers=HEADERS, json=digraph_payload)
    digraph_code = digraph_response.json()['choices'][0]['message']['content']
    return digraph_code

def main():
    pdf_path = './test.pdf'
    base64_images = process_pdf(pdf_path)

    if base64_images:
        page_answers = generate_digraph(base64_images)
        digraph_code = merge_digraphs(page_answers)

        print("\nDigraph code for all pages:")
        print(digraph_code[9:-3])
        print("digraph_code_execution----------------------------------")
        exec(digraph_code[9:-3])

if __name__ == "__main__":
    main()





