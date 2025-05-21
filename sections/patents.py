from bs4 import BeautifulSoup
import re
from pathlib import Path

def clean_dict(d):
    return {k: v for k, v in d.items() if v is not None}

def parse(context, profile, output_dir):
    section = "patents"
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
    patents = []

    for item in soup.select("li.pvs-list__paged-list-item"):
        title = patent_number = issue_date = description = None

        title_tag = item.select_one(".t-bold span[aria-hidden='true']")
        if title_tag:
            title = title_tag.get_text(strip=True)

        info_tag = item.select_one("span.t-14.t-normal span[aria-hidden='true']")
        if info_tag:
            text = info_tag.get_text(strip=True)
            parts = [p.strip() for p in text.split("\u00b7")]
            if len(parts) == 2:
                patent_number, issued = parts
                match = re.search(r"Issued\s+(\w+\s+\d{1,2},\s+\d{4})", issued)
                if match:
                    issue_date = match.group(1)

        desc_tag = item.select_one("div.t-14.t-normal.t-black span[aria-hidden='true']")
        if desc_tag:
            description = desc_tag.get_text(" ", strip=True)

        cleaned = clean_dict({
            "title": title,
            "patent_number": patent_number,
            "issue_date": issue_date,
            "description": description
        })

        if cleaned:
            patents.append(cleaned)

    return patents if patents else None