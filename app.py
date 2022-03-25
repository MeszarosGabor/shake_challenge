from collections import defaultdict
from datetime import datetime
from random import choices

import requests
from typing import Optional
import uvicorn
from fastapi import FastAPI

from pydantic import BaseModel

from api_key import API_KEY


class Item(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    tax: Optional[float] = None


class APIKeyRequest(BaseModel):
    name: str


class User(BaseModel):
    user_name: str
    api_key: str
    credits: Optional[int] = 3


def generate_random_api_key():
    return ''.join(choices('abcdefg1234567890', k=12))


app = FastAPI()

REQUEST_CREDIT_COST = 1

USER_COLLECTION = []
VALID_APIS = set()
API_KEY_TO_USER = {}

API_KEY_TO_LAST_API_CALL = defaultdict(lambda: datetime.fromtimestamp(1))
COOLDOWN_AFTER_LAST_CALL_IN_SEC = 3

# URLS
SUPPORTED_CURRENCIES_BASE = "https://api.getgeoapi.com/v2/currency/list?api_key={api_key}"
CONVERT_URL_BASE =\
    "https://api.getgeoapi.com/v2/currency/convert?api_key={api_key}&from={from_}&to={to}&amount={amount}&format=json"
HISTORICAL_CONVERT_URL_BASE =\
    "https://api.getgeoapi.com/v2/currency/historical/{year}-{month}-{day}?api_key={api_key}&from={from_}&to={to}&amount={amount}&format=json"


def _convert(curr_from, curr_to, amount,):
    url = CONVERT_URL_BASE.format(api_key=API_KEY, from_=curr_from, to=curr_to, amount=amount)
    resp = requests.get(url).json()
    unit_price = resp["rates"].get(curr_to)
    return amount * unit_price if unit_price else None


@app.get("/supported_currencies")
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
    k = generate_random_api_key()
    print(f"Generated key {k}")
    user = User(user_name=name, api_key=k)
    USER_COLLECTION.append(user)
    API_KEY_TO_USER[k] = user
    VALID_APIS.add(k)
    return user


def validate_request(api_key):
    if api_key not in VALID_APIS:
        return False, {"Error": "Your API KEY is invalid"}
    user = API_KEY_TO_USER[api_key]
    if user.credits <= 0:
        return False, {"Error": "You do not have enough credits"}
    now = datetime.utcnow()
    if (now - API_KEY_TO_LAST_API_CALL[api_key]).total_seconds() < COOLDOWN_AFTER_LAST_CALL_IN_SEC:
        return False, {"Error": "You are being rate-limited"}
    return True, {}


def update_user_stats(api_key):
    user = API_KEY_TO_USER[api_key]
    user.credits -= REQUEST_CREDIT_COST
    API_KEY_TO_LAST_API_CALL[api_key] = datetime.utcnow()
    print(API_KEY_TO_LAST_API_CALL)


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


if __name__ == "__main__":
    print('Running...')
    uvicorn.run(app)
