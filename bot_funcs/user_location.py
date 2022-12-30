from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, Location
from telegram.ext import ContextTypes
from telegram.error import BadRequest

from files.constants import (
    no_static_location_msg, 
    no_chargers_near_you, 
    found_chargers_near_you,
    new_chargers_near_you,
    ended_sharing_live_loc,
    MAPS_LINK,
)
from api.chargers import get_chargers
from api.distance_calc import distance_in_km

from datetime import timedelta


async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """If the user sent a regular location, ask them to send a live location instead"""

    # If user sent a live location, there will be an attribute `live_period`. If not,
    # it's a regular location. We get a location update roughly every ~30 seconds. If the 
    # user ended their sharing, we get a last update with `horizontal_accuracy` set, but no
    # `live_period` attribute.
    location = update.effective_message.location
    user_id = update.effective_user.id
    print(location)

    # If user has sent a regular location, ask them to send a live location instead
    if not location.live_period and not location.horizontal_accuracy:
        # rare case where user actually ended live location sharing, but somehow didn't have 
        # horizontal_accuracy set
        if jobs:=context.job_queue.get_jobs_by_name(str(user_id)):
            jobs[0].schedule_removal()
            await cleanup(context)
            return 

        await update.effective_message.reply_text(no_static_location_msg)
        return

    # If user has ended sharing live location, we need to clean up
    if location.horizontal_accuracy and not location.live_period:
        # User has ended sharing live location manually
        # Remove the job so we don't run it twice
        context.job_queue.get_jobs_by_name(str(user_id))[0].schedule_removal()
        await cleanup(context)
        return

    # we add 5 seconds to the live_period, because the last update we get from Telegram
    # could come a few seconds late
    when_to_run = timedelta(seconds=location.live_period + 5) + update.effective_message.date

    # Schedule a job to run when the live location sharing ends
    if not context.job_queue.get_jobs_by_name(str(user_id)):  # Don't schedule more than one job
        print("scheduling job")
        context.job_queue.run_once(cleanup, when_to_run, user_id=user_id, name=str(user_id))

    chargers: list[dict] = await get_chargers(location.latitude, location.longitude, context)

    # If user has started new live location, we need to share the list of chargers near them
    if "list_of_chargers" not in context.user_data:
        # If there are no chargers near the user, we will alert them when we find some
        if not chargers:
            print("No chargers near you")
            # If we have already alerted the user that there are no chargers near them, don't do it again
            if not context.user_data.get("no_chargers_found", False):
                await update.effective_message.reply_text(no_chargers_near_you)
            context.user_data["no_chargers_found"] = True
            return

        markup = await generate_markup(chargers, location, context)

        msg = await update.effective_message.reply_text(
            found_chargers_near_you.format(number_of_chargers=len(chargers)), 
            reply_markup=markup
        )
        context.user_data["editing_ids"] = (msg.chat_id, msg.message_id)
        context.user_data["no_chargers_found"] = False
        return

    # Check if we have a new charger near the user, that is not already in the list
    new_chargers = [i for i in chargers if i not in context.user_data["list_of_chargers"]]

    # If there are new chargers, alert the user
    if new_chargers:
        print("New chargers found")
        await update.effective_message.reply_text(new_chargers_near_you)
        context.user_data["no_chargers_found"] = False

    all_chargers = context.user_data["list_of_chargers"] + new_chargers

    # and just update the list of chargers by editing reply markup
    markup = await generate_markup(all_chargers, location, context)
    chat_id, message_id = context.user_data["editing_ids"]
    try:
        msg = await context.bot.edit_message_reply_markup(chat_id, message_id, reply_markup=markup)
    except BadRequest:  # Message reply markup is the same
        pass
    else:
        context.user_data["no_chargers_found"] = False
        context.user_data["editing_ids"] = (msg.chat_id, msg.message_id)


async def generate_markup(chargers: list[dict], location: Location, context: ContextTypes.DEFAULT_TYPE) -> InlineKeyboardMarkup:
    """Generate inline keyboard markup for chargers"""

    # cache the distance between the user and each charger
    cached_distances = {(i["lat"], i["lng"]): distance_in_km((location.latitude, location.longitude), (i["lat"], i["lng"])) for i in chargers}
    # Drop chargers that are more than 10km away
    chargers = [i for i in chargers if cached_distances[(i["lat"], i["lng"])] <= 10]

    # Save list of new chargers, after we have dropped the ones that are too far away
    context.user_data["list_of_chargers"] = chargers
    # Sort chargers by distance
    chargers.sort(key=lambda x: cached_distances[(x["lat"], x["lng"])])
    markup = InlineKeyboardMarkup.from_column(
        [InlineKeyboardButton(
            f"{i['name']} ({round(cached_distances[(i['lat'], i['lng'])], 2)}km)",
            url=MAPS_LINK.format(lat=i['lat'], lng=i['lng'])
        )
        for i in chargers],
    )

    return markup


async def cleanup(context: ContextTypes.DEFAULT_TYPE, update: Update = None):
    context.user_data.pop("list_of_chargers", None)
    context.user_data.pop("editing_ids", None)
    context.user_data.pop("no_chargers_found", None)
    if context.job:
        await context.bot.send_message(context.job.user_id, ended_sharing_live_loc)
    else:
        await update.effective_message.reply_text(ended_sharing_live_loc)
    print("Cleaned up")


async def cmd_cleanup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await cleanup(context, update)
