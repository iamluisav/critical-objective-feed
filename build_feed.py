import json
import requests
import sqlite3
import time
from bs4 import BeautifulSoup
from datetime import datetime
import xml.etree.ElementTree as ET
from urllib.parse import urljoin

DB_PATH = "description_cache.db"

def init_cache():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS descriptions (
            job_id TEXT PRIMARY KEY,
            description TEXT,
            fetched_at TEXT
        )
    """)
    conn.commit()
    return conn

def get_cached_description(conn, job_id):
    row = conn.execute("SELECT description FROM descriptions WHERE job_id = ?", (job_id,)).fetchone()
    return row[0] if row else None

def set_cached_description(conn, job_id, description):
    conn.execute(
        "INSERT OR REPLACE INTO descriptions (job_id, description, fetched_at) VALUES (?, ?, ?)",
        (job_id, description, datetime.now().isoformat())
    )
    conn.commit()

def fetch_greenhouse_description(conn, slug, job_id):
    cached = get_cached_description(conn, f"greenhouse:{job_id}")
    if cached is not None:
        return cached
    try:
        url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs/{job_id}"
        res = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        res.raise_for_status()
        data = res.json()
        description = data.get("content", "") or ""
        # Strip HTML tags
        if description:
            soup = BeautifulSoup(description, "html.parser")
            description = soup.get_text(separator="\n").strip()
        set_cached_description(conn, f"greenhouse:{job_id}", description)
        time.sleep(0.1)
        return description
    except Exception:
        return ""

def get_logo(url):
    try:
        res = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(res.text, "html.parser")

        og = soup.find("meta", property="og:image")
        if og and og.get("content"):
            return urljoin(url, og["content"])

        imgs = soup.find_all("img")
        for img in imgs:
            src = img.get("src", "")
            alt = (img.get("alt") or "").lower()
            cls = " ".join(img.get("class", [])) if img.get("class") else ""
            combined = f"{src} {alt} {cls}".lower()
            if "logo" in combined:
                return urljoin(url, src)

        icon = soup.find("link", rel=lambda x: x and "icon" in x.lower())
        if icon and icon.get("href"):
            return urljoin(url, icon["href"])

        return urljoin(url, "/favicon.ico")
    except Exception:
        return ""

def normalize_job_type(value):
    if not value:
        return "fulltime"
    v = value.strip().lower()
    mapping = {
        "full-time": "fulltime",
        "full time": "fulltime",
        "fulltime": "fulltime",
        "part-time": "parttime",
        "part time": "parttime",
        "parttime": "parttime",
        "contract": "contract",
        "contractor": "contract",
        "intern": "internship",
        "internship": "internship",
        "temporary": "temporary",
        "volunteer": "volunteer"
    }
    return mapping.get(v, "fulltime")

def normalize_location_type(workplace_type="", location_text=""):
    text = f"{workplace_type or ''} {location_text or ''}".strip().lower()
    if "hybrid" in text:
        return "hybrid"
    if "remote" in text:
        return "remote"
    return "onsite"

def parse_lever(company):
    jobs = []
    res = requests.get(company["feed_url"], timeout=15, headers={"User-Agent": "Mozilla/5.0"})
    res.raise_for_status()

    data = res.json()
    logo_url = get_logo(company["company_url"])

    for post in data:
        categories = post.get("categories", {}) or {}

        location = categories.get("location", "") or ""
        commitment = categories.get("commitment", "") or ""
        department = categories.get("team", "") or ""

        description = post.get("descriptionPlain") or post.get("description") or ""
        apply_url = post.get("applyUrl", "") or ""
        job_url = post.get("hostedUrl", "") or ""

        created_at = post.get("createdAt")
        if created_at:
            try:
                published = datetime.fromtimestamp(created_at / 1000).strftime("%Y-%m-%d")
            except Exception:
                published = datetime.now().strftime("%Y-%m-%d")
        else:
            published = datetime.now().strftime("%Y-%m-%d")

        jobs.append({
            "job_id": post.get("id", ""),
            "job_title": post.get("text", ""),
            "description": description,
            "company_name": company["company_name"],
            "company_url": company["company_url"],
            "company_logo_url": logo_url,
            "application_link": apply_url,
            "publish_date": published,
            "job_type": normalize_job_type(commitment),
            "location": location,
            "location_type": normalize_location_type(commitment, location),
            "department": department,
            "job_url": job_url
        })

    return jobs

def parse_ashby(company):
    jobs = []
    res = requests.get(company["feed_url"], timeout=15, headers={"User-Agent": "Mozilla/5.0"})
    res.raise_for_status()

    root = ET.fromstring(res.content)
    logo_url = get_logo(company["company_url"])

    for job_el in root.findall("job"):
        def get(tag):
            el = job_el.find(tag)
            return el.text.strip() if el is not None and el.text else ""

        position = job_el.find("position")
        def safe_text(el):
            return (el.text or "").strip() if el is not None else ""
        title = safe_text(position.find("title")) if position is not None else ""
        description = safe_text(position.find("description")) if position is not None else ""
        location = ""
        location_el = position.find("location") if position is not None else None
        if location_el is not None:
            def loc_name(tag):
                el = location_el.find(tag)
                if el is not None:
                    name = el.find("name")
                    return name.text.strip() if name is not None and name.text else ""
                return ""
            city = loc_name("city")
            state = loc_name("state")
            country = loc_name("country")
            parts = [p for p in [city, state, country] if p]
            location = ", ".join(parts)

        workplace_type = get("workplaceType")
        is_remote = get("isRemote").lower()

        if workplace_type.lower() == "remote" or is_remote == "yes":
            loc_type = "remote"
        elif workplace_type.lower() == "hybrid":
            loc_type = "hybrid"
        else:
            loc_type = "onsite"

        jobs.append({
            "job_id": get("jobId"),
            "job_title": title,
            "description": description,
            "company_name": company["company_name"],
            "company_url": company["company_url"],
            "company_logo_url": logo_url,
            "application_link": get("applicationUrl"),
            "publish_date": datetime.now().strftime("%Y-%m-%d"),
            "job_type": normalize_job_type(get("employmentType")),
            "location": location,
            "location_type": loc_type,
            "department": get("department"),
            "job_url": get("jobUrl")
        })

    return jobs

def parse_greenhouse(company, conn):
    jobs = []
    res = requests.get(company["feed_url"], timeout=15, headers={"User-Agent": "Mozilla/5.0"})
    res.raise_for_status()

    data = res.json()
    logo_url = get_logo(company["company_url"])

    # Extract slug from feed_url: https://boards-api.greenhouse.io/v1/boards/{slug}/jobs
    feed_url = company["feed_url"]
    slug = feed_url.rstrip("/").split("/boards/")[-1].split("/")[0]

    total = len(data.get("jobs", []))
    print(f"  Fetching descriptions for {total} Greenhouse jobs...", flush=True)

    for i, post in enumerate(data.get("jobs", []), 1):
        job_id = str(post.get("id", ""))
        location = post.get("location", {}).get("name", "") or ""

        metadata = {m["name"]: m["value"] for m in post.get("metadata", []) or []}
        employment_type = metadata.get("Employment Type", "") or ""
        workplace_type = metadata.get("Workplace Type", "") or ""

        updated_at = post.get("updated_at", "")
        try:
            published = updated_at[:10] if updated_at else datetime.now().strftime("%Y-%m-%d")
        except Exception:
            published = datetime.now().strftime("%Y-%m-%d")

        apply_url = post.get("absolute_url", "")

        description = fetch_greenhouse_description(conn, slug, job_id)

        if i % 20 == 0:
            print(f"  ... {i}/{total}", flush=True)

        jobs.append({
            "job_id": job_id,
            "job_title": post.get("title", ""),
            "description": description,
            "company_name": company["company_name"],
            "company_url": company["company_url"],
            "company_logo_url": logo_url,
            "application_link": apply_url,
            "publish_date": published,
            "job_type": normalize_job_type(employment_type),
            "location": location,
            "location_type": normalize_location_type(workplace_type, location),
            "department": post.get("departments", [{}])[0].get("name", "") if post.get("departments") else "",
            "job_url": apply_url
        })

    return jobs

def build_csv(jobs):
    import csv
    with open("feed.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "Job title", "Job type", "Company name", "Company URL", "Company logo",
            "Job location", "Office location", "Location limits", "Description",
            "Apply URL", "Apply email", "Salary min", "Salary maximum",
            "Salary currency", "Salary schedule", "Highlighted", "Sticky",
            "Post length", "Post state", "Date posted", "Category name"
        ])
        writer.writeheader()
        for job in jobs:
            writer.writerow({
                "Job title": job.get("job_title", ""),
                "Job type": job.get("job_type", "fulltime"),
                "Company name": job.get("company_name", ""),
                "Company URL": job.get("company_url", ""),
                "Company logo": job.get("company_logo_url", ""),
                "Job location": job.get("location_type", "onsite"),
                "Office location": job.get("location", ""),
                "Location limits": "",
                "Description": job.get("description", ""),
                "Apply URL": job.get("application_link", ""),
                "Apply email": "",
                "Salary min": "",
                "Salary maximum": "",
                "Salary currency": "",
                "Salary schedule": "",
                "Highlighted": "false",
                "Sticky": "false",
                "Post length": "30",
                "Post state": "published",
                "Date posted": job.get("publish_date", ""),
                "Category name": job.get("department", "")
            })

def build_xml(jobs):
    root = ET.Element("jobs")

    for job in jobs:
        job_el = ET.SubElement(root, "job")
        for key, value in job.items():
            el = ET.SubElement(job_el, key)
            el.text = str(value or "")

    tree = ET.ElementTree(root)
    tree.write("feed.xml", encoding="utf-8", xml_declaration=True)

def main():
    with open("companies.json") as f:
        companies = json.load(f)

    conn = init_cache()
    all_jobs = []

    try:
        for company in companies:
            try:
                if company["source_type"] == "lever":
                    jobs = parse_lever(company)
                elif company["source_type"] == "ashby":
                    jobs = parse_ashby(company)
                elif company["source_type"] == "greenhouse":
                    jobs = parse_greenhouse(company, conn)
                else:
                    print(f"Skipping unsupported source_type: {company['source_type']}")
                    continue

                print(f"{company['company_name']}: found {len(jobs)} jobs")
                all_jobs.extend(jobs)

            except Exception as e:
                print(f"Error processing {company['company_name']}: {type(e).__name__}: {e}")
    finally:
        conn.close()

    build_xml(all_jobs)
    build_csv(all_jobs)
    print(f"\nBuilt feed.xml and feed.csv with {len(all_jobs)} total jobs")

if __name__ == "__main__":
    main()
