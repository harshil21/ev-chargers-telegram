from telegram import Update
from telegram.ext import ContextTypes

from files.constants import help_msg


async def help_cmd(update: Update, _: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_html(help_msg)


async def start_cmd(update: Update, _: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_html(help_msg)

