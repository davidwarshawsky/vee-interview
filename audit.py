import json

from langchain_openai import ChatOpenAI

def summarize_content(webpage_content, system_prompt):
    llm = ChatOpenAI(model='gpt-4o')
    response = llm.invoke(system_prompt + webpage_content)
    return response


def generate_mission_statement(homepage_text:str) -> str:
    system_prompt = "Create a mission statement for this organization"
    return summarize_content(webpage_content=homepage_text, system_prompt=system_prompt).content


def audit_website(website_map:dict, stakeholders:dict,mission_statement:str,output_map_path:str=None):
    output_map = {}
    for page, data in website_map.items():
        for stakeholder, description in stakeholders.items():
            system_prompt = """
                 "Tags refer to opening and closing XML tags.
                 All benefits and drawbacks sit inside {stakeholder} tags.
                 Cover the benefits and drawbacks from the perspective of {stakeholder}: {description}.
                 Provide specific examples as to how the content affects or informs {stakeholder}.
                 Keep this in the lens of the mission statement {mission_statement}.
                 First state all the benefits where each benefit is between opening and closing benefit tags.
                 Second state all the drawbacks where each drawback is between opening and closing drawback tags.
                 List all benefits first and then all drawbacks second. 
                 Provide no introduction, no precursor and no post cursor.\n"
                 """.format(stakeholder=stakeholder, description=description,
                            mission_statement=mission_statement.replace("\n", " "))
            summary = summarize_content(data['text'], system_prompt)
            if not page in output_map:
                output_map[page] = {stakeholder: summary.content}
            else:
                output_map[page][stakeholder] = summary.content
    if output_map_path:
        with open(output_map_path, 'w') as f:
            json.dump(output_map, f, indent=4)
    return output_map



def audit_images(captions, website_map,base_url,stakeholders,output_map_path=None):
    # captions_dict = {k: v for caption in captions for k, v in caption.items()}
    summaries_map = {}
    for url, data in website_map.items():
        links = data['links']
        if url.startswith(base_url):
            image_captions = [captions[link] for link in links if link.startswith(base_url) and (link.endswith('.jpg') or link.endswith('.png'))]
            images_text = "\n".join(image_captions)
            for stakeholder, description in stakeholders.items():
                system_prompt = """
                     "Tags refer to opening and closing XML tags.
                     All benefits and drawbacks sit inside {stakeholder} tags.
                     Cover the benefits and drawbacks from the perspective of {stakeholder}: {description}.
                     Provide specific examples as to how the content affects or informs {stakeholder}.
                     First state all the benefits where each benefit is between opening and closing benefit tags.
                     Second state all the drawbacks where each drawback is between opening and closing drawback tags.
                     List all benefits first and then all drawbacks second.
                     Provide no introduction, no precursor and no post cursor.\n"
                     """.format(stakeholder=stakeholder, description=description)
                try:
                    summary = summarize_content(images_text, system_prompt)
                    if not url in summaries_map:
                        summaries_map[url] = {stakeholder: summary.content}
                    else:
                        summaries_map[url][stakeholder] = summary.content
                except Exception as e:
                    summary = ""
                    if not url in summaries_map:
                        summaries_map[url] = {stakeholder: summary}
                    else:
                        summaries_map[url][stakeholder] = summary
    if output_map_path:
        with open(output_map_path, 'w') as f:
            json.dump(summaries_map, f, indent=4)
    return summaries_map