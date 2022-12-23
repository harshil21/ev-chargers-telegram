import asyncio
import json
import httpx

from pathlib import Path

from api.distance_calc import distance_in_km


api_key = Path("files/api_key.txt").read_text().strip()

# Query an API to get the list of electric charging stations nearby
# for a given latitude and longitude. The chargers should be within
# 10km of the user's location.

# The API is https://maps.googleapis.com/maps/api/place/nearbysearch/json


async def query_chargers(latitude: float, longitude: float):
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
        "keyword": "EV charging station",
        "location": f"{latitude},{longitude}",
        "rankby": "distance",
        "key": api_key,
    }

    async with httpx.AsyncClient() as client:
        print("querying chargers")
        resp = await client.get(url, params=params)

    return resp.json()


async def get_chargers(latitude: float, longitude: float) -> list[dict]:
    """Check if the chargers are already stored in cache, if not, query the API."""

    cached_chargers = await check_cache(latitude, longitude)
    if len(cached_chargers) <= 5:
        chargers = await query_chargers(latitude, longitude)
        chargers_filtered = await save_chargers_to_cache(chargers)  # new chargers that are not in cache
        return chargers_filtered
    print("chargers already in cache")
    return cached_chargers


async def save_chargers_to_cache(resp: dict) -> None:
    print("saving new chargers to cache")
    filtered = []

    with Path("files/chargers.json").open("a") as f:
        for i in resp['results']:
            cache = {"name": i['name'], "lat": i['geometry']['location']['lat'], "lng": i['geometry']['location']['lng']}
            is_charger_in_cache = await check_cache(cache['lat'], cache['lng'], exact=True)
            if not is_charger_in_cache:
                json.dump(cache, f)
                f.write('\n')
                filtered.append(cache)

    return filtered


async def check_cache(latitude: float, longitude: float, exact: bool = False) -> bool | list:
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
            chargers = json.loads(line)
            cached_lat, cached_long = chargers["lat"], chargers["lng"]
            if exact:
                if cached_lat == latitude and cached_long == longitude:
                    return True
                continue
            dist_to_charger = distance_in_km((latitude, longitude), (cached_lat, cached_long))
            if dist_to_charger <= 10:  # 10km
                closest_chargers.append(chargers)

            if len(closest_chargers) >= 10:  # max of 10 chargers
                return closest_chargers
    
    if exact:
        return False

    return closest_chargers


# print(check_cache(25.3057, 55.3799))
# print(asyncio.run(query_chargers(25.3057, 55.3799)))