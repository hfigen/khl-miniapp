# KHL Mini App

This repository contains the source code for a Telegram Mini App that displays statistics for KHL (Kontinental Hockey League) players. Users can search for a player by full name in Russian, select a season and regular season/playoffs mode, and view key statistics: games played, goals, assists, points, plus/minus and penalty minutes. The mini‑app automatically resolves duplicate surnames by showing a candidate list and is localized in Russian by default.

## Project Structure

- **app.py** – Flask backend serving both the Web App and an API for search and player stats.
- **parser.py** – Scrapes player statistics from allhockey.ru for a given season and mode.
- **bot.py** – Telegram bot that sends a web app button to open the mini‑app.
- **index.html, main.js, style.css** – Frontend of the mini‑app, built with HTML/CSS/JS using Telegram Web Apps.
- **render.yaml** – Deployment blueprint for Render.com defining a free web service and a background worker.
- **requirements.txt** – Python dependencies for both services.

## Running Locally

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Start the Flask web server:
   ```bash
   export FLASK_APP=app
   flask run --port 8000
   ```
3. In another terminal, run the bot:
   ```bash
   export TELEGRAM_BOT_TOKEN=<your bot token>
   export WEB_APP_URL=http://localhost:8000/
   python bot.py
   ```
4. Open your bot in Telegram and tap the “Открыть статистику” button to launch the mini‑app.

## Deployment on Render

The included **render.yaml** blueprint defines two free services for [Render.com](https://render.com):
- **khl‑miniapp‑web** – a web service running Gunicorn to serve the Flask app.
- **khl‑miniapp‑bot** – a background worker running the Telegram bot.

To deploy with a blueprint:

1. Push this repository to GitHub (done!).
2. Sign up or log in to Render.com.
3. Create a new **Blueprint** service and connect your GitHub repo.
4. Set environment variables for the worker service:
   - `TELEGRAM_BOT_TOKEN` – the token from BotFather.
   - `WEB_APP_URL` – the full HTTPS URL of your web service (e.g., `https://khl-miniapp-web.onrender.com/`).
5. Deploy the blueprint. Render will build and start both services for free.

After deployment, visit the bot and the mini‑app should work seamlessly.

---

This project is developed as a demo with a zero budget. Feel free to modify or extend it!
