import discord
from config import DISCORD_TOKEN, SCHEDULE_CHANNEL_IDS
from vct_scheduler import get_schedule

intents = discord.Intents.default()
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

    schedule = get_schedule()
    separator = "\n\n" + "─" * 30 + "\n\n"
    
    for region, region_messages in schedule.items():
        if not region_messages:
            continue
        
        channel = client.get_channel(SCHEDULE_CHANNEL_IDS[region])
        text = separator.join(region_messages)
        await channel.send(text, suppress_embeds=True)

    print("Schedule posted!")

client.run(DISCORD_TOKEN)