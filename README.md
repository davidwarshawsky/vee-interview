# Vee Interview Project

## Overview
The thought process started out as I'm going to make a langgraph graph that repeatedly gets the URLs with the same base URL and text from each URL with a tool call and then
maps out the URLs of the page starting out on the homepage of the organization. The jpg and png links linked to on each URL are extracted and are captioned. The text and image captions
are summarized into their benefits and drawbacks for each individual stakeholder desired. Then all the summaries with their corresponding URL are combined and summarized in chunks.
Those summarized chunks are put together and a report is created in raw markdown through prompt engineering which is then converted into a PDF.

In the end, I used langchain as this task does not actually require langgraph. Langgraph is mainly useful in situations with interactive use and not for basic summarization. 
The workflow is not trivial but using langgraph overcomplicates something that the user doesn't have control over other than which stakeholders they are interested in and the mission statement.

## Features
- Generates PDF audit reports for the non-profit in a pdf_reports folder.
- All intermediate steps are stored inside of a folder named after the Organization.
- The program checks if the intermediate steps have been generated before to save recalculating.

## Getting Started
To get started with the project, clone the repository and navigate to the project directory.
Python 3.11.9 is required to guarantee functionality. 
Pip needs to be installed on the latest version.

```bash
git clone https://github.com/davidwarshawsky/vee-interview.git
cd vee-interview
```

## Prerequisites
- OpenAIKey in a .env file: `OPENAI_API_KEY=sk-AbCdEFghiJKLM....`
Make sure you have the following installed on your machine:
- Python 3.11.9

## Installation
```bash
python -m venv vee-interview
source vee-interview/bin/activate  # On Windows use `.\vee-interview\Scripts\activate`
pip install -r requirements.txt
```

If using Windows: Open PowerShell as Administrator and run:
```bash
winget install wkhtmltopdf
```

If using macOS:
1. Install Homebrew if not yet on the system:
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```
2. Install wkhtmltopdf with Homebrew:
```bash
brew install wkhtmltopdf
```
3. Verify installation:
```bash
wkhtmltopdf --version
```

If the command isn't working (Windows), you'll need to add wkhtml to the path in PowerShell:
1. Open a new PowerShell as Administrator.
2. Verify that this works:
```bash
& "C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe" --version
```
3. If it does work, add it to the path with:
```bash
[System.Environment]::SetEnvironmentVariable("Path", "$env:Path;C:\Program Files\wkhtmltopdf\bin", [System.EnvironmentVariableTarget]::Machine)
```
4. Then you'll need to set the config variable in `main.py`:
```python
config = pdfkit.configuration(wkhtmltopdf=r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe')
```
If on macOS, comment out the above config line in `main.py`.

There shouldn't be issues with paths between Windows, macOS, and Linux due to os.path.join which uses system path separators.

## License
This project is copyrighted by David Warshawsky. All Rights Reserved with License to Idan Tovi at Vee for non-commercial use for validating the project.

## Contact
For any questions or feedback, please open an issue or contact us at [davidawarshawsky@gmail.com](mailto:davidawarshawsky@gmail.com).