"""Lesson 1: connect to Discord and respond to /ping."""

import getpass
import os
import logging

import discord
from discord import app_commands
from schedule import ScheduleReader


class VCTBot(discord.Client):
    def __init__(self, server_id: int):
        # Only server information is needed, not members' message contents.
        intents = discord.Intents.none()
        intents.guilds = True
        super().__init__(intents=intents, allowed_mentions=discord.AllowedMentions.none())
        self.server = discord.Object(id=server_id)
        self.tree = app_commands.CommandTree(self)
        self.schedules = ScheduleReader()

        @self.tree.command(name="ping", description="Check whether VCT Reminder is working")
        async def ping(interaction: discord.Interaction):
            # An ephemeral reply is visible only to the person using the command.
            await interaction.response.send_message(
                "Pong! VCT Reminder is connected.\n"
                "This is our connection test. VCT reminders and results come next.",
                ephemeral=True,
            )

        @self.tree.command(name="schedule", description="See upcoming VCT matches from VLR")
        @app_commands.describe(region="Choose a VCT region or global events")
        @app_commands.choices(region=[
            app_commands.Choice(name=name.title(), value=name)
            for name in ("all", "global", "americas", "emea", "pacific", "china")
        ])
        async def schedule(interaction: discord.Interaction, region: str = "all"):
            await interaction.response.defer(ephemeral=True, thinking=True)
            try:
                embed = await self.schedules.embed(region)
                await interaction.followup.send(embed=embed, ephemeral=True)
            except (OSError, ValueError):
                logging.getLogger(__name__).exception("Could not read VLR schedule")
                await interaction.followup.send(
                    "I couldn't read VLR's schedule just now. Please try again later. "
                    "https://www.vlr.gg/matches", ephemeral=True,
                )

    async def setup_hook(self):
        # Register in your server so this first command is available quickly.
        self.tree.copy_global_to(guild=self.server)
        await self.tree.sync(guild=self.server)

    async def on_ready(self):
        print(f"Connected as {self.user}. Try /ping in your Discord server.")
        print("Keep this window open. Press Ctrl+C to stop the bot.")


def main():
    server_id = os.getenv("DISCORD_GUILD_ID") or input("Your Discord server ID: ").strip()
    if not server_id.isdecimal() or int(server_id) <= 0:
        raise SystemExit("Use the numeric Server ID, not the server name or invite link.")

    # The token is entered privately and never written to a file.
    token = os.getenv("DISCORD_BOT_TOKEN") or getpass.getpass(
        "Bot token (hidden while you paste; press Enter afterward): "
    )
    token = token.strip()
    if not token:
        raise SystemExit("A bot token is required. Run the bot again to enter it.")

    try:
        VCTBot(int(server_id)).run(token)
    except discord.LoginFailure:
        raise SystemExit("Discord rejected the token. Get a fresh token from the Bot page.") from None
    except discord.Forbidden:
        raise SystemExit(
            "Discord denied access. Check the Server ID and invite the bot with "
            "the bot and applications.commands scopes."
        ) from None


if __name__ == "__main__":
    main()
