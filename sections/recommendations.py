from bs4 import BeautifulSoup
import re
from pathlib import Path

def clean_dict(d):
    return {k: v for k, v in d.items() if v is not None}

def parse(context, profile, output_dir):
    section = "recommendations"
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
    recommendations = []

    for item in soup.select("li.pvs-list__paged-list-item"):
        name = headline = organization = date = relationship = text = profile_url = None

        name_tag = item.select_one("a.optional-action-target-wrapper span[aria-hidden='true']")
        if name_tag:
            name = name_tag.get_text(strip=True)

        profile_link = item.select_one("a.optional-action-target-wrapper")
        if profile_link and profile_link.has_attr("href"):
            profile_url = profile_link['href']

        headline_candidates = item.select("span.t-14.t-normal span[aria-hidden='true']")
        for candidate in headline_candidates:
            raw_headline = candidate.get_text(strip=True)
            if not re.match(r"^\u00b7\s*\d+(st|nd|rd)?$", raw_headline):
                if " at " in raw_headline:
                    headline, organization = map(str.strip, raw_headline.split(" at ", 1))
                else:
                    headline = raw_headline
                break

        date_tag = item.select_one("span.pvs-entity__caption-wrapper[aria-hidden='true']")
        if date_tag:
            date_text = date_tag.get_text(" ", strip=True)
            date_match = re.match(r"([A-Za-z]+ \d{1,2}, \d{4})", date_text)
            if date_match:
                date = date_match.group(1)
            relationship = date_text[len(date):].strip() if date else date_text

        text_tag = item.select_one("div.t-14.t-normal.t-black span[aria-hidden='true']")
        if text_tag:
            text = text_tag.get_text(" ", strip=True)

        recommendations.append(clean_dict({
            "name": name,
            "headline": headline,
            "organization": organization,
            "date": date,
            "relationship": relationship,
            "text": text,
            "profile_url": profile_url
        }))

    return recommendations if recommendations else None