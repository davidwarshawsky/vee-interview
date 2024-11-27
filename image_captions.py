from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
import base64, os, httpx, json
import asyncio, aiohttp
from concurrent.futures import ThreadPoolExecutor
from typing import List
load_dotenv()

def get_image_links(website_map,base_url):
    image_links = {
        key: [link for link in values['links'] if '.jpg' in link or '.png' in link and link.startswith(base_url)]
        for
        key, values in website_map.items()
    }
    image_links = {key: values for key, values in image_links.items() if values}
    image_links = [item for sublist in image_links.values() for item in sublist]
    return image_links


async def download_image(session, url, output_dir):
    name = url.split('/')[-1]
    output_dir = os.path.join(output_dir, "images")
    filename = os.path.join(output_dir,name)
    if not os.path.exists(filename):
        async with session.get(url) as response:
            content = await response.read()
            with open(filename, "wb") as f:
                f.write(content)


async def download_images_async(urls,output_dir=None):
    if not output_dir:
        output_dir = "images"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
    else:
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
    async with aiohttp.ClientSession() as session:
        tasks = [download_image(session, url, output_dir) for url in urls]
        await asyncio.gather(*tasks)


def download_images(urls: List[str], output_dir):
    asyncio.run(download_images_async(urls, output_dir))


async def fetch_caption(url, input_path, model, semaphore):
    async with semaphore:
        filename = os.path.join(input_path, "images", url.split('/')[-1])
        with open(filename, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")
        message = HumanMessage(
            content=[
                {"type": "text", "text": "describe the scene."},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{image_data}"},
                },
            ],
        )
        response = await model.invoke([message])
        return url, response.content

def caption_images(urls,images_path, output_filepath=None):
    captions = {}
    model = ChatOpenAI(model="gpt-4o")
    semaphore = asyncio.Semaphore(10)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    with ThreadPoolExecutor() as executor:
        futures = [loop.run_in_executor(executor, fetch_caption, url, images_path, model, semaphore) for url in urls]
        results = loop.run_until_complete(asyncio.gather(*futures))
    for result in results:
        captions[result[0]] = result[1]
    if output_filepath:
        with open(output_filepath, 'w') as f:
            json.dump(captions, f, indent=4)
    return captions

