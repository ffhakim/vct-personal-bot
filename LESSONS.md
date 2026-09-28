# VCT Reminder — learning project

## Lesson 1: get the bot online

This starter implements `/ping` and `/schedule`. It reads VLR on request but does not send scheduled posts yet.

## Lesson 2: read VLR

The active project is now `/home/ffhakim/vct_scheduler` in Ubuntu, using
`/home/ffhakim/.venv`. The original `vct_scheduler.py` is preserved.

```bash
source ~/.venv/bin/activate
cd ~/vct_scheduler
python bot.py
```

Enter your Server ID and token privately as before. Try `/schedule`, or select a
region such as `global` or `pacific`. Replies are private during development.
The command shows up to five upcoming matches from VLR's current schedule page
and caches retrieved pages for five minutes. It excludes Challengers, Ascension,
and Game Changers. It does not yet scan event pages beyond that listing.

`schedule.py` reads HTML with BeautifulSoup and checks the source's embedded UTC
time against its displayed date, clock time, and recognized timezone abbreviation.
If they disagree or cannot be verified, the command shows a warning and source link
instead of converting an uncertain time. Verified times display in JST and each
Discord reader's local timezone. Tournament venue timezone configuration, automatic
reminders, channel routing, and results remain for later lessons.

On the first live check, VLR's displayed and embedded times disagreed. This is an
unresolved source-data issue, so those matches intentionally show a warning.

The earlier Windows setup instructions below are retained for reference.

Open PowerShell in this folder. Create a private Python environment for this project:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe bot.py
```

The environment holds this project's installed packages. `discord.py` is the package
that lets our Python code communicate with Discord. No environment activation is needed.

The bot asks for two things:

1. **Server ID:** in Discord, open User Settings > Advanced and enable Developer Mode.
   Right-click your server's icon and choose Copy Server ID. Paste that number at the prompt.
2. **Bot token:** open your application in https://discord.com/developers/applications,
   choose Bot > Reset Token, and copy the new token. Paste it into the terminal prompt.
   Nothing appears as you paste; this is intentional. Press Enter.

Do not put the token in chat, screenshots, source code, or GitHub. This starter keeps it
in memory only, so you enter it again next time. Resetting a token invalidates the old one.

When you see `Connected as ...`, enter `/ping` in a server channel and select the command
from your bot. Its private response should say `Pong! VCT Reminder is connected.`
Keep the terminal open while using the bot. Press Ctrl+C to stop it.

If the command is missing, check the server ID, the bot's membership in that server,
and that the invitation included `applications.commands`. Reopen Discord if necessary.
Members also need permission to use application commands in that channel.

## Understand the code

- `import` loads code provided by Python or an installed package.
- `VCTBot` describes our Discord connection and what it can do.
- `setup_hook` registers the slash command when the bot starts.
- `ping` runs when someone uses `/ping`.
- `on_ready` prints a message after the bot connects.
- `main` asks for settings and starts the connection.
- `async` and `await` let the bot wait for Discord without blocking other work.

First exercise: change the text `Pong! VCT Reminder is connected.`, save `bot.py`,
stop and restart the bot, and try `/ping` again.

## Agreed features for later lessons

- VCT Americas, EMEA, Pacific, China, Masters and Champions; VLR as the main source.
- Five schedule channels: `vct-global-schedules`, `vct-americas-schedules`,
  `vct-emea-schedules`, `vct-pacific-schedules`, `vct-china-schedules`.
- Five results channels with the same prefixes and the suffix `-results`.
- Masters and Champions go to global channels regardless of the teams' home regions.
- Announce newly published dates/times and subsequent changes; published is not a guarantee.
- Remind 24 hours before and one hour before each match.
- At 07:00 Asia/Tokyo, summarize remaining matches for that JST day per channel.
- Display tournament-local time using each event's verified location, JST, and a Discord
  timestamp that displays in each reader's timezone.
- Send finished scores to the corresponding results channel.
- Persist sent notifications to avoid ordinary restart duplicates.
- Start locally, learn GitHub commits, then arrange always-on hosting.

## GitHub later

A repository is the project's folder and history. A commit is a named saved checkpoint.
We have not created or uploaded a GitHub repository yet. The `.gitignore` file excludes
local environments and common secret files when we do. Never put tokens inside `bot.py`.

References: https://discordpy.readthedocs.io/en/stable/quickstart.html and
https://discordpy.readthedocs.io/en/stable/interactions/api.html
