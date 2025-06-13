#Course content with content for TDS Jan 2025 as on 15 Apr 2025 (Cloned using GITHUB ACCOUNT)

import re
from dotenv import load_dotenv
import os
from google import genai
from pathlib import Path
import requests
from io import BytesIO
import mimetypes
from google.genai import types

def extract_image_links(markdown_text):
    return re.findall(r'!\[(.*?)\]\((.*?)\)', markdown_text)


load_dotenv()
genai_api_key = os.getenv("GENAI_API_KEY")


image_processing_errors = 0

def get_image_description(image_path):
    global image_processing_errors
    try:
        image_bytes = requests.get(image_path).content
        image = types.Part.from_bytes(
        data=image_bytes, mime_type="image/jpeg"
        )

        client = genai.Client(api_key=genai_api_key)
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=["Describe the study-related content in this image, including headings, formulas, and the main topic if identifiable.", image],
        )
        return response.text
    except Exception as e:
        image_processing_errors += 1
        print(f"⚠️ Error describing image: {image_url}\n{e}")
        return f"⚠️ Failed to process image: {e}"

    


source_dir = Path("tools-in-data-science-public")  # Folder containing original markdown files
target_dir = Path("markdown")                      # Folder to save modified markdown files
target_dir.mkdir(exist_ok=True)                    # Create the folder if it doesn't exist




for md_file in source_dir.rglob("*.md"):
    print(f"Processing {md_file}...")

    # Read the content of the .md file
    with open(md_file, 'r', encoding='utf-8') as file:
        content = file.read()

    # Extract all image references
    images = extract_image_links(content)

    # For each image, describe it and append below the image
    for alt_text, image_url in images:
        description = get_image_description(image_url)
        markdown_image = f"![{alt_text}]({image_url})"
        image_description = f"{markdown_image}\n\n> 📘 **Image Description:** {description.strip()}\n"
        content = content.replace(markdown_image, image_description)


    # Write the modified content to a new file in the markdown/ directory
    target_file = target_dir / md_file.name
    with open(target_file, 'w', encoding='utf-8') as out_file:
        out_file.write(content)

    print(f"Saved modified file: {target_file}\n")

print("All markdown files of the TDS course content processed successfully!")
print(f"Total image processing errors: {image_processing_errors}")




