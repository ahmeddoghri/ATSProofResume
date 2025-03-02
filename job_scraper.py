import requests
from bs4 import BeautifulSoup
import re
import json
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers.json import JsonOutputParser 
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from openai import OpenAI

class JobPostingScraper:
    def __init__(self, model_name="gpt-4o", temperature=0.0, api_key=None):
        """
        Initialize the scraper with GPT-4o for reliable extraction.
        """
        self.user_agent = "Mozilla/5.0"
        self.api_key = api_key
        # Always use GPT-4o for job scraping for reliable extraction
        self.llm = ChatOpenAI(
            model_name="gpt-4o",  # Force GPT-4o regardless of input
            temperature=0.0,      # Use 0 temperature for consistent results
            openai_api_key=api_key
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
            
            # More structured prompt with explicit JSON format
            extraction_prompt = f"""
            Extract the company name and job title from the following job posting text.
            
            Job Posting Text:
            {input_data["job_posting_text"]}
            
            Instructions:
            1. Identify the company that posted this job
            2. Identify the exact job title
            3. Return ONLY a valid JSON object with this exact format:
            {{
                "company": "Company Name Here",
                "job_title": "Job Title Here"
            }}
            
            Do not include any explanations, notes, or additional text. Only return the JSON object.
            """
            
            # Direct OpenAI call for more control
            client = OpenAI(api_key=self.api_key)
            response = client.chat.completions.create(
                model="gpt-4o",  # Always use GPT-4o for extraction
                messages=[
                    {"role": "system", "content": "You are a precise extraction tool that only outputs valid JSON."},
                    {"role": "user", "content": extraction_prompt}
                ],
                temperature=0.0,  # Use 0 temperature for deterministic results
                response_format={"type": "json_object"}  # Force JSON output
            )
            
            # Parse the JSON response
            try:
                result = json.loads(response.choices[0].message.content)
                # Validate the result has the required keys
                if "company" not in result or "job_title" not in result:
                    raise ValueError("Missing required keys in JSON response")
                
                # Add the full job text to the result
                result["job_text"] = job_text
                
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                print("JSON parsing failed, using regex extraction")
                # Try to extract using regex as a fallback
                company_match = re.search(r'"company"\s*:\s*"([^"]+)"', response.choices[0].message.content)
                title_match = re.search(r'"job_title"\s*:\s*"([^"]+)"', response.choices[0].message.content)
                
                company = company_match.group(1) if company_match else "Unknown_Company"
                job_title = title_match.group(1) if title_match else "Unknown"
                
                result = {
                    "company": company,
                    "job_title": job_title,
                    "job_text": job_text
                }
                
        except Exception as e:
            print(f"Extraction failed: {e}")
            # Try a simpler extraction approach as fallback
            try:
                # Look for common patterns in job postings
                title_patterns = [
                    r'<title>(.*?)</title>',
                    r'<h1[^>]*>(.*?)</h1>',
                    r'job title[:\s]*([^<\n]+)',
                    r'position[:\s]*([^<\n]+)',
                    r'role[:\s]*([^<\n]+)'
                ]
                
                company_patterns = [
                    r'company[:\s]*([^<\n]+)',
                    r'at ([A-Z][A-Za-z0-9\s&]+)',
                    r'join ([A-Z][A-Za-z0-9\s&]+)',
                    r'about ([A-Z][A-Za-z0-9\s&]+)'
                ]
                
                # Try to extract job title
                job_title = "Unknown"
                for pattern in title_patterns:
                    matches = re.search(pattern, job_text, re.IGNORECASE)
                    if matches:
                        job_title = matches.group(1).strip()
                        break
                        
                # Try to extract company
                company = "Unknown_Company"
                for pattern in company_patterns:
                    matches = re.search(pattern, job_text, re.IGNORECASE)
                    if matches:
                        company = matches.group(1).strip()
                        break
                
                return {
                    "company": company,
                    "job_title": job_title,
                    "job_text": job_text
                }
                
            except Exception as inner_e:
                print(f"Fallback extraction failed: {inner_e}")
                return {"company": "Unknown_Company", "job_title": "Unknown", "job_text": job_text}
        
        print("--------------------------------")
        print("EXTRACTION RESULT")
        print(result)
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
        Updates the API key but keeps using GPT-4o for job scraping.
        """
        self.api_key = api_key
        # Always use GPT-4o for job scraping regardless of the model selected
        self.llm = ChatOpenAI(
            model_name="gpt-4o",  # Force GPT-4o
            temperature=0.0,      # Use 0 temperature
            openai_api_key=api_key
        )