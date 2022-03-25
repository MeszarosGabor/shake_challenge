from collections import defaultdict
from datetime import datetime
from random import choices

import requests
from typing import Optional
import uvicorn
from fastapi import FastAPI

from pydantic import BaseModel


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
COOLDOWN_AFTER_LAST_CALL_IN_SEC = 5

QUERY_URL_BASE = "https://open.er-api.com/v6/latest/{}"


def _convert(curr_from, curr_to, amount):
    url = QUERY_URL_BASE.format(curr_from)
    resp = requests.get(url).json()
    unit_price = resp["rates"].get(curr_to)
    return amount * unit_price if unit_price else None


@app.get("/supported_currencies")
def supported_currencies():
    """ 
    Returns the currencies supported by the 3rd party site.
    No API KEY needed for this endpoint.
    """
    url = QUERY_URL_BASE.format("USD")
    resp = requests.get(url).json()
    return sorted(list(resp['rates'].keys()) + ['USD'])


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


@app.get("/convert/")
def convert(api_key: str, curr_from: str, curr_to: str, amount: int = 1):
    if api_key not in VALID_APIS:
        return {"Error": "Your API KEY is invalid"}
    user = API_KEY_TO_USER[api_key]
    if user.credits <= 0:
        return {"Error": "You do not have enough credits"}
    now = datetime.utcnow()
    if (now - API_KEY_TO_LAST_API_CALL[api_key]).total_seconds() < COOLDOWN_AFTER_LAST_CALL_IN_SEC:
        return {"Error": "You are being rate-limited"}

    curr_to_amount = _convert(curr_from, curr_to, amount)
    user.credits -= REQUEST_CREDIT_COST
    API_KEY_TO_LAST_API_CALL[api_key] = now
    return {
        "curr_from": curr_from,
        "curr_from_amount": amount,
        "curr_to": curr_to,
        "curr_to_amount": curr_to_amount
        }


if __name__ == "__main__":
    print('Running...')
    uvicorn.run(app)
