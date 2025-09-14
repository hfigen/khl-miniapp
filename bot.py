"""
Telegram bot integration for the KHL stats mini‑app.

This bot listens for the ``/start`` command and sends a message
containing a button that launches the mini‑app in a web view.  The
user must specify the ``TELEGRAM_BOT_TOKEN`` environment variable
with the token provided by BotFather and ``WEB_APP_URL`` with the
public URL of the deployed mini‑app.

Example usage:

    TELEGRAM_BOT_TOKEN=8217313889:AA... \
    WEB_APP_URL=https://example.com python -m khl_stats.bot

This will start the bot and listen for incoming messages.  When a
user sends ``/start`` to the bot, they will receive a button
opening the mini‑app at the specified URL.
"""

from __future__ import annotations

import logging
import os
from typing import Final

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes

LOGGER = logging.getLogger(__name__)


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /start command by sending the mini‑app button."""
    web_app_url: str = os.environ.get('WEB_APP_URL', '').strip()
    if not web_app_url:
        await update.message.reply_text('WEB_APP_URL is not configured on the server.')
        return
    button = InlineKeyboardButton(
        text='Открыть статистику',
        web_app=WebAppInfo(url=web_app_url)
    )
    markup = InlineKeyboardMarkup([[button]])
    await update.message.reply_text(
        'Добро пожаловать! Нажмите кнопку ниже, чтобы открыть мини‑приложение.',
        reply_markup=markup
    )


def main() -> None:
    """Run the Telegram bot."""
    logging.basicConfig(level=logging.INFO)
    token: str | None = os.environ.get('TELEGRAM_BOT_TOKEN')
    if not token:
        raise RuntimeError('TELEGRAM_BOT_TOKEN environment variable is required')
    application: Final = Application.builder().token(token).build()
    application.add_handler(CommandHandler('start', start_handler))
    LOGGER.info('Bot started and waiting for messages...')
    application.run_polling()


if __name__ == '__main__':
    main()