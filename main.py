from telegram.ext import (
    Application,
    MessageHandler,
    CommandHandler,
    filters,
    PicklePersistence,
)

import datetime as dtm
import logging
import os
from pathlib import Path

from bot_funcs.user_location import handle_location, cmd_cleanup
from bot_funcs.help import help_cmd, start_cmd
from bot_funcs.stats import get_stats, clear_stats


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


def get_token():
    token_file = Path("files/token.txt")  # for local testing

    if not token_file.exists():  # For replit deploy
        return os.environ.get("TOKEN")

    return token_file.read_text().strip()


def main():
    pp = PicklePersistence("files/data.pickle")
    app = Application.builder().token(get_token()).persistence(pp).build()

    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(MessageHandler(filters.LOCATION, handle_location))
    app.add_handler(CommandHandler("cleanup", cmd_cleanup))
    app.add_handler(CommandHandler("stats", get_stats, filters.User([476269395, 1745589926])))

    app.job_queue.run_daily(clear_stats, dtm.time(0, 0))

    app.run_polling()


if __name__ == "__main__":
    main()
