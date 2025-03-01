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
    def __init__(self, model_name="gpt-3.5-turbo", temperature=0.0, api_key=None):
        """
        Initialize the scraper with configurable model parameters.
        """
        self.user_agent = "Mozilla/5.0"
        self.llm = ChatOpenAI(
            model_name=model_name,
            temperature=temperature,
            api_key=api_key
        )
        # Simplified prompt that only extracts company and job title
        self.extract_prompt_template = (
            "Extract ONLY the following details from the job posting text:\n"
            "1. Company Name\n"
            "2. Job Title\n\n"
            "Return the output strictly as a JSON object with keys 'company' and 'job_title'. "
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
        
        # Extract all text from the page - this will be saved directly
        job_text = soup.get_text(separator="\n", strip=True)
        
        try:
            # Only use LLM to extract company and job title
            input_data = {"job_posting_text": job_text[:4000]}  # Limit to first 4000 chars for extraction
            result = (self.extract_prompt | self.llm | self.json_parser).invoke(input=input_data)
            
            # Add the full job text to the result
            result["job_text"] = job_text
        except Exception as e:
            print(f"Extraction failed: {e}")
            # Fallback if extraction fails
            return {"company": "Unknown_Company", "job_title": "Unknown", "job_text": job_text}
        
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

    def update_model_config(self, model_name: str, temperature: float, api_key: str):
        """
        Updates the LLM configuration with new parameters.
        """
        self.llm = ChatOpenAI(
            model_name=model_name,
            temperature=temperature,
            api_key=api_key
        )