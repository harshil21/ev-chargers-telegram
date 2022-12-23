from replit import db
from telegram import Update
from telegram.ext import ContextTypes, ApplicationHandlerStop

from files.constants import auth_msg, invalid_auth_msg, success_auth_msg, already_auth_msg, fail_auth_msg



async def check_if_user_is_authenticated(update: Update, _: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in db or "is_auth" not in db[user_id] or not db[user_id]["is_auth"]:
        await update.effective_message.reply_text(auth_msg)
        raise ApplicationHandlerStop


async def authenticate_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # User already authenticated
    if user_id in db and "is_auth" in db[user_id] and db[user_id]["is_auth"]:
        await update.effective_message.reply_text(already_auth_msg)

    args = context.args

    # Invalid arguments
    if len(args) != 2:
        await update.effective_message.reply_text(invalid_auth_msg)
    
    username, password = args

    # Valid credentials
    if username == "admin" and password == "allowed":
        db[user_id] = {"is_auth": True}
        await update.effective_message.reply_text(success_auth_msg)
    
    # Invalid credentials
    else:
        await update.effective_message.reply_text(fail_auth_msg)

    raise ApplicationHandlerStop
