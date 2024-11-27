import asyncio
import json
import os
from typing import List

from langchain_openai import ChatOpenAI
from pydantic import Field, BaseModel

from website_scraper import run_content_map_creation
from image_captions import get_image_links, download_images, caption_images
from audit import audit_images, audit_website
from report_generator import generate_full_reports, generate_output_reports
import pdfkit
from markdown import markdown
import glob


def reports_to_pdfs(org_name):
    # Get a list of all JSON file names in the reports subfolder
    json_files = glob.glob(os.path.join(org_name, "reports", "*.json"))
    if not json_files:
        print("No JSON files found in the reports subfolder.")
        return

    # Print the list of JSON file names
    if not os.path.exists(os.path.join(org_name,"pdf_reports")):
        os.makedirs(os.path.join(org_name,"pdf_reports"))
    for json_file in json_files:
        with open(json_file, "r") as file:
            # Load the JSON content
            md_report = json.load(file)[0]
        md_report = md_report.replace('```markdown','').replace('```','')
        filename = os.path.basename(json_file)
        # Convert Markdown to HTML
        html_content = markdown(md_report)
        # Path to save the PDF
        output_pdf_path = os.path.join(org_name,"pdf_reports",filename.replace(".json", ".pdf"))
        # Convert HTML to PDF
        config = pdfkit.configuration(wkhtmltopdf=r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe')
        pdfkit.from_string(html_content, output_pdf_path, configuration=config)


def main(org_name, base_url, stakeholders_dict, mission_statement):
    if not os.path.exists(org_name):
        os.makedirs(org_name)
    else:
        pass

    if os.path.exists(os.path.join(org_name,"website_map.json")):
        with open(os.path.join(org_name,"website_map.json"),encoding="utf-8") as f:
            website_map = json.load(f)
    else:
        website_map = run_content_map_creation(base_url,os.path.join(org_name,"website_map.json"))
    
    image_links = get_image_links(website_map= website_map,base_url= base_url)
    
    download_images(urls= image_links, output_dir= org_name)

    if os.path.exists(os.path.join(org_name,"captions.json")):
        with open(os.path.join(org_name,"captions.json"),encoding="utf-8") as f:
            captions = json.load(f)
    else:
        captions = caption_images(urls= image_links, images_path= os.path.join(org_name,"images"), output_filepath= os.path.join(org_name,"captions.json"))
    
    if os.path.exists(os.path.join(org_name,"website_audit.json")):
        with open(os.path.join(org_name,"website_audit.json"),encoding="utf-8") as f:
            url_reports = json.load(f)
    else:
        url_reports = audit_website(website_map, stakeholders_dict, mission_statement, os.path.join(org_name,'website_audit.json'))
    
    if os.path.exists(os.path.join(org_name,"images_audit.json")):
        with open(os.path.join(org_name,"images_audit.json"),encoding="utf-8") as f:
            image_reports = json.load(f)
    else:
        image_reports = audit_images(captions, website_map, base_url, stakeholders_dict,os.path.join(org_name,'images_audit.json'))


    class Report(BaseModel):
        benefits: List[str] = Field(description="The unique benefits for the stakeholder based on the combined context.")
        drawbacks: List[str] = Field(description="The unique drawbacks for the stakeholder based on the combined context.")

    llm = ChatOpenAI(model="gpt-4o")
    if os.path.exists(os.path.join(org_name,"output_reports.json")):
        with open(os.path.join(org_name,"output_reports.json"),encoding="utf-8") as f:
            output_reports = json.load(f)
    else:
        structured_llm = llm.with_structured_output(Report)
        output_reports = asyncio.run(generate_output_reports(url_reports,
                                                            image_reports,
                                                                stakeholders_dict,
                                                                structured_llm,
                                                                os.path.join(org_name,"output_reports.json")))
    output_reports_path = os.path.join(org_name,"reports")
    generate_full_reports(stakeholders_dict,output_reports,llm,output_reports_path)
    reports_to_pdfs(org_name)




if __name__ == "__main__":
    org_name = "HillelSv"
    base_url = "https://hillelsv.org/"
    stakeholders_dict = {
        "Board of Directors": "Responsible for overall governance and making strategic decisions.",
        "Staff": "Employees who work full-time or part-time for the organization.",
        "Volunteers": "Individuals who offer their time and services freely to support the organization’s mission.",
        "Donors": "People or entities that provide financial support to the organization.",
        "Beneficiaries": "Individuals or groups who directly benefit from the organization's work.",
        "Government Agencies": "Public sector organizations that might regulate or provide funding.",
        "Grant-Making Foundations": "Organizations that provide grants to support the non-profit’s activities.",
        "Partners": "Other organizations or entities that collaborate with the non-profit.",
        "Media": "Press and news organizations that cover stories about the non-profit.",
        "Community Members": "Local individuals who are part of the community served by the non-profit."
    }

    mission_statement = 'Our mission at Hillel of Silicon Valley is to provide a welcoming and supportive environment for students, enriching their college experience and enabling them to connect with the Jewish community and Israel. We strive to inspire the next generation of Jews through meaningful Jewish experiences when they need us the most.'

    main(org_name, base_url, stakeholders_dict, mission_statement)

