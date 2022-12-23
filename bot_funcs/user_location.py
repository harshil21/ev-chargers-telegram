from telegram import Update

from telegram.ext import ContextTypes



async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """If the user sent a regular location, ask them to send a live location instead"""

    location = update.effective_message.location
    print(location)