from itertools import chain
import asyncio
import os
import aiohttp
from tqdm import tqdm
from itertools import chain
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
load_dotenv()
import json

from typing import List
from pydantic import BaseModel,Field





class Report(BaseModel):
    benefits: List[str] = Field(description="The unique benefits for the stakeholder based on the combined context.")
    drawbacks: List[str] = Field(description="The unique drawbacks for the stakeholder based on the combined context.")


def process_text(text, max_tokens):
    """
    Processes the input text by splitting it into chunks based on the specified maximum number of tokens.
    Args:
        text (str): The input text to be processed.
        max_tokens (int): The maximum number of tokens allowed in each chunk.
    Returns:
        list: A list of text chunks, each containing up to max_tokens tokens.
    """
    # Check for token limit and split if necessary
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=max_tokens, chunk_overlap=200)
    text_chunks = text_splitter.split_text(text)
    return text_chunks

def summarize(text, system_message,llm):  # Adjust model as needed
    """
    Summarizes the given text using a language model.
    Args:
        text (str): The text to be summarized.
        system_message (str): The system message to be used in the summarization process.
        llm (object): The language model object that provides the `invoke` method for generating responses.
    Returns:
        list: A list of responses generated by the language model for each chunk of the text.
    """
    sys_message = SystemMessage(content=system_message)
    chunks = process_text(text,110_000)
    # Process each chunk and combine results
    results = []
    for chunk in chunks:
        messages = [sys_message,HumanMessage(content=chunk)]
        response = llm.invoke(messages)
        results.append(response)
    return results

def generate_report(context, llm,stakeholder):
    """Generates a report using the provided context and LLM.

    Args:
        context (str): The context for the report.
        llm: The language model to use.

    Returns:
        Report: A Report object containing benefits and drawbacks.
    """

    prompt = f"Analyze the following text and provide the unique benefits and drawbacks for the stakeholder {stakeholder}: {context}"

    # Use structured output to get a structured response
    response = llm.invoke([HumanMessage(content=prompt)])

    return response



async def process_page_and_stakeholder(url, stakeholder, website_reviews, images_reviews, llm):
    """
    Process a page and stakeholder to generate a report.
    Args:
        url (str): The URL of the page to process.
        stakeholder (str): The stakeholder to consider.
        website_reviews (dict): A dictionary containing website reviews with pages as keys.
        images_reviews (dict): A dictionary containing image reviews.
        llm (object): A language model object used for processing.
    Returns: 
        tuple: A tuple containing the URL, stakeholder, and the generated report.

        """
    context = '\n'.join([website_reviews[url][stakeholder], images_reviews[url][stakeholder] if url in images_reviews else ""])
    summaries = summarize(context, f"Provide a list of unique benefits and drawbacks for the stakeholder {stakeholder}: ", llm)
    benefits = list(chain(*[summary.benefits for summary in summaries]))
    drawbacks = list(chain(*[summary.drawbacks for summary in summaries]))
    benefits_drawbacks = benefits + drawbacks
    context = '\n'.join(benefits_drawbacks)
    report = generate_report(context, llm,stakeholder)
    return url, stakeholder, report


async def generate_output_reports(website_reviews, image_reviews, stakeholders_dict, llm,output_reports_path=None):
    """
    Generate output reports for website and image reviews for each stakeholder.
    This function processes reviews for each page and stakeholder, generates reports, and optionally saves them to a specified file path.
    Args:
        website_reviews (dict): A dictionary containing website reviews with pages as keys.
        image_reviews (dict): A dictionary containing image reviews.
        stakeholders_dict (dict): A dictionary containing stakeholders information.
        llm (object): A STRUCTURED language model object used for processing. Report Pydantic BaseModel with fields.
        output_reports_path (str, optional): The file path to save the output reports. Defaults to None.
    Returns:
        dict: A dictionary containing the generated reports for each page and stakeholder.
    """

    output_reports = {}
    async with aiohttp.ClientSession():
        tasks = []
        for page in tqdm(list(website_reviews.keys()),"Generating reports for each page"):
            for stakeholder in stakeholders_dict:
                task = asyncio.create_task(process_page_and_stakeholder(page, stakeholder, website_reviews, image_reviews, llm))
                tasks.append(task)
            results = await asyncio.gather(*tasks)
            for url, stakeholder, report in results:
                output_reports.setdefault(url, {})[stakeholder] = {
                    "benefits": report.benefits,
                    "drawbacks": report.drawbacks
                }
    if output_reports_path:
        with open(output_reports_path,"w") as f:
            json.dump(output_reports,f,indent=4)
    return output_reports


def generate_full_reports(stakeholders,output_reports,llm,output_directory=None):
    """
    Generates detailed reports for each stakeholder based on the provided output reports.
    Args:
        stakeholders (list): A list of stakeholders for whom the reports are to be generated.
        output_reports (dict): A dictionary containing the benefits and drawbacks for each stakeholder, keyed by URL.
        llm (object): The language model used to generate the summaries. 
    Returns:
        None
    The function creates a detailed report for each stakeholder by:
    1. Generating a system prompt for the language model.
    2. Compiling the benefits and drawbacks from the output reports.
    3. Summarizing the compiled information using the language model.
    4. Saving the summaries in a JSON file named after the stakeholder.
    """
    if not output_directory:
        output_directory = "reports"
        if not os.path.exists("reports"):
            os.makedirs("reports")
    else:
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)
    for stakeholder in stakeholders:
        system_prompt = """
                Provide the benefits and drawbacks of how {stakeholder} view the nonprofit.
                Provide specific benefits and drawbacks with links to the website and how certain links have drawbacks or benefits.
                Explain how the non-profit could highlight it's strengths better and how it can improve its image with regards to is drawbacks.
                Provide in-depth examples.
                Make recommendations on how to improve. 
                A detailed report with sections. 
                The report should be in raw markdown.
                Provide no precursor or post cursor text.
                """.format(stakeholder=stakeholder)
        full_context = []
        for url in output_reports:
            benefits, drawbacks = '\n'.join(output_reports[url][stakeholder]["benefits"]), '\n'.join(output_reports[url][stakeholder]["drawbacks"])
            full_context.append(f"{url}:\nBenefits:\n{benefits}\nDrawbacks:\n{drawbacks}")
        full_context = '\n'.join(full_context)
        summaries = summarize(full_context, system_prompt,llm)
        summaries = [summary.content for summary in summaries]
        path = os.path.join(output_directory,f"{stakeholder}_report.json")
        with open(path,"w") as f:
            json.dump(summaries,f,indent=4)
