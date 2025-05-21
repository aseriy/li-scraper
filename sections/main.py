from bs4 import BeautifulSoup
from pathlib import Path

def clean_dict(d):
    return {k: v for k, v in d.items() if v is not None}

def parse(context, profile, output_dir):
    section = "main"
    url = f"https://www.linkedin.com/in/{profile}"

    page = context.pages[0] if context.pages else context.new_page()
    page.goto(url)
    page.wait_for_timeout(5000)

    # Expand "...see more" in About section if it exists
    try:
        see_more_btn = page.query_selector("button.inline-show-more-text__see-more")
        if see_more_btn and see_more_btn.is_visible():
            see_more_btn.click()
            page.wait_for_timeout(500)
    except:
        pass

    # Re-extract full page HTML after possible DOM changes
    html = page.content()

    with open(Path(output_dir) / f"{profile}.{section}.html", "w", encoding="utf-8") as f:
        f.write(html.strip())

    soup = BeautifulSoup(html, "html.parser")
    name = headline = about = followers = None

    # Name
    name_tag = soup.select_one("h1")
    if name_tag:
        name = name_tag.get_text(strip=True)

    # Headline
    headline_tag = soup.select_one("div.text-body-medium") or soup.select_one("div.text-body-medium.break-words")
    if headline_tag:
        headline = headline_tag.get_text(strip=True)

    # Followers
    for span in soup.select("main span[aria-hidden='true']"):
        text = span.get_text(strip=True)
        if "follower" in text.lower():
            followers = text
            break

    # About section
    about_tag = soup.select_one("div[class*='inline-show-more-text'] span[aria-hidden='true']")
    print("💬 ABOUT HTML TAG:", about_tag)
    if about_tag:
        about = about_tag.get_text(separator="\n", strip=True)
        print("💬 ABOUT TEXT:", repr(about))

    return clean_dict({
        "name": name,
        "headline": headline,
        "followers": followers,
        "about": about
    })
