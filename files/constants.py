# Authentication related strings

auth_msg = "You must be authenticated to use this bot. Please enter your credentials using " \
           "<code>/auth <username> <password></code>"

invalid_auth_msg = "Invalid credentials specified. Please use as <code>/auth username password </code>."

success_auth_msg = "You have been authenticated successfully!"

fail_auth_msg = "Wrong username or password."

already_auth_msg = "You are already authenticated."

# Bot commands related strings

help_msg = "This bot is used to find EV chargers near you. To use this bot, you must be authenticated. " \
           "Please use <code>/auth username password</code> to authenticate. Please send a live location" \
           " to begin."


# Location related strings

no_static_location_msg = "Please send a live location instead."

no_chargers_near_you = "No chargers found near you, we will alert you when we find some."

found_chargers_near_you = "Found {number_of_chargers} chargers near you"

new_chargers_near_you = "New chargers were found near you, the list above has been updated."

already_sharing_live_loc = "You are already sharing your live location. Please end the previous session before starting a new one."

ended_sharing_live_loc = "You have ended sharing live location."