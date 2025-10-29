## DM Relay Bot (romantic edition)

This Discord bot relays DMs it receives to a configured channel in your server, with a wholesome, romantic presentation suitable for women-only communities.

### Features
- Relays DMs to a specific channel you choose
- Romantic embed styling with heart/flower emojis
- Attachment support (uploads files; falls back to links)
- Optional anonymization of senders
- Optional username/avatar and presence setup for a cozy vibe

### Prerequisites
- Python 3.9+
- A Discord bot token with the Message Content Intent enabled in the Developer Portal

### Setup
1. Create and activate a virtual environment (recommended):
   ```bash
   python3 -m venv .venv && source .venv/bin/activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy the config template and edit it:
   ```bash
   cp settings.py.template settings.py
   $EDITOR settings.py
   ```
   - Set `DISCORD_TOKEN` to your bot token
   - Set `RELAY_CHANNEL_ID` to the numeric ID of the channel to receive relayed messages
   - Optionally set `ANONYMIZE_SENDER = True` to hide sender identity
   - Optionally set `APPEARANCE.avatar_path` to a romantic image (e.g., a rose/heart)
   - Optionally set `APPEARANCE.username_override` and presence fields

4. Ensure the Message Content Intent is enabled for your bot in the Discord Developer Portal.

5. Run the bot:
   ```bash
   python bot.py
   ```

### Docker
Build and run locally:
```bash
docker build -t aninbot:latest .
docker run --rm -it \
  -v "$PWD/settings.py:/app/settings.py:ro" \
  --name aninbot aninbot:latest
```

### Docker Swarm
1. Initialize Swarm if needed:
   ```bash
   docker swarm init
   ```
2. Build the image on your manager:
   ```bash
   docker build -t aninbot:latest .
   ```
3. Deploy the stack (make sure `settings.py` exists next to `aninbot.yml`):
   ```bash
   docker stack deploy -c aninbot.yml anin
   ```
4. Check logs:
   ```bash
   docker service ls
   docker service logs -f anin_aninbot
   ```

### Notes and Tips
- If avatar/username updates fail, it's likely due to Discord rate limits; try again later.
- You can restrict who gets relayed by filling `ALLOW_LIST_USER_IDS` in `settings.py`.
- The bot ignores messages from other bots and only relays DMs (not server messages).

### Privacy
Be mindful that relaying DMs shares private messages with your server moderators/team. Consider enabling anonymization and communicating this behavior clearly to your community.


