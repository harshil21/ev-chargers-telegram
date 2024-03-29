import os
import datetime as dtm
import json
import httpx
from typing import List, Union

from pathlib import Path
from telegram.ext import ContextTypes

from api.distance_calc import distance_in_km
from files.constants import (
    MAX_CHARGERS_TO_SHOW,
    MAX_DISTANCE_TO_SHOW,
    QUERY_INTERVAL,
    QUERY_AFTER_DISTANCE,
)


def get_api_key():
    token_file = Path("files/api_key.txt")  # for local testing

    if not token_file.exists():  # For replit deploy
        return os.environ.get("API_KEY")

    return token_file.read_text().strip()


# Query an API to get the list of electric charging stations nearby
# for a given latitude and longitude. The chargers should be within
# 10km of the user's location.

# The API is https://maps.googleapis.com/maps/api/place/nearbysearch/json


async def query_chargers(latitude: float, longitude: float):
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
        "keyword": "Electric Vehicle charging station",
        "location": f"{latitude},{longitude}",
        "rankby": "distance",
        "key": get_api_key(),
    }

    async with httpx.AsyncClient() as client:
        print("querying chargers")
        resp = await client.get(url, params=params)

    return resp.json()


async def get_chargers(
    latitude: float, longitude: float, context: ContextTypes.DEFAULT_TYPE
) -> List[dict]:
    """Check if the chargers are already stored in cache, if not, query the API."""

    cached_chargers = await check_cache(latitude, longitude)
    distances = [
        distance_in_km((latitude, longitude), (i["lat"], i["lng"]))
        for i in cached_chargers
    ]
    last_query = context.user_data.get("last_queried", None)

    if last_query is None:
        now = dtm.datetime.now()
        context.user_data["last_queried"] = now
        last_query = now

    # When should we query for new chargers? if all chargers are more than 7km away and the last query was more than 10 minutes ago
    if bool(
        all(distance >= QUERY_AFTER_DISTANCE for distance in distances)
        if distances
        else True
    ) and ((last_query + dtm.timedelta(minutes=QUERY_INTERVAL)) <= dtm.datetime.now()):
        chargers = await query_chargers(latitude, longitude)
        context.user_data["last_queried"] = dtm.datetime.now()
        chargers_filtered = await save_chargers_to_cache(
            chargers
        )  # new chargers that are not in cache
        return chargers_filtered

    print("chargers already in cache")
    return cached_chargers


async def save_chargers_to_cache(resp: dict) -> None:
    print("saving new chargers to cache")
    filtered = []

    with Path("files/chargers.json").open("a") as f:
        for i in resp["results"]:
            cache = {
                "name": i["name"],
                "lat": i["geometry"]["location"]["lat"],
                "lng": i["geometry"]["location"]["lng"],
            }
            is_charger_in_cache = await check_cache(
                cache["lat"], cache["lng"], exact=True
            )
            if not is_charger_in_cache:
                json.dump(cache, f)
                f.write("\n")
                filtered.append(cache)

    return filtered


async def check_cache(
    latitude: float, longitude: float, exact: bool = False
) -> Union[bool, list]:
    """Check if the chargers are already stored in cache, we check that
    by using the distance_in_km function from distance_calc.py. If the
    chargers are not within 10km, return False.

    Args:
        latitude (float): The latitude of the user's location
        longitude (float): The longitude of the user's location
        exact (bool, optional): If True, check if the exact location is in cache. Defaults to False.

    """

    closest_chargers = []

    cached_chargers = Path("files/chargers.json")
    with cached_chargers.open() as f:
        for line in f:
            charger = json.loads(line)
            cached_lat, cached_long = charger["lat"], charger["lng"]
            if exact:
                if cached_lat == latitude and cached_long == longitude:
                    return True
                continue
            dist_to_charger = distance_in_km(
                (latitude, longitude), (cached_lat, cached_long)
            )
            if dist_to_charger <= MAX_DISTANCE_TO_SHOW:  # 20km
                closest_chargers.append(charger)

            if len(closest_chargers) >= MAX_CHARGERS_TO_SHOW:  # max of 12 chargers
                return closest_chargers

    if exact:
        return False

    return closest_chargers
