import asyncio
import logging
import random
import os
import time
from typing import List, Optional

import discord

try:
	from settings import (
		DISCORD_TOKEN,
		RELAY_CHANNEL_ID,
		APPEARANCE,
		ROMANTIC_EMOJIS,
		ALLOW_LIST_USER_IDS,
		ANONYMIZE_SENDER,
	)
except Exception as exc:  # pragma: no cover - startup guard
	raise SystemExit(
		"Missing or invalid settings. Copy settings.py.template to settings.py and fill it in.\n"
		f"Underlying error: {exc}"
	)


logging.basicConfig(
	level=logging.INFO,
	format="[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("aninbot")


def _build_activity(activity_type: str, status_text: str) -> Optional[discord.Activity]:
    if not status_text:
        return None
    at = (activity_type or "listening").lower()
    if at == "playing":
        return discord.Game(name=status_text)
    if at == "listening":
        return discord.Activity(type=discord.ActivityType.listening, name=status_text)
    if at == "watching":
        return discord.Activity(type=discord.ActivityType.watching, name=status_text)
    if at == "competing":
        return discord.Activity(type=discord.ActivityType.competing, name=status_text)
    return discord.Activity(type=discord.ActivityType.listening, name=status_text)


def _activity_from_settings() -> Optional[discord.Activity]:
    activity_type = (APPEARANCE or {}).get("activity_type", "listening").lower()
    status_text = (APPEARANCE or {}).get("status_text", "Listening to love letters 💌")
    return _build_activity(activity_type, status_text)


intents = discord.Intents.default()
intents.message_content = True  # required for DM content
intents.messages = True
intents.guilds = True

bot = discord.Client(intents=intents)


async def _maybe_set_avatar_and_username():
	"""Optionally set avatar and username for a romantic, wholesome vibe.

	This is rate-limited by Discord (avatar/name changes). Failures are logged only.
	"""
	avatar_path = (APPEARANCE or {}).get("avatar_path") or ""
	username_override = (APPEARANCE or {}).get("username_override") or ""
	try:
		if username_override and bot.user and bot.user.name != username_override:
			await bot.user.edit(username=username_override)
			logger.info("Updated bot username to '%s'", username_override)
	except Exception as e:
		logger.warning("Could not update username: %s", e)
	try:
		if avatar_path and os.path.isfile(avatar_path):
			with open(avatar_path, "rb") as f:
				avatar_bytes = f.read()
			await bot.user.edit(avatar=avatar_bytes)
			logger.info("Updated bot avatar from '%s'", avatar_path)
	except Exception as e:
		logger.warning("Could not update avatar: %s", e)


@bot.event
async def on_ready():
	try:
		activity = _activity_from_settings()
		await bot.change_presence(activity=activity, status=discord.Status.online)
	except Exception as e:
		logger.warning("Presence update failed: %s", e)
	await _maybe_set_avatar_and_username()
	logger.info("Logged in as %s (%s)", bot.user, getattr(bot.user, "id", "?"))
    # Start background random presence updater if enabled
	try:
		asyncio.create_task(_presence_randomizer())
	except Exception as e:
		logger.warning("Failed to start presence randomizer: %s", e)


async def _presence_randomizer():
    """Background task to update presence at random intervals up to a max.

    Controlled by APPEARANCE config keys:
    - randomize_presence: bool
    - presence_texts: List[str]
    - presence_min_seconds: int (default 3600)
    - presence_max_seconds: int (default 21600)
    - activity_types: Optional[List[str]]
    """
    cfg = APPEARANCE or {}
    if not cfg.get("randomize_presence"):
        return
    try:
        min_s = int(cfg.get("presence_min_seconds", 3600))
        max_s = int(cfg.get("presence_max_seconds", 21600))
    except Exception:
        min_s, max_s = 3600, 21600
    if max_s < min_s:
        min_s, max_s = max_s, min_s
    if min_s < 10:
        min_s = 10
    texts = cfg.get("presence_texts") or [cfg.get("status_text", "Listening to love letters 💌")]
    types = cfg.get("activity_types") or [cfg.get("activity_type", "listening")]
    while True:
        try:
            text = (random.choice(texts) or "").strip()
            act_type = (random.choice(types) or "listening").lower()
            activity = _build_activity(act_type, text or cfg.get("status_text", "Listening to love letters 💌"))
            await bot.change_presence(activity=activity)
            logger.info("Presence updated: type='%s' text='%s'", act_type, text)
        except Exception as e:
            logger.warning("Presence randomizer failed to update: %s", e)
        try:
            sleep_for = random.randint(min_s, max_s)
        except Exception:
            sleep_for = 3600
        await asyncio.sleep(sleep_for)


async def _send_with_attachments(channel: discord.abc.Messageable, *, content: Optional[str], embed: Optional[discord.Embed], attachments: List[discord.Attachment]):
	files = []
	failed = []
	for att in attachments:
		try:
			files.append(await att.to_file())
		except Exception:
			failed.append(att)
	try:
		return await channel.send(content=content or None, embed=embed, files=files if files else None)
	except Exception as e:
		logger.warning("Primary send failed (%s). Retrying without files.", e)
		msg = await channel.send(content=content or None, embed=embed)
		if failed or files:
			# Fallback: send URLs of any attachments that couldn't be uploaded
			urls = [a.url for a in failed] + [getattr(f, "url", None) for f in attachments if hasattr(f, "url")]
			urls = [u for u in urls if u]
			if urls:
				await channel.send("Attachment links:" + "\n" + "\n".join(urls))
		return msg


def _build_embed(author: discord.User, content: str, avatar_url: Optional[str]) -> discord.Embed:
	emoji = (APPEARANCE or {}).get("emoji") or (random.choice(ROMANTIC_EMOJIS) if ROMANTIC_EMOJIS else "💖")
	title = f"{emoji} New love letter received"
	desc = content.strip() if content else ""
	if len(desc) > 4000:
		desc = desc[:4000] + "\n… (truncated)"
	embed = discord.Embed(title=title, description=desc or "(no text)", color=discord.Color.from_rgb(255, 105, 180))
	if avatar_url:
		embed.set_thumbnail(url=avatar_url)
	sender_label = "Anonymous sweetheart" if ANONYMIZE_SENDER else f"{author} ({author.id})"
	embed.add_field(name="From", value=sender_label, inline=False)
	embed.set_footer(text=(random.choice(ROMANTIC_EMOJIS) if len(ROMANTIC_EMOJIS) > 1 else "🌸"))
	return embed


@bot.event
async def on_message(message: discord.Message):
	# Ignore messages from ourselves or other bots
	if message.author.bot:
		return
	# Only relay DMs
	if message.guild is not None:
		return
	# Allow-list filter if provided
	if ALLOW_LIST_USER_IDS and message.author.id not in set(ALLOW_LIST_USER_IDS):
		return
	# Load relay channel
	channel = bot.get_channel(RELAY_CHANNEL_ID)
	if channel is None:
		try:
			channel = await bot.fetch_channel(RELAY_CHANNEL_ID)
		except Exception as e:
			logger.error("Failed to fetch relay channel %s: %s", RELAY_CHANNEL_ID, e)
			return
	# Build romantic embed
	embed = _build_embed(message.author, message.content or "",
		None if ANONYMIZE_SENDER else getattr(message.author.display_avatar, "url", None))
	# Send
	await _send_with_attachments(channel, content=None, embed=embed, attachments=message.attachments)


def main() -> None:
	if not DISCORD_TOKEN or DISCORD_TOKEN == "YOUR_BOT_TOKEN_HERE":
		raise SystemExit("Please set DISCORD_TOKEN in settings.py")
	bot.run(DISCORD_TOKEN)


if __name__ == "__main__":
	random.seed(time.time())
	main()


