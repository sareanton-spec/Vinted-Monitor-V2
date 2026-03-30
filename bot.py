import discord
from discord.ext import commands, tasks
import os
import requests
import asyncio

# Discord-bot token hämtas från Environment Variable på Render
TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Lagrar Vinted-URL per kanal
channel_urls = {}

# Lagrar IDs på annonser som redan skickats, så vi inte skickar samma två gånger
sent_ads = {}

@bot.event
async def on_ready():
    print(f"Inloggad som {bot.user}")
    check_vinted.start()  # startar loop som kollar Vinted

# Kommandot för att sätta URL/filter i Discord
@bot.command()
async def seturl(ctx, *, url):
    channel_id = ctx.channel.id
    channel_urls[channel_id] = url
    sent_ads[channel_id] = set()  # starta ny lista för denna kanal
    await ctx.send(f"Filter-URL satt för den här kanalen!")

# Loop som kollar Vinted var 60:e sekund
@tasks.loop(seconds=60)
async def check_vinted():
    for channel_id, url in channel_urls.items():
        try:
            response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
            response.raise_for_status()
            ads = response.json().get("items", [])  # beroende på Vinted API/struktur

            channel = bot.get_channel(channel_id)
            if not channel:
                continue

            for ad in ads:
                ad_id = ad.get("id")
                if ad_id in sent_ads[channel_id]:
                    continue  # hoppa över annonser vi redan skickat

                # Skicka meddelande till Discord
                name = ad.get("title", "Okänt namn")
                price = ad.get("price", {}).get("amount", "Okänt pris")
                link = ad.get("url", "#")

                msg = f"Ny annons!\n**{name}**\nPris: {price}\n[Se annonsen här]({link})"
                await channel.send(msg)

                # Lägg till i skickade annonser
                sent_ads[channel_id].add(ad_id)

        except Exception as e:
            print(f"Fel vid hämtning för kanal {channel_id}: {e}")

bot.run(TOKEN)