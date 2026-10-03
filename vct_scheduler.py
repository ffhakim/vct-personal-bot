import discord
import json
import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from zoneinfo import ZoneInfo

URL = "https://www.vlr.gg/matches"

def get_region(event_name):
    if event_name.startswith("VCT"):
        for region in ["Americas", "EMEA", "Pacific", "China"]:
            if region in event_name:
                return region.lower()
                
    if event_name.startswith("Valorant Champions") or event_name.startswith("Valorant Masters"):
        return "global"
            
    return None

CITY_TIMEZONES = {
    "Shanghai": "Asia/Shanghai",
    "Los Angeles": "America/Los_Angeles",
    "Berlin": "Europe/Berlin",
    "Seoul": "Asia/Seoul",
    "Tokyo": "Asia/Tokyo",
}

REGION_COLORS = {
    "global": 0xFF4655,
    "americas": 0xE05818,
    "emea": 0xD0F818,
    "pacific": 0x00D0D0,
    "china": 0xF82058,
}

MEMORY_FILE = "posted_matches.json"

def load_memory():
    if not os.path.exists(MEMORY_FILE):
        return {}

    with open(MEMORY_FILE, "r") as file:
        return json.load(file)
    
def save_memory(memory):
    with open(MEMORY_FILE, "w") as file:
        json.dump(memory, file, indent=4)

def get_schedule(memory):
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
        
        if match_url in memory:
            continue
        
        match_response = requests.get(match_url, timeout=20)
        match_response.raise_for_status()
        match_soup = BeautifulSoup(match_response.content, "html5lib")

        event_header = match_soup.select_one(".match-header-event")
        event_url = "https://www.vlr.gg" + event_header["href"]
        
        event_response = requests.get(event_url, timeout=20)
        event_response.raise_for_status()
        event_soup = BeautifulSoup(event_response.content, "html5lib")
        
        city = None
        
        for label in event_soup.select(".label"):
            if label.get_text(strip=True) == "Location":
                city = label.find_next_sibling("div").get_text(strip=True)

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
        
        local_zone = CITY_TIMEZONES.get(city)
        
        if local_zone is None:
            print(f"Unknown city: {city} — add it to CITY_TIMEZONES")
            local_time = None
        else:
            local_time = vlr_time.astimezone(ZoneInfo(local_zone))

        patch = next(
            (text for text in date_header.stripped_strings if text.startswith("Patch ")),
            None,
        )

        date_time_line = f"{match_date} • {match_time}"
        your_time_line = f"🕒 <t:{unix_time}:F> (<t:{unix_time}:R>)"

        if local_time is not None:
            local_clock = local_time.strftime("%-I:%M %p")
            date_time_line += f" ({local_clock} {city})"

        if patch is not None:
            date_time_line += f" • *{patch}*"

        embed = discord.Embed(
            title=f"{team_one} vs {team_two}",
            url=match_url,
            description="\n".join([stage_name, date_time_line, your_time_line]),
            color=REGION_COLORS[region],
        )
        
        embed.set_author(name=event_name, url=event_url)
        
        messages_by_region[region].append(embed)
        memory[match_url] = {
            "time": unix_time,
            "teams": f"{team_one} vs {team_two}",
        }
        found_count += 1

        if found_count == 4:
            break
        
    if found_count == 0:
        print("No VCT matches found.")
        
    return messages_by_region