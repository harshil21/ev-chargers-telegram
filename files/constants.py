# Bot commands related strings

help_msg = (
    "This bot is used to find EV chargers near you. To use this bot, you must be authenticated. "
    "Please use <code>/auth username password</code> to authenticate. Please send a live location"
    " to begin."
)


# Location related strings

no_static_location_msg = "Please send a live location instead."

no_chargers_near_you = (
    "No chargers found near you, we will alert you when we find some."
)

found_chargers_near_you = "Found {number_of_chargers} chargers near you"

new_chargers_near_you = (
    "New chargers were found near you, the list above has been updated."
)

already_sharing_live_loc = "You are already sharing your live location. Please end the previous session before starting a new one."

ended_sharing_live_loc = "You have ended sharing live location."

# Other strings

MAPS_LINK = "https://www.google.com/maps/search/?api=1&query={lat},{lng}"

MAX_CHARGERS_TO_SHOW = 12  # Max number of chargers to show in the markup

MAX_DISTANCE_TO_SHOW = 20  # km

QUERY_INTERVAL = 10  # Minutes

QUERY_AFTER_DISTANCE = 7  # km
