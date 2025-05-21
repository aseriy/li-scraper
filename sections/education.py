import re
from bs4 import BeautifulSoup
from pathlib import Path

def clean_dict(d):
    return {k: v for k, v in d.items() if v is not None}

def parse(context, profile, output_dir):
    section = "education"
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
    education_items = soup.select("li.pvs-list__paged-list-item")
    education_entries = []

    for item in education_items:
        school = degree = start_date = end_date = activities = description = None

        school_tag = item.select_one("div.t-bold span[aria-hidden='true']")
        if school_tag:
            school = school_tag.get_text(strip=True)

        degree_tag = item.select_one("span.t-14.t-normal > span[aria-hidden='true']")
        if degree_tag:
            degree = degree_tag.get_text(strip=True)

        date_tag = item.select_one("span.pvs-entity__caption-wrapper[aria-hidden='true']")
        if date_tag:
            date_text = date_tag.get_text(strip=True)
            match = re.match(r"(\w+ \d{4}|\d{4})\s*-\s*(\w+ \d{4}|\d{4}|Present)", date_text)
            if match:
                start_date = match.group(1).strip()
                end_date = match.group(2).strip()

        activities_tag = item.find("span", string=re.compile("activities and societies", re.I))
        if activities_tag:
            activities = activities_tag.find_parent().get_text(" ", strip=True).replace("Activities and societies:", "").strip()

        detail_spans = item.select("div.t-14.t-normal.t-black span[aria-hidden='true']")
        desc_lines = []
        for span in detail_spans:
            text = span.get_text(strip=True)
            if text and "activities and societies" not in text.lower():
                desc_lines.append(text)

        if desc_lines:
            description = " ".join(desc_lines)

        entry = clean_dict({
            "school": school,
            "degree": degree,
            "start_date": start_date,
            "end_date": end_date,
            "activities": activities,
            "description": description
        })

        education_entries.append(entry)

    return education_entries if education_entries else None
