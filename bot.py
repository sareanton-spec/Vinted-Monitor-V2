import discord
from discord.ext import commands, tasks
import os
import requests
import asyncio

# Discord-token från Render Environment Variable
TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Lagrar URL per kanal
channel_urls = {}
# Spårar annonser som redan skickats
sent_ads = {}

@bot.event
async def on_ready():
    print(f"Inloggad som {bot.user}")
    check_vinted.start()  # starta loop

# Kommandot för att sätta filter-URL i Discord
@bot.command()
async def seturl(ctx, *, url):
    channel_id = ctx.channel.id
    channel_urls[channel_id] = url
    sent_ads[channel_id] = set()  # ny lista för redan skickade annonser
    await ctx.send(f"Filter-URL satt för den här kanalen!")

# Loop som kollar Vinted
@tasks.loop(seconds=120)  # kollar var 2:e minut
async def check_vinted():
    for channel_id, url in channel_urls.items():
        try:
            response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
            response.raise_for_status()
            ads = response.json().get("items", [])

            channel = bot.get_channel(channel_id)
            if not channel:
                continue

            for ad in ads:
                ad_id = ad.get("id")
                if ad_id in sent_ads[channel_id]:
                    continue

                name = ad.get("title", "Okänt namn")
                price = ad.get("price", {}).get("amount", "Okänt pris")
                link = ad.get("url", "#")

                msg = f"Ny annons!\n**{name}**\nPris: {price}\n[Se annonsen här]({link})"

                await channel.send(msg)
                sent_ads[channel_id].add(ad_id)

                # Vänta 2 sekunder mellan meddelanden för att undvika 429
                await asyncio.sleep(2)

        except Exception as e:
            print(f"Fel vid hämtning för kanal {channel_id}: {e}")

bot.run(TOKEN)