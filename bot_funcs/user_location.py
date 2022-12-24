from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, Location
from telegram.ext import ContextTypes

from files.constants import (
    no_static_location_msg, 
    no_chargers_near_you, 
    found_chargers_near_you,
    new_chargers_near_you,
    already_sharing_live_loc,
    ended_sharing_live_loc,
)
from api.chargers import get_chargers
from api.distance_calc import distance_in_km

from datetime import timedelta


MAPS_LINK = "https://www.google.com/maps/search/?api=1&query={lat},{lng}"


async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """If the user sent a regular location, ask them to send a live location instead"""

    # If user sent a live location, there will be an attribute `live_period`. If not,
    # it's a regular location. We get a location update roughly every ~30 seconds. If the 
    # user ended their sharing, we get a last update with `horizontal_accuracy` set, but no
    # `live_period` attribute.
    location = update.effective_message.location
    print(location)

    # If user has sent a regular location, ask them to send a live location instead
    if not location.live_period and not location.horizontal_accuracy:
        # rare case where user actually ended live location sharing, but somehow didn't have 
        # horizontal_accuracy set
        if "list_of_chargers" in context.user_data:
            await update.effective_message.reply_text(ended_sharing_live_loc)
            await cleanup(context)
            return 

        await update.effective_message.reply_text(no_static_location_msg)
        return

    user_id = update.effective_user.id

    # Don't let the user share live location more than once, this is not possible client-side, but still
    if context.job_queue.get_jobs_by_name(user_id):
        await update.effective_message.reply_text(already_sharing_live_loc)
        return

    # If user has ended sharing live location, we need to clean up
    if location.horizontal_accuracy and not location.live_period:
        # User has ended sharing live location manually
        await update.effective_message.reply_text(ended_sharing_live_loc)
        await cleanup(context)
        return

    # we add 5 seconds to the live_period, because the last update we get from Telegram
    # could come a few seconds late
    when_to_run = timedelta(seconds=location.live_period + 5) + update.effective_message.date

    # Schedule a job to run when the live location sharing ends
    if not context.job_queue.get_jobs_by_name(str(user_id)):  # Don't schedule more than one job
        print("scheduling job")
        context.job_queue.run_once(cleanup, when_to_run, user_id=user_id, name=str(user_id))
    
    chargers: list[dict] = await get_chargers(location.latitude, location.longitude)
    number_of_chargers = len(chargers)

    # If user has started new live location, we need to share the list of chargers near them
    if "list_of_chargers" not in context.user_data:
        if not chargers:
            await update.effective_message.reply_text(no_chargers_near_you)
            return

        context.user_data["list_of_chargers"] = chargers

        markup = await generate_markup(chargers, location)

        msg = await update.effective_message.reply_text(
            found_chargers_near_you.format(number_of_chargers=number_of_chargers), 
            reply_markup=markup
        )
        context.user_data["editing_ids"] = (msg.chat_id, msg.message_id)

    else:
        # Check if we have a new charger near the user, that is not already in the list
        new_chargers = [i for i in chargers if i not in context.user_data["list_of_chargers"]]

        all_chargers = context.user_data["list_of_chargers"] + new_chargers
        # Remove any charger with distance greater than 10km
        all_chargers = [i for i in all_chargers if distance_in_km((location.latitude, location.longitude), (i["lat"], i["lng"])) <= 10]

        # Save the new list of chargers
        context.user_data["list_of_chargers"] = all_chargers

        # If there are new chargers, alert the user
        if new_chargers:
            print("New chargers found")
            await update.effective_message.reply_text(new_chargers_near_you)

        # else just update the list of chargers by editing reply markup
        markup = await generate_markup(all_chargers, location)
        chat_id, message_id = context.user_data["editing_ids"]
        if markup == update.effective_message.reply_markup:
            return
        msg = await context.bot.edit_message_reply_markup(chat_id, message_id, reply_markup=markup)
        context.user_data["editing_ids"] = (msg.chat_id, msg.message_id)


async def generate_markup(chargers: list[dict], location: Location) -> InlineKeyboardMarkup:
    """Generate inline keyboard markup for chargers"""

    # Sort chargers by distance
    chargers.sort(key=lambda x: distance_in_km((location.latitude, location.longitude), (x["lat"], x["lng"])))
    distances = [distance_in_km((location.latitude, location.longitude), (i["lat"], i["lng"])) for i in chargers]
    markup = InlineKeyboardMarkup.from_column(
        [InlineKeyboardButton(
            f"{i['name']} ({round(distances[index], 2)}km)",
            url=MAPS_LINK.format(lat=i['lat'], lng=i['lng'])
        )
        for index, i in enumerate(chargers)],
    )

    return markup


async def cleanup(context: ContextTypes.DEFAULT_TYPE):
    context.user_data.pop("list_of_chargers", None)
    context.user_data.pop("editing_ids", None)
    print("Cleaned up")


async def cmd_cleanup(_: Update, context: ContextTypes.DEFAULT_TYPE):
    await cleanup(context)
