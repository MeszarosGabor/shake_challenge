"""
Implementation of the Currency Rate Calculator API.
"""

# Standard Library Imports
from collections import defaultdict

# Third Party Imports
import requests
import uvicorn
from fastapi import HTTPException, FastAPI

# Application Imports
from constants import THIRD_PARTY_API_KEY
from models import User
from utils import charge_bank_account,  generate_unused_api_key, update_user_stats, validate_request


app = FastAPI()


# Global Containers  - TO BE MOVED TO REDIS DB (Not within scope per problem statement)
USER_COLLECTION = []
VALID_API_KEYS = set()
API_KEY_TO_USER = {}
API_KEY_TO_LAST_API_CALLS = defaultdict(list)


# URLS
SUPPORTED_CURRENCIES_BASE = "https://api.getgeoapi.com/v2/currency/list?api_key={api_key}"
CONVERT_URL_BASE =\
    "https://api.getgeoapi.com/v2/currency/convert/?api_key={api_key}&from={from_}&to={to}&amount={amount}&format=json"
HISTORICAL_CONVERT_URL_BASE =\
    "https://api.getgeoapi.com/v2/currency/historical/{year}-{month}-{day}?api_key={api_key}&from={from_}&to={to}&amount={amount}&format=json"


@app.get("/supported_currencies/")
def supported_currencies():
    """
    Returns the currencies supported by the 3rd party site.
    No API KEY needed for this endpoint.
    """
    resp = requests.get(SUPPORTED_CURRENCIES_BASE.format(api_key=THIRD_PARTY_API_KEY)).json()
    return sorted(list(resp["currencies"]))


@app.get("/get_api_key/")
def get_api_key(name: str):
    print(f"{name} is requesting api")
    k = generate_unused_api_key(VALID_API_KEYS)
    print(f"Generated key {k}")
    user = User(user_name=name, api_key=k)
    USER_COLLECTION.append(user)
    API_KEY_TO_USER[k] = user
    return user


@app.get("/convert/")
def convert(api_key: str, curr_from: str, curr_to: str, amount: int = 1):
    """ Convert the currency based on real time exchange information """
    # Validate request with respect to API KEY, rate limiting, credits etc.
    is_valid_request, error_msg = validate_request(api_key, VALID_API_KEYS,
                                                   API_KEY_TO_LAST_API_CALLS,
                                                   API_KEY_TO_USER)
    if not is_valid_request:
        raise HTTPException(503, error_msg)
    # Collect data from 3rd party API
    url = CONVERT_URL_BASE.format(api_key=THIRD_PARTY_API_KEY, from_=curr_from, to=curr_to, amount=amount)
    resp = requests.get(url).json()
    curr_to_amount = resp["rates"].get(curr_to, {}).get('rate_for_amount')

    # Update API stats
    update_user_stats(api_key, API_KEY_TO_USER, API_KEY_TO_LAST_API_CALLS)

    return {
        "curr_from": curr_from,
        "curr_from_amount": amount,
        "curr_to": curr_to,
        "curr_to_amount": curr_to_amount
        }


@app.get("/convert_historical/")
def convert_historical(api_key: str,
                       year: str,
                       month: str,
                       day: str,
                       curr_from: str,
                       curr_to: str,
                       amount: int = 1):
    """ Convert the indicated currency based on historical data. """
    # Validate request with respect to API KEY, rate limiting, credits etc.
    is_valid_request, error_msg = validate_request(api_key, VALID_API_KEYS,
                                                   API_KEY_TO_LAST_API_CALLS,
                                                   API_KEY_TO_USER)
    if not is_valid_request:
        raise HTTPException(503, error_msg)

    # Collect data from 3rd party API
    url = HISTORICAL_CONVERT_URL_BASE.format(api_key=THIRD_PARTY_API_KEY, year=year, month=month, day=day,
                                             from_=curr_from, to=curr_to, amount=amount)
    resp = requests.get(url).json()
    curr_to_amount = resp["rates"].get(curr_to, {}).get('rate_for_amount')

    # Update API stats
    update_user_stats(api_key, API_KEY_TO_USER, API_KEY_TO_LAST_API_CALLS)

    return {
        "curr_from": curr_from,
        "curr_from_amount": amount,
        "curr_to": curr_to,
        "curr_to_amount": curr_to_amount,
        "date": f"{year}-{month}-{day}"
        }


@app.get("/credits/")
def get_credits(api_key: str):
    """ Returns the available credits of the given key's user. """
    if api_key not in VALID_API_KEYS:
        raise HTTPException(503, "Your API KEY is invalid")
    user = API_KEY_TO_USER[api_key]
    return {
        "user": user.user_name,
        "credits": user.credits
    }


@app.get("/top_up_credits/")
def top_up_credits(api_key: str, credit: int = 1):
    """ Add credits to a given user's account. """
    if api_key not in VALID_API_KEYS:
        raise HTTPException(503, "Your API KEY is invalid")
    if credit <= 0:
        raise HTTPException(503, "Must apply positive credit")
    user = API_KEY_TO_USER[api_key]
    charge_bank_account(user, credit)
    user.credits += credit
    return {
        "Result": "successful top-up",
        "user": user.user_name,
        "new credits": user.credits
    }


if __name__ == "__main__":
    print('Running...')
    uvicorn.run(app)
