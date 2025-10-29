# Simple runtime image for aninbot
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
	PYTHONUNBUFFERED=1

WORKDIR /app

# System deps (none strictly required; keep image small)
RUN apt-get update -y && apt-get install -y --no-install-recommends \
	ca-certificates && \
	rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# App code (settings.py is intentionally excluded; mount via Swarm config)
COPY bot.py settings.py.template README.md ./

CMD ["python", "-u", "bot.py"]

