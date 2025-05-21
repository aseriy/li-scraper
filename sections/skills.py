from bs4 import BeautifulSoup
import re
from pathlib import Path


def clean_dict(d):
    return {k: v for k, v in d.items() if v is not None}

def parse(context, profile, output_dir):
    section = "skills"
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
    skills = []

    for item in soup.select("li.pvs-list__paged-list-item"):
        name = endorsements = endorsed_by = context = url = None

        # Skill name
        name_tag = item.select_one(".t-bold span[aria-hidden='true']")
        if name_tag:
            name = name_tag.get_text(strip=True)

        # Skill URL (link to LinkedIn search or insights)
        link_tag = item.select_one("a[data-field='skill_page_skill_topic']")
        if link_tag and link_tag.has_attr("href"):
            url = link_tag['href']

        # All descriptive spans
        detail_spans = item.select("span[aria-hidden='true']")
        for span in detail_spans:
            text = span.get_text(strip=True)
            if re.match(r"\d+\+?\s+endorsement", text, re.IGNORECASE):
                endorsements = text.split()[0]
            elif text.lower().startswith("endorsed by"):
                endorsed_by = text.replace("Endorsed by", "").split("who")[0].strip()
            elif "experiences across" in text.lower():
                context = text

        skills.append(clean_dict({
            "name": name,
            "endorsements": endorsements,
            "endorsed_by": endorsed_by,
            "context": context,
            "url": url
        }))

    return skills
