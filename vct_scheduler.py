import requests
from bs4 import BeautifulSoup
from datetime import datetime
from zoneinfo import ZoneInfo
from config import WEBHOOK_URL

URL = "https://www.vlr.gg/matches"

def get_region(event_name):
    if event_name.startswith("VCT"):
        for region in ["Americas", "EMEA", "Pacific", "China"]:
            if region in event_name:
                return region.lower()
                
    if event_name.startswith("Valorant Champions") or event_name.startswith("Valorant Masters"):
        return "global"
            
    return None

r = requests.get(URL, timeout=20)
r.raise_for_status()
soup = BeautifulSoup(r.content, 'html5lib') # If this line causes an error, run 'pip install html5lib' or install html5lib

matches = soup.select("a.match-item")

messages_by_region = {
    "global": [],
    "americas": [],
    "emea": [],
    "pacific": [],
    "china": [],
}
found_count = 0

for match in matches:
    event_element = match.select_one(".match-item-event")
    event_parts = event_element.find_all(string=True, recursive=False)
    event_name = " ".join(part.strip() for part in event_parts).strip()
    
    region = get_region(event_name)
    if region is None:
        continue
    
    teams = match.select(".match-item-vs-team-name")
    
    team_one = teams[0].get_text(" ", strip=True)
    team_two = teams[1].get_text(" ", strip=True)
    
    match_path = match["href"]
    match_url = "https://www.vlr.gg" + match_path
    
    match_response = requests.get(match_url, timeout=20)
    match_response.raise_for_status()
    match_soup = BeautifulSoup(match_response.content, "html5lib")

    event_header = match_soup.select_one(".match-header-event")
    event_url = "https://www.vlr.gg" + event_header["href"]

    stage_element = event_header.select_one(".match-header-event-series")
    stage_name = " ".join(stage_element.get_text().split())

    date_header = match_soup.select_one(".match-header-date")
    date_element = date_header.select_one('[data-moment-format="dddd, MMMM D"]')
    time_element = date_header.select_one('[data-moment-format="h:mm A z"]')

    match_date = date_element.get_text(" ", strip=True)
    match_time = time_element.get_text(" ", strip=True)
    raw_time = time_element["data-utc-ts"]
    
    vlr_time = datetime.strptime(raw_time, "%Y-%m-%d %H:%M:%S")
    vlr_time = vlr_time.replace(tzinfo=ZoneInfo("America/New_York"))
    unix_time = int(vlr_time.timestamp())

    patch = next(
        (text for text in date_header.stripped_strings if text.startswith("Patch ")),
        None,
    )

    date_time_line = f"{match_date} • {match_time}"
    your_time_line = f"🕒 <t:{unix_time}:F> (<t:{unix_time}:R>)"

    if patch is not None:
        date_time_line += f" • *{patch}*"

    message = "\n".join([
        f"[**{event_name}**]({event_url})",
        stage_name,
        "",
        f"**{team_one} vs {team_two}**",
        date_time_line,
        your_time_line,
        f"[Match details]({match_url})",
    ])
    
    messages_by_region[region].append(message)
    found_count += 1

    if found_count == 4:
        break
    

if found_count == 0:
    print("No VCT matches found.")

separator = "\n\n" + "─" * 30 + "\n\n"

for region, region_messages in messages_by_region.items():
    if not region_messages:
        continue

    print(f"===== #vct-{region}-schedules =====")
    print(separator.join(region_messages))
    print()
    
    if region == "global":
        text = separator.join(region_messages)
        requests.post(WEBHOOK_URL, json={"content": text, "flags": 4})