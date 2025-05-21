import re
from bs4 import BeautifulSoup
from datetime import datetime
from collections import defaultdict
from pathlib import Path

def parse_duration_string(duration_str):
    if not duration_str:
        return 0
    years = months = 0
    match_years = re.search(r"(\d+)\s+yr", duration_str)
    match_months = re.search(r"(\d+)\s+mo", duration_str)
    if match_years:
        years = int(match_years.group(1))
    if match_months:
        months = int(match_months.group(1))
    return years * 12 + months

def format_duration(months_total):
    years, months = divmod(months_total, 12)
    parts = []
    if years:
        parts.append(f"{years} yr{'s' if years > 1 else ''}")
    if months:
        parts.append(f"{months} mo{'s' if months > 1 else ''}")
    return " ".join(parts) if parts else None

def clean_dict(d):
    return {k: v for k, v in d.items() if v is not None}

def parse(context, profile, output_dir):
    section = "experience"
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
    experience_items = soup.select("li.pvs-list__paged-list-item")
    experiences = []

    for item in experience_items:
        sub_roles = item.select("li.pvs-list__item--one-column")
        if sub_roles:
            company_tag = item.select_one("div.t-bold span[aria-hidden='true']")
            company = company_tag.get_text(strip=True) if company_tag else None

            for sub in sub_roles:
                title = start_date = end_date = duration = description = None

                title_tag = sub.select_one("div.t-bold span[aria-hidden='true']")
                if title_tag:
                    title = title_tag.get_text(strip=True)

                date_tag = sub.select_one("span.pvs-entity__caption-wrapper[aria-hidden='true']")
                if date_tag:
                    date_text = date_tag.get_text(strip=True)
                    date_match = re.search(r"([A-Za-z]+\s\d{4}|\d{4})\s*[-to]+\s*(Present|[A-Za-z]+\s\d{4}|\d{4})", date_text)
                    duration_match = re.search(r"\u00b7\s*(.+)", date_text)
                    if date_match:
                        start_date = date_match.group(1).strip()
                        end_date = date_match.group(2).strip()
                    if duration_match:
                        duration = duration_match.group(1).strip()

                desc_tag = sub.select_one("div.t-14.t-normal.t-black span[aria-hidden='true']")
                if desc_tag:
                    description = desc_tag.get_text(" ", strip=True)

                experiences.append(clean_dict({
                    "title": title,
                    "company": company,
                    "start_date": start_date,
                    "end_date": end_date,
                    "duration": duration,
                    "description": description
                }))
            continue

        title = company = start_date = end_date = duration = description = None

        title_tag = item.select_one("div.hoverable-link-text.t-bold span[aria-hidden='true']")
        if title_tag:
            title = title_tag.get_text(strip=True)

        company_tag = item.select_one("span.t-14.t-normal > span[aria-hidden='true']")
        if company_tag:
            raw_company = company_tag.get_text(strip=True)
            if re.match(r"\d{4}.*\u00b7.*", raw_company):
                continue
            company = raw_company

        date_tag = item.select_one("span.pvs-entity__caption-wrapper[aria-hidden='true']")
        if date_tag:
            date_text = date_tag.get_text(strip=True)
            date_match = re.search(r"([A-Za-z]+\s\d{4}|\d{4})\s*[-to]+\s*(Present|[A-Za-z]+\s\d{4}|\d{4})", date_text)
            duration_match = re.search(r"\u00b7\s*(.+)", date_text)
            if date_match:
                start_date = date_match.group(1).strip()
                end_date = date_match.group(2).strip()
            if duration_match:
                duration = duration_match.group(1).strip()

        desc_tag = item.select_one("div.t-14.t-normal.t-black span[aria-hidden='true']")
        if desc_tag:
            description = desc_tag.get_text(" ", strip=True)

        experiences.append(clean_dict({
            "title": title,
            "company": company,
            "start_date": start_date,
            "end_date": end_date,
            "duration": duration,
            "description": description
        }))

    unique = {}
    for exp in experiences:
        key = (exp.get("title"), exp.get("start_date"))
        if key not in unique:
            unique[key] = exp

    def parse_date_safe(date_str):
        try:
            return datetime.strptime(date_str, "%b %Y")
        except:
            try:
                return datetime.strptime(date_str, "%Y")
            except:
                return None

    grouped_dict = defaultdict(list)
    for role in unique.values():
        company = role.get("company")
        role_copy = {k: v for k, v in role.items() if k != "company"}
        grouped_dict[company].append(role_copy)

    grouped_output = []
    for company, roles in grouped_dict.items():
        sorted_roles = sorted(roles, key=lambda r: parse_date_safe(r.get("start_date")) or datetime.min)
        total_months = sum(parse_duration_string(r.get("duration")) for r in sorted_roles if r.get("duration"))

        start_dates = [parse_date_safe(r.get("start_date")) for r in sorted_roles if r.get("start_date")]
        end_dates = [parse_date_safe(r.get("end_date")) for r in sorted_roles if r.get("end_date") and r.get("end_date", "").lower() != "present"]
        overall_start = min(start_dates) if start_dates else None
        overall_end = "Present" if any(r.get("end_date", "").lower() == "present" for r in sorted_roles) else (
            max(end_dates).strftime("%b %Y") if end_dates else None
        )

        grouped_output.append(clean_dict({
            "company": company,
            "start_date": overall_start.strftime("%b %Y") if overall_start else None,
            "end_date": overall_end,
            "duration": format_duration(total_months),
            "roles": [clean_dict(r) for r in sorted_roles]
        }))

    return grouped_output
