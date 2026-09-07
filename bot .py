import os
import discord
import requests
from bs4 import BeautifulSoup
from discord.ext import tasks

# =========================
# INSTELLINGEN
# =========================

TOKEN = os.getenv("DISCORD_TOKEN")

GLORY_EVENTS_CHANNEL = 1459268351112249488
FIGHT_CARD_CHANNEL = 1546274078619476149
GLORY_LIVE_CHANNEL = 1546273891536871485

# =========================
# DISCORD
# =========================

intents = discord.Intents.default()

client = discord.Client(intents=intents)


# =========================
# GLORY EVENTS OPHALEN
# =========================

def haal_event_links():
    response = requests.get(
        "https://glorykickboxing.com/events",
        timeout=15
    )

    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    links = []

    for a in soup.find_all("a", href=True):
        href = a["href"].split("#")[0]

        if href.startswith("/events/") and href != "/events":
            link = "https://glorykickboxing.com" + href

            if link not in links:
                links.append(link)

    return links


# =========================
# FIGHT CARD OPHALEN
# =========================

def haal_fight_card(event_url):
    response = requests.get(
        event_url,
        timeout=15
    )

    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    regels = [
        regel.strip()
        for regel in soup.get_text("\n").splitlines()
        if regel.strip()
    ]

    gevechten = []

    for i, regel in enumerate(regels):

        if regel.lower() == "vs":

            if i > 0 and i + 1 < len(regels):

                vechter1 = regels[i - 1]
                vechter2 = regels[i + 1]

                gevecht = f"{vechter1} vs {vechter2}"

                if gevecht not in gevechten:
                    gevechten.append(gevecht)

    return gevechten


# =========================
# BOT START
# =========================

@client.event
async def on_ready():

    print(f"Ingelogd als {client.user}")

    if not controleer_glory.is_running():
        controleer_glory.start()


# =========================
# GLORY CONTROLE
# =========================

@tasks.loop(minutes=30)
async def controleer_glory():

    try:

        print("GLORY controleren...")

        event_links = haal_event_links()

        print(
            f"GLORY gecontroleerd. "
            f"{len(event_links)} events gevonden."
        )

        if not event_links:
            print("Geen GLORY events gevonden.")
            return

        event_url = event_links[0]

        print(f"Event: {event_url}")

        fight_card = haal_fight_card(event_url)

        print(
            f"{len(fight_card)} gevechten gevonden."
        )

        if not fight_card:
            print("Geen fight card gevonden.")
            return

        kanaal = client.get_channel(FIGHT_CARD_CHANNEL)

        if kanaal is None:
            print("Fight Card kanaal niet gevonden!")
            return

        event_naam = (
            event_url
            .rstrip("/")
            .split("/")[-1]
            .replace("-", " ")
            .upper()
        )

        embed = discord.Embed(
            title=f"🥊 {event_naam} — Fight Card",
            description="\n".join(
                f"• {gevecht}"
                for gevecht in fight_card
            ),
            url=event_url
        )

        await kanaal.send(embed=embed)

        print("✅ Fight card naar Discord gestuurd!")

    except requests.exceptions.RequestException as e:

        print(
            "❌ Fout bij verbinding met GLORY:",
            e
        )

    except Exception as e:

        print(
            "❌ Onverwachte fout:",
            e
        )


# =========================
# BOT LOGIN
# =========================

if not TOKEN:
    raise RuntimeError(
        "DISCORD_TOKEN is niet ingesteld!"
    )

client.run(TOKEN)