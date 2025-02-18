import requests
from bs4 import BeautifulSoup
import re
import json
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers.json import JsonOutputParser 
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

class JobPostingScraper:
    def __init__(self):
        self.user_agent = "Mozilla/5.0"
        self.llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.0)
        self.extract_prompt_template = (
            "Extract the following details from the job posting text:\n"
            "1. Company Name\n"
            "2. Job Title\n"
            "3. The main job description text\n\n"
            "Return the output strictly as a JSON object with keys 'company', 'job_title', and 'job_text'. "
            "Only respond with valid JSON and nothing else.\n\n"
            "Job Posting Text:\n{job_posting_text}\n\n"
            "Output:"
        )
        self.extract_prompt = PromptTemplate(
            template=self.extract_prompt_template,
            input_variables=["job_posting_text"]
        )
        # Initialize the JSON output parser to force JSON output.
        self.json_parser = JsonOutputParser()

    def scrape_job_posting(self, url: str) -> dict:
        try:
            response = requests.get(url, headers={"User-Agent": self.user_agent})
            response.raise_for_status()
        except requests.RequestException as e:
            return {"company": "Unknown_Company", "job_title": "Unknown", "job_text": f"Failed to fetch job posting: {e}"}
        
        soup = BeautifulSoup(response.text, "html.parser")
        job_text = soup.get_text(separator="\n", strip=True)
        
        try:
            input_data = {"job_posting_text": job_text}
            result = (self.extract_prompt | self.llm | self.json_parser).invoke(input=input_data)
        except Exception as e:
            # Fallback if extraction fails
            return {"company": "Unknown_Company", "job_title": "Unknown", "job_text": "Job posting extraction failed."}
        
        return result  # dict with keys 'company', 'job_title', 'job_text'

    def capture_screenshot(self, url: str, output_path: str) -> None:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        driver = webdriver.Chrome(options=chrome_options)
        try:
            driver.get(url)
            driver.implicitly_wait(5)
            total_width = driver.execute_script("return document.body.scrollWidth")
            total_height = driver.execute_script("return document.body.scrollHeight")
            driver.set_window_size(total_width, total_height)
            driver.implicitly_wait(2)
            driver.save_screenshot(output_path)
        except Exception as e:
            print(f"Screenshot capture failed: {e}")
            # Optionally, you can create a placeholder image here
        finally:
            driver.quit()