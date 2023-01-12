from telegram.ext import (
    Application,
    MessageHandler,
    CommandHandler,
    filters,
    PicklePersistence,
)

import logging
import os
from pathlib import Path

from bot_funcs.user_location import handle_location, cmd_cleanup
from bot_funcs.help import help_cmd, start_cmd


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

    app.run_polling()


if __name__ == "__main__":
    main()
