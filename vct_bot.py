import discord
from config import DISCORD_TOKEN, SCHEDULE_CHANNEL_IDS
from vct_scheduler import get_schedule, load_memory, save_memory

intents = discord.Intents.default()
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

    memory = load_memory()
    schedule = get_schedule(memory)
    
    for region, region_messages in schedule.items():
        if not region_messages:
            continue
        
        channel = client.get_channel(SCHEDULE_CHANNEL_IDS[region])
        await channel.send(embeds=region_messages)
        
    save_memory(memory)
    print("Schedule posted!")

client.run(DISCORD_TOKEN)