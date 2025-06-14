import requests
from bs4 import BeautifulSoup
import json
from dotenv import load_dotenv
import os
from google import genai
from google.genai import types
import time

# Load API key from .env file
load_dotenv()
genai_api_key = os.getenv("GENAI_API_KEY")

# Initialize Gemini client
client = genai.Client(api_key=genai_api_key)

# Global counter for image errors
image_processing_errors = 0

# # Describe image using Gemini
# def get_image_description(image_url):
#     global image_processing_errors
#     try:
#         image_bytes = requests.get(image_url).content
#         image = types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg")
#         time.sleep(5)
#         response = client.models.generate_content(
#             model="gemini-2.0-flash",
#             contents=[
#                 "Describe the study-related content in this image, including headings, formulas, and the main topic if identifiable.",
#                 image,
#             ],
#         )
#         return response.text.strip()
#     except Exception as e:
#         image_processing_errors += 1
#         print(f"⚠️ Error describing image: {image_url}\n{e}")
#         return f"⚠️ Failed to process image: {e}"
    

def get_image_description(image_url):
    global image_processing_errors
    max_retries = 3
    for attempt in range(max_retries):
        try:
            image_bytes = requests.get(image_url).content
            image = types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg")

            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[
                    "Describe the study-related content in this image, including headings, formulas, and the main topic if identifiable.",
                    image,
                ],
            )
            return response.text.strip()

        except Exception as e:
            if "RESOURCE_EXHAUSTED" in str(e) or "429" in str(e):
                wait_time = 60  # or parse 'retryDelay' if needed
                print(f"⚠️ Quota exhausted. Waiting {wait_time}s before retrying...")
                time.sleep(wait_time)
            else:
                image_processing_errors += 1
                print(f"⚠️ Error describing image: {image_url}\n{e}")
                return f"⚠️ Failed to process image: {e}"

    image_processing_errors += 1
    return f"⚠️ Failed after {max_retries} retries due to quota limits."

# Load list of posts
with open("tds_posts_jan_to_apr_2025.json", "r", encoding="utf-8") as file:
    posts = json.load(file)

# Create markdown folder if it doesn't exist
os.makedirs("markdown", exist_ok=True)

# Extract content and save as markdown
def extract_markdown_for_post(post_url):
    HEADERS = {
        "cookie": "_fbp=fb.2.1685009617749.827372375; _ga_MXPR4XHYG9=GS1.1.1727465592.1.1.1727465621.0.0.0; _ga_WMF1LS64VT=GS1.1.1727465574.2.1.1727465635.0.0.0; _ga_K38CF65X4M=GS1.1.1739974908.1.0.1739974916.0.0.0; _gcl_au=1.1.713156231.1745229867; _gcl_gs=2.1.k1$i1748155813$u129582030; _gcl_aw=GCL.1748155816.CjwKCAjw3MXBBhAzEiwA0vLXQXCHOMchU5lOVP3nP-F4471Qtge6l3J_kUMy242aCkL6Q60sgYG6XBoCF1oQAvD_BwE; _ga_5HTJMW67XK=GS2.1.s1748695194$o238$g0$t1748695241$j13$l0$h0; _ga_QHXRKWW9HH=GS2.3.s1749753644$o42$g0$t1749753644$j60$l0$h0; _ga=GA1.1.19740650.1685009618; _ga_08NPRH5L4M=GS2.1.s1749753675$o572$g1$t1749755572$j51$l0$h0; _bypass_cache=true; _t=B6r32xfs5EETXWtDBg%2BH0yiSESxjzuEY5VJJdTdjXGWJ5UKDrow%2BdqyVgyrfk0F7S5K0EObijMH7R7phGgGVvzsWMFAwfVmhJKunv%2FVGrERFYGNLSazcHybVcKlKgYjwA%2FLbVUHGwANoRXKD9DEj1jqVMECoSQe4HFxb8Mij2leqeUbOuayUJ6gbzui6d5%2BBGSoVrKh2yfSq3LnnBRObRjg6XHhJIzmN5Po2MOd6KqvsDIBMHnpOvM30VeBjxtKXXlRAN2ZI%2FenY2V0QrSh2YlB%2FkyCkLgOhnHVyiqxMFe2qaaNB1pI6jwo7sGdbmYdcAqG%2FQO%2F%2Fa98%3D--WvSfOzwR0U3xrRCP--4t88pJsJq73aoSPV3HdBTQ%3D%3D; _forum_session=EG3l3%2BAso6tgRf1Ze2fYyArm6C44S76CnQ0qWvxfV%2BWQ6ccdTovll53vFI0LrA%2Fu3Z56fBLBShTAh%2BTa6lL4EhPeD7rBpc9Kem4lpcBKUxq8ZmqOWox%2F13csk8hUGYS90BmlZ5KsXSVZeVjmySqC%2Ba%2FH3TE9lC7GJs3YtEi4iTvjeFWH9FwseOxUc2bhskppls4Fw%2FT9wfWiSVG%2Fm%2FF0gec%2FniFBZ8cPikmAgOo9cx0yaLc3UoHs3r9jb2NmcV7K%2BZYqywSBHWIkq1tOhT6RqEhzqfAwQzzu5h6%2B1Kh5TcRS%2FNnowIPoANaIYJzTIeFN%2BW01BGaiS7DWwq2sPwLklHHJlVLJZQPg%2FvsCr2IO7AC%2Bk99T3HnDMVtJQ0%2BgUg%3D%3D--HUpsOvDQ0rNfJE9g--sZazMcvutt85hR44MJlvfA%3D%3D"
    }
    json_url = post_url + ".json"
    try:
        response = requests.get(json_url, headers=HEADERS)
        response.raise_for_status()
        data = response.json()

        markdown_chunks = []

        for p in data.get("post_stream", {}).get("posts", []):
            soup = BeautifulSoup(p.get("cooked", ""), "html.parser")
            text = soup.get_text(separator="\n").strip()

            md = f"### Post by **{p.get('username')}** (Post #{p.get('post_number')})\n\n{text}\n"

            images = [img['src'] for img in soup.find_all("img") if img.get("src")]
            for image_url in images:
                description = get_image_description(image_url)
                md += f"\n![Image]({image_url})\n\n_Description: {description}_\n"

            markdown_chunks.append(md)

        return "\n---\n".join(markdown_chunks)

    except Exception as e:
        return f"❌ Error fetching post content from {json_url}: {e}"

# Process and save each post
for post in posts:
    print(f"Processing: {post['title']}")
    markdown_content = extract_markdown_for_post(post["url"])
    file_path = os.path.join("markdown", f"{post['id']}.md")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(f"# {post['title']}\n\nURL: {post['url']}\n\n{markdown_content}")

print(f"\n✅ All markdown files saved in the 'markdown/' folder.")
print(f"⚠️ Total image description errors: {image_processing_errors}")
