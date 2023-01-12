from telegram import Update
from telegram.ext import ContextTypes

from files.constants import bot_stats_str


async def get_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    stats = context.bot_data.get("live_locs", 0)

    # Get no. of users where "last_queried" is today.
    uniq_users = 0

    for k, v in context.application.user_data.items():
        if (query := v.get("last_queried", False)) and query.day == query.today().day:
            uniq_users += 1

    await update.effective_message.reply_html(
        bot_stats_str.format(
            live_locs=stats, uniq_users=uniq_users
        )
    )


async def clear_stats(context: ContextTypes.DEFAULT_TYPE) -> None:
    # Clear live_locs variable every 24h
    context.bot_data["live_locs"] = 0
