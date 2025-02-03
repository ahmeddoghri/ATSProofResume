import requests
from bs4 import BeautifulSoup
import re

def scrape_job_posting(url):
    """Scrapes job details from the given URL."""
    
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
    except requests.RequestException as e:
        return {"company": "Unknown_Company", "content": f"Failed to fetch job posting: {e}"}

    soup = BeautifulSoup(response.text, "html.parser")
    
    job_text = soup.get_text(separator="\n", strip=True)
    
    company_name = "Unknown_Company"
    meta_tags = ["company", "organization", "employer"]
    
    for tag in meta_tags:
        meta_tag = soup.find("meta", {"name": tag})
        if meta_tag and "content" in meta_tag.attrs:
            company_name = re.sub(r"[^a-zA-Z0-9_\-]", "_", meta_tag["content"])
            break

    return {"company": company_name, "content": job_text}