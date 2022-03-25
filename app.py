from collections import defaultdict
from datetime import datetime
from random import choices
from string import ascii_lowercase, digits

import requests
import uvicorn
from fastapi import FastAPI
from typing import Optional
from pydantic import BaseModel

from api_key import API_KEY


app = FastAPI()

REQUEST_CREDIT_COST = 1

USER_COLLECTION = []
VALID_API_KEYS = set()
API_KEY_TO_USER = {}

API_KEY_LENGTH = 12
API_KEY_TO_LAST_API_CALL = defaultdict(list)
QPM_LIMIT = 10

# URLS
SUPPORTED_CURRENCIES_BASE = "https://api.getgeoapi.com/v2/currency/list?api_key={api_key}"
CONVERT_URL_BASE =\
    "https://api.getgeoapi.com/v2/currency/convert?api_key={api_key}&from={from_}&to={to}&amount={amount}&format=json"
HISTORICAL_CONVERT_URL_BASE =\
    "https://api.getgeoapi.com/v2/currency/historical/{year}-{month}-{day}?api_key={api_key}&from={from_}&to={to}&amount={amount}&format=json"


class User(BaseModel):
    user_name: str
    api_key: str
    credits: Optional[int] = 3


def generate_random_api_key():
    return ''.join(choices(ascii_lowercase + digits, k=API_KEY_LENGTH))

def generate_unused_api_key():
    for i in range(10 ** API_KEY_LENGTH):
        k = generate_random_api_key()
        if k not in VALID_API_KEYS:
            VALID_API_KEYS.add(k)
            return k


def validate_request(api_key):
    if api_key not in VALID_API_KEYS:
        return False, {"Error": "Your API KEY is invalid"}
    user = API_KEY_TO_USER[api_key]
    if user.credits <= 0:
        return False, {"Error": "You do not have enough credits; consider top-up!"}
    now = datetime.utcnow().timestamp()
    API_KEY_TO_LAST_API_CALL[api_key] = [t for t in API_KEY_TO_LAST_API_CALL[api_key] if now - t < 60]
    if len(API_KEY_TO_LAST_API_CALL[api_key]) >= QPM_LIMIT:
        return False, {"Error": "You are being rate-limited"}
    return True, {}


def update_user_stats(api_key):
    user = API_KEY_TO_USER[api_key]
    user.credits -= REQUEST_CREDIT_COST
    API_KEY_TO_LAST_API_CALL[api_key].append(datetime.utcnow().timestamp())


############################# ENDPOINTS #########################################
@app.get("/supported_currencies/")
def supported_currencies():
    """ 
    Returns the currencies supported by the 3rd party site.
    No API KEY needed for this endpoint.
    """
    resp = requests.get(SUPPORTED_CURRENCIES_BASE.format(api_key=API_KEY)).json()
    return sorted(list(resp["currencies"]))


@app.get("/get_api_key/")
def get_api_key(name: str):
    print(f"{name} is requesting api")
    k = generate_unused_api_key()
    print(f"Generated key {k}")
    user = User(user_name=name, api_key=k)
    USER_COLLECTION.append(user)
    API_KEY_TO_USER[k] = user
    return user


@app.get("/convert/")
def convert(api_key: str, curr_from: str, curr_to: str, amount: int = 1):
    # Validate request with respect to API KEY, rate limiting, credits etc.
    is_valid_request, error_msg = validate_request(api_key)
    if not is_valid_request:
        return error_msg

    # Collect data from 3rd party API
    url = CONVERT_URL_BASE.format(api_key=API_KEY, from_=curr_from, to=curr_to, amount=amount)
    resp = requests.get(url).json()
    curr_to_amount = resp["rates"].get(curr_to, {}).get('rate_for_amount')

    # Update API stats
    update_user_stats(api_key)

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
    # Validate request with respect to API KEY, rate limiting, credits etc.
    is_valid_request, error_msg = validate_request(api_key)
    if not is_valid_request:
        return error_msg

    url = HISTORICAL_CONVERT_URL_BASE.format(api_key=API_KEY, year=year, month=month, day=day,
                                             from_=curr_from, to=curr_to, amount=amount)
    resp = requests.get(url).json()
    curr_to_amount = resp["rates"].get(curr_to, {}).get('rate_for_amount')

    update_user_stats(api_key)

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
        return {"Error": "Your API KEY is invalid"}
    user = API_KEY_TO_USER[api_key]
    return {
        "user": user.user_name,
        "credits": user.credits
    }


def charge_bank_account(user, credit):
    """ To be implemented """
    pass  # :) This is where the money is at, but implementation is out of scope.


@app.get("/top_up_credits/")
def top_up_credits(api_key: str, credit: int = 1):
    """ Add credits to a given user's account. """
    if api_key not in VALID_API_KEYS:
        return {"Error": "Your API KEY is invalid"}
    if credit <= 0:
        return {"Error": "Must apply positive credit"}
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
