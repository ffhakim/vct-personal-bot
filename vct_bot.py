import asyncio
import discord
from discord.ext import tasks
from config import DISCORD_TOKEN, SCHEDULE_CHANNEL_IDS
from vct_scheduler import get_schedule, load_memory, save_memory

intents = discord.Intents.default()
client = discord.Client(intents=intents)

@tasks.loop(minutes=30)
async def check_schedule():
    print(f"Logged in as {client.user}")

    memory = load_memory()
    schedule = await asyncio.to_thread(get_schedule, memory)
    
    for region, region_messages in schedule.items():
        if not region_messages:
            continue
        
        channel = client.get_channel(SCHEDULE_CHANNEL_IDS[region])
        for start in range(0, len(region_messages), 10):
            group = region_messages[start:start + 10]
            await channel.send(embeds=group)
        
    save_memory(memory)
    print("Checked VLR")

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

    if not check_schedule.is_running():
        check_schedule.start()

client.run(DISCORD_TOKEN)