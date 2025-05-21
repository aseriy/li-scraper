from bs4 import BeautifulSoup
import re
from pathlib import Path

def clean_dict(d):
    return {k: v for k, v in d.items() if v is not None}

def parse(context, profile, output_dir):
    section = "certifications"
    url = f"https://www.linkedin.com/in/{profile}/details/{section}/"

    page = context.pages[0] if context.pages else context.new_page()
    page.goto(url)
    page.wait_for_timeout(5000)

    content = page.query_selector("main")
    if not content:
        return None
    html = content.inner_html()

    with open(Path(output_dir) / f"{profile}.{section}.html", "w", encoding="utf-8") as f:
        f.write(html.strip())

    soup = BeautifulSoup(html, "html.parser")
    cert_items = soup.select("li.pvs-list__paged-list-item")
    certifications = []

    for item in cert_items:
        name = issuer = issue_date = credential_id = credential_url = None
        skills = []

        name_tag = item.select_one("div.t-bold span[aria-hidden='true']")
        if name_tag:
            name = name_tag.get_text(strip=True)

        issuer_tag = item.select_one("span.t-14.t-normal > span[aria-hidden='true']")
        if issuer_tag:
            issuer = issuer_tag.get_text(strip=True)

        date_tag = item.select_one("span.pvs-entity__caption-wrapper[aria-hidden='true']")
        if date_tag:
            date_text = date_tag.get_text(strip=True)
            match = re.search(r"Issued\s+(\w+\s+\d{4})", date_text)
            if match:
                issue_date = match.group(1).strip()

        black_light_spans = item.select("span.t-14.t-normal.t-black span[aria-hidden='true']")
        for span in black_light_spans:
            text = span.get_text(strip=True)
            if "credential id" in text.lower():
                credential_id = text.replace("Credential ID", "").strip()

        url_tag = item.select_one("a[href*='coursera.org'], a[href*='credly.com'], a[href*='linkedin.com/learning'], a[href*='verify']")
        if url_tag and url_tag.has_attr("href"):
            credential_url = url_tag["href"]

        skill_tags = item.select("span[aria-hidden='true']")
        for tag in skill_tags:
            text = tag.get_text(strip=True)
            if text.lower().startswith("skills:"):
                skills = [s.strip() for s in text.replace("Skills:", "").split("\u00b7") if s.strip()]

        certifications.append(clean_dict({
            "name": name,
            "issuer": issuer,
            "issue_date": issue_date,
            "credential_id": credential_id,
            "credential_url": credential_url,
            "skills": skills if skills else None
        }))

    return certifications if certifications else None
