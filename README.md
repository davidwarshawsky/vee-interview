# Vee Interview Project

## Overview
The thought process started out as I'm going to make a langgraph graph that repeatedly gets the urls with the same base url and text from each url with a tool call and then
maps out the urls of the page starting out on the homepage of the organization. The jpg and png links linked to on each url are extracted and are captioned. The text and image captions
are summarized into their benefits and drawbacks for each individual stakeholder desired. Then all the summaries with their corresponding url are combined and summarized in chunks.
Those summarized chunks are put together and a report is created in raw markdown through prompt engineering which is then converted into a pdf.

In the end I used langchain as this task does not actually require langgraph. Langgraph is mainly useful in situations with interactive use and not for basic summarization. The workflow
is not trivial but using langgraph overcomplicates something that the user doesn't have control over other than which stakeholders they are interested in and the mission statment.

## Features
- Generates pdf audit reports for the non-profit in a pdf_reports folder.
- All intermediate steps are stored inside of a folder named after the Organization.
- The program checks if the intermediate steps have been generated before to save recalculating.

## Getting Started
To get started with the project, clone the repository and navigate to the project directory:

```bash
git clone https://github.com/davidwarshawsky/vee-interview.git
cd vee-interview
```

## Prerequisites
Make sure you have the following installed on your machine:
- [Node.js](https://nodejs.org/)
- [npm](https://www.npmjs.com/)

## Installation


## License
This project is copyrighted by David Warshawsky. All Rights Reserved except to Idan Tovi at Vee for non-commercial use for validating the project.

## Contact
For any questions or feedback, please open an issue or contact us at [davidawarshawsky@gmail.com](mailto:davidawarshawsky@gmail.com).
