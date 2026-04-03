import requests
import json
import re
import time
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0"}

CANDIDATES = [
    ("Zanskar", "https://www.zanskar.com"),
    ("Figure", "https://www.figure.ai"),
    ("Clone Robotics", "https://clonerobotics.com"),
    ("Mark43", "https://www.mark43.com"),
    ("Cortical Labs", "https://www.corticallabs.com"),
    ("Antora Energy", "https://www.antoraenergy.com"),
    ("Anthro Energy", "https://www.anthroenergy.com"),
    ("Xona Space Systems", "https://www.xonaspace.com"),
    ("Stoke Space", "https://www.stokespace.com"),
    ("Ark Electronics", "https://arkelectron.com"),
    ("Astro Mechanica", "https://www.astromecha.co"),
    ("Atomic Machines", "https://www.atomicmachines.com"),
    ("Array Labs", "https://www.arraylabs.io"),
    ("Asylon Robotics", "https://www.asylonrobotics.com"),
    ("Base Power", "https://www.basepowercompany.com"),
    ("Blumen Systems", "https://www.blumensystems.com"),
    ("Atom Limbs", "https://www.atomlimbs.com"),
    ("AstroForge", "https://astroforge.com"),
    ("Vast", "https://www.vastspace.com"),
    ("Bedrock Energy", "https://www.bedrockenergy.com"),
    ("Bedrock Ocean", "https://www.bedrockocean.com"),
    ("Cerebras Systems", "https://www.cerebras.net"),
    ("Atomic Semi", "https://atomicsemi.com"),
    ("Brimstone", "https://www.brimstone.com"),
    ("Helion Energy", "https://www.helionenergy.com"),
    ("TurbineOne", "https://www.turbineone.com"),
    ("Roam Robotics", "https://www.roamrobotics.com"),
    ("CHAOS Industries", "https://www.chaosinc.com"),
    ("Cognition", "https://cognition.ai"),
    ("Skysafe", "https://www.skysafe.io"),
    ("Twelve", "https://www.twelve.co"),
    ("Bright Machines", "https://www.brightmachines.com"),
    ("Beacon AI", "https://www.beaconai.co"),
    ("Dawn Aerospace", "https://www.dawnaerospace.com"),
    ("Varda Space", "https://www.varda.com"),
    ("Collaborative Robotics", "https://www.co.bot"),
    ("Colossal Biosciences", "https://www.colossal.com"),
    ("Durin", "https://www.durin.com"),
    ("Zeno Power", "https://www.zenopower.com"),
    ("Earth AI", "https://www.earth-ai.com"),
    ("Mach Industries", "https://machindustries.com"),
    ("EarthGrid", "https://www.earthgrid.io"),
    ("Corvus Robotics", "https://www.corvus-robotics.com"),
    ("Arc Boats", "https://www.arcboats.com"),
    ("Astranis", "https://www.astranis.com"),
    ("Applied Intuition", "https://www.appliedintuition.com"),
    ("Apex Space", "https://www.apexspace.com"),
    ("Danti", "https://www.danti.ai"),
    ("Dusty Robotics", "https://www.dustyrobotics.com"),
    ("Cognitive Space", "https://www.cognitivespace.com"),
    ("Formlogic", "https://www.formlogic.com"),
    ("Gridware", "https://www.gridware.io"),
    ("Epsilon3", "https://www.epsilon3.io"),
    ("Exowatt", "https://www.exowatt.com"),
    ("Field AI", "https://www.fieldai.com"),
    ("Chariot Defense", "https://www.chariotdefense.com"),
    ("Formic", "https://www.formic.co"),
    ("Decagon", "https://decagon.ai"),
    ("Atmo", "https://www.atmo.ai"),
    ("Conductor AI", "https://www.conductorai.co"),
    ("Podium Automation", "https://www.podiumautomation.com"),
    ("Electric Air", "https://electricair.io"),
    ("Cosmic Robotics", "https://www.cosmicrobotics.com"),
    ("Cambridge Aerospace", "https://www.cambridgeaerospace.com"),
    ("Dirac", "https://www.diracinc.com"),
    ("Workrise", "https://workrise.com"),
    ("AtmoCooling", "https://www.atmocooling.com"),
    ("Flyby Robotics", "https://flybyrobotics.com"),
    ("Still Bright", "https://www.stillbright.co"),
    ("Deep Isolation", "https://www.deepisolation.com"),
    ("GenLogs", "https://www.genlogs.io"),
    ("Pila Energy", "https://pilaenergy.com"),
    ("Atopile", "https://www.atopile.io"),
    ("Blue Water Autonomy", "https://www.blw.ai"),
]

LEVER_RE = re.compile(r'jobs\.lever\.co/([a-zA-Z0-9_\-]+)', re.IGNORECASE)
ASHBY_RE = re.compile(r'jobs\.ashbyhq\.com/([a-zA-Z0-9_\-\.]+)', re.IGNORECASE)
ASHBY_API_RE = re.compile(r'app\.ashbyhq\.com/api/xml-feed/job-postings/organization/([a-zA-Z0-9_\-\.]+)', re.IGNORECASE)
GREENHOUSE_RE = re.compile(r'boards\.greenhouse\.io/([a-zA-Z0-9_\-]+)', re.IGNORECASE)

def check_url(url):
    try:
        r = requests.get(url, timeout=10, headers=HEADERS, allow_redirects=True)
        return r.text
    except Exception:
        return ""

def detect(company_name, company_url):
    pages_to_check = [
        company_url,
        company_url.rstrip("/") + "/careers",
        company_url.rstrip("/") + "/jobs",
        company_url.rstrip("/") + "/about/careers",
        company_url.rstrip("/") + "/work-with-us",
    ]

    found_text = ""
    for page in pages_to_check:
        text = check_url(page)
        if text:
            found_text += text
            # Stop early if we already found an ATS
            if (LEVER_RE.search(found_text) or ASHBY_RE.search(found_text) or
                    ASHBY_API_RE.search(found_text) or GREENHOUSE_RE.search(found_text)):
                break
        time.sleep(0.2)

    m = LEVER_RE.search(found_text)
    if m:
        slug = m.group(1)
        return {
            "company_name": company_name,
            "company_url": company_url,
            "source_type": "lever",
            "feed_url": f"https://api.lever.co/v0/postings/{slug}"
        }

    m = ASHBY_RE.search(found_text) or ASHBY_API_RE.search(found_text)
    if m:
        slug = m.group(1)
        return {
            "company_name": company_name,
            "company_url": company_url,
            "source_type": "ashby",
            "feed_url": f"https://app.ashbyhq.com/api/xml-feed/job-postings/organization/{slug}"
        }

    m = GREENHOUSE_RE.search(found_text)
    if m:
        slug = m.group(1)
        return {
            "company_name": company_name,
            "company_url": company_url,
            "source_type": "greenhouse",
            "feed_url": f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs"
        }

    return None

def main():
    with open("companies.json") as f:
        existing = json.load(f)

    existing_urls = {c["feed_url"] for c in existing}
    existing_names = {c["company_name"].lower() for c in existing}

    new_entries = []
    unsupported = []

    for company_name, company_url in CANDIDATES:
        if company_name.lower() in existing_names:
            print(f"SKIP (already exists): {company_name}")
            continue

        print(f"Checking {company_name}...", end=" ", flush=True)
        result = detect(company_name, company_url)

        if result and result["feed_url"] not in existing_urls:
            print(f"Found {result['source_type'].upper()} → {result['feed_url']}")
            new_entries.append(result)
        elif result:
            print(f"Already have feed")
        else:
            print("No supported ATS found")
            unsupported.append((company_name, company_url))

    if new_entries:
        existing.extend(new_entries)
        with open("companies.json", "w") as f:
            json.dump(existing, f, indent=2)
        print(f"\nAdded {len(new_entries)} new companies to companies.json")

    if unsupported:
        print(f"\nNo ATS detected for {len(unsupported)} companies:")
        for name, url in unsupported:
            print(f"  - {name}: {url}")

if __name__ == "__main__":
    main()
