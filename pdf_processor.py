import base64
import os
import tempfile
from pdf2image import convert_from_path
from pdf2image.exceptions import PDFInfoNotInstalledError, PDFPageCountError, PDFSyntaxError

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