"""Read public VLR schedules. Refuse to guess when source times disagree."""

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
import re
import time
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup
import discord


BASE = "https://www.vlr.gg"


def region_for(event):
    event = event.lower()
    if any(word in event for word in ("game changers", "challengers", "ascension")):
        return None
    if re.match(r"valorant champions \d{4}\b", event):
        return "global"
    if not re.match(r"vct\s+\d{4}\s*:", event):
        return None
    if re.search(r"\bmasters\b", event):
        return "global"
    for region in ("americas", "emea", "pacific", "china"):
        if re.search(rf"\b{region}\b", event):
            return region
    return None


@dataclass
class Match:
    title: str
    event: str
    region: str
    url: str


def parse_matches(html):
    soup = BeautifulSoup(html, "html.parser")
    rows = soup.select("a.match-item")
    if not rows:
        raise ValueError("VLR returned no recognizable match listings. Try again later.")
    matches = []
    for row in rows:
        status = row.select_one(".ml-status")
        if not status or status.get_text(strip=True).lower() != "upcoming":
            continue
        event_node = row.select_one(".match-item-event")
        teams = row.select(".match-item-vs-team-name")
        if not event_node or len(teams) != 2:
            raise ValueError("VLR's match layout changed; schedule parsing needs checking.")
        event = " ".join(event_node.find_all(string=True, recursive=False)).strip()
        event = " ".join(event.split())
        region = region_for(event)
        href = row.get("href", "")
        if region and re.match(r"^/\d+/", href):
            matches.append(Match(
                " vs ".join(t.get_text(" ", strip=True) for t in teams),
                event, region, BASE + href,
            ))
    return matches


def verified_time(html):
    soup = BeautifulSoup(html, "html.parser")
    nodes = soup.select(".match-header-date [data-utc-ts]")
    if not nodes:
        return None, "Time not confirmed on VLR."
    try:
        raw = datetime.strptime(nodes[0]["data-utc-ts"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
    except ValueError:
        return None, "Time not confirmed on VLR."
    clock_node = next((n for n in nodes if "h:mm" in n.get("data-moment-format", "")), None)
    date_node = next((n for n in nodes if "MMMM" in n.get("data-moment-format", "")), None)
    if clock_node is None or date_node is None:
        return None, "Could not cross-check VLR's time. Check the match link."
    rendered = clock_node.get_text(" ", strip=True)
    date_text = date_node.get_text(" ", strip=True)
    offsets = {"UTC": 0, "GMT": 0, "JST": 9, "KST": 9, "EDT": -4, "EST": -5,
               "PDT": -7, "PST": -8, "CEST": 2, "CET": 1, "BST": 1}
    parts = rendered.rsplit(" ", 1)
    if len(parts) != 2 or parts[1] not in offsets:
        return None, f"VLR displays {date_text}, {rendered}; timezone not verified."
    local = raw.astimezone(timezone(timedelta(hours=offsets[parts[1]])))
    try:
        expected_clock = datetime.strptime(parts[0], "%I:%M %p").time()
        expected_date = datetime.strptime(date_text + f", {local.year}", "%A, %B %d, %Y").date()
    except ValueError:
        return None, "Could not cross-check VLR's time. Check the match link."
    if local.time().replace(tzinfo=None) != expected_clock or local.date() != expected_date:
        return None, f"VLR displays {date_text}, {rendered}, but its embedded time disagrees. Check the match link."
    return raw, ""


def fetch(url):
    request = Request(url, headers={"User-Agent": "VCTReminder-learning/0.1"})
    with urlopen(request, timeout=15) as response:
        return response.read().decode("utf-8")


class ScheduleReader:
    def __init__(self):
        self.cache = {}
        self.lock = asyncio.Lock()

    async def page(self, url):
        cached = self.cache.get(url)
        if cached and time.monotonic() - cached[0] < 300:
            return cached[1]
        html = await asyncio.to_thread(fetch, url)
        self.cache[url] = (time.monotonic(), html)
        return html

    async def embed(self, region):
        # Serialize requests and reuse pages for five minutes.
        async with self.lock:
            matches = parse_matches(await self.page(BASE + "/matches"))
            matches = [m for m in matches if region == "all" or m.region == region]
            embed = discord.Embed(title=f"Upcoming VCT matches — {region.title()}",
                                  url=BASE + "/matches", color=0xFA4454)
            if not matches:
                embed.description = "No upcoming matches for this selection on VLR's current schedule page."
            for match in matches[:5]:
                try:
                    start, warning = verified_time(await self.page(match.url))
                except (OSError, ValueError):
                    start, warning = None, "Match time unavailable. Check the match link."
                if start:
                    stamp = int(start.timestamp())
                    when = (f"JST: {start.astimezone(ZoneInfo('Asia/Tokyo')):%a %d %b, %H:%M}\n"
                            f"Your local time: <t:{stamp}:F> (<t:{stamp}:R>)")
                else:
                    when = warning
                text = f"{discord.utils.escape_markdown(match.event)}\n{when}\n[Match on VLR]({match.url})"
                embed.add_field(name=match.title[:256], value=text[:1024], inline=False)
            embed.set_footer(text="Up to 5 matches • cached 5 minutes • published schedules can change")
            return embed
