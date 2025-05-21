import json
import argparse
import os
from pathlib import Path
from playwright.sync_api import sync_playwright
from sections.main import parse as parse_main
from sections.experience import parse as parse_experience
from sections.education import parse as parse_education
from sections.certifications import parse as parse_certifications
from sections.skills import parse as parse_skills
from sections.recommendations import parse as parse_recommendations
from sections.publications import parse as parse_publications
from sections.patents import parse as parse_patents

VALID_SAMESITE = {"Strict", "Lax", "None"}

def normalize_samesite(value):
    return value if value in VALID_SAMESITE else "Lax"


def scrape_section(context, profile, section, output_dir):
    parser = globals().get(f"parse_{section}")
    if not parser:
        return None
    section_json = parser(context, profile, output_dir)

    return section_json


def scrape_profile(context, profile, output_dir):
    sections = [
        "main",
        # "experience",
        # "education",
        # "certifications",
        # "skills",
        # "recommendations",
        # "publications",
        # "patents"
    ]

    profile_json = {}
    os.makedirs(output_dir, exist_ok=True)

    for section in sections:
        section_json = scrape_section(context, profile, section, output_dir)
        if section_json is not None:
            profile_json[section] = section_json

    with open(Path(output_dir) / f"{profile}.json", "w", encoding="utf-8") as f:
        json.dump(profile_json, f, indent=2)



def main():
    parser = argparse.ArgumentParser(description="Scrape LinkedIn profile sections")
    parser.add_argument("--profiles", nargs="+", required=True, help="List of LinkedIn profile IDs to scrape")
    parser.add_argument("--cookies", default="linkedin_cookies.json", help="Path to the LinkedIn cookies JSON file")
    parser.add_argument("--output", default="output", help="Directory to save output files")
    args = parser.parse_args()

    with open(args.cookies, "r") as f:
        raw_cookies = json.load(f)

    cookies = [
        {
            "name": c["name"],
            "value": c["value"],
            "domain": c["domain"],
            "path": c.get("path", "/"),
            "secure": c.get("secure", True),
            "httpOnly": c.get("httpOnly", False),
            "sameSite": normalize_samesite(c.get("sameSite"))
        }
        for c in raw_cookies if ".linkedin.com" in c.get("domain", "")
    ]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        context.add_cookies(cookies)

        for profile in args.profiles:
            scrape_profile(context, profile, args.output)

        context.close()
        browser.close()

if __name__ == "__main__":
    main()
