import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import xml.etree.ElementTree as ET

def get_logo(url):
    try:
        res = requests.get(url, timeout=5)
        soup = BeautifulSoup(res.text, "html.parser")

        # Try og:image
        og = soup.find("meta", property="og:image")
        if og and og.get("content"):
            return og["content"]

        # Try logo-like image
        imgs = soup.find_all("img")
        for img in imgs:
            src = img.get("src", "").lower()
            if "logo" in src:
                return src

        # Fallback to favicon
        return url + "/favicon.ico"

    except:
        return ""

def normalize_job(job, company):
    return {
        "job_id": job.get("id", ""),
        "job_title": job.get("title", ""),
        "description": job.get("description", ""),
        "company_name": company["company_name"],
        "company_url": company["company_url"],
        "company_logo_url": get_logo(company["company_url"]),
        "application_link": job.get("apply_url", ""),
        "publish_date": datetime.now().strftime("%Y-%m-%d"),
        "job_type": "fulltime",
        "location": job.get("location", ""),
        "location_type": "onsite",
        "department": job.get("department", ""),
        "job_url": job.get("url", "")
    }

def build_xml(jobs):
    root = ET.Element("jobs")

    for job in jobs:
        job_el = ET.SubElement(root, "job")
        for key, value in job.items():
            el = ET.SubElement(job_el, key)
            el.text = value

    tree = ET.ElementTree(root)
    tree.write("feed.xml", encoding="utf-8", xml_declaration=True)

def main():
    with open("companies.json") as f:
        companies = json.load(f)

    all_jobs = []

    for company in companies:
        try:
            res = requests.get(company["feed_url"])
            data = res.text

            # TEMP placeholder — we’ll improve parsing next
            fake_job = {
                "id": company["company_name"],
                "title": "Sample Role",
                "description": "Placeholder until parsing is added",
                "apply_url": company["company_url"],
                "location": "Remote",
                "department": "",
                "url": company["company_url"]
            }

            all_jobs.append(normalize_job(fake_job, company))

        except Exception as e:
            print("Error:", e)

    build_xml(all_jobs)

if __name__ == "__main__":
    main()
