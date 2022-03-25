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
    credits: Optional[int] = 100


def generate_random_api_key():
    return ''.join(choices('abcdefg1234567890', k=12))


app = FastAPI()

USER_COLLECTION = []
VALID_APIS = set()
QUERY_URL_BASE = "https://open.er-api.com/v6/latest/{}"


def _convert(curr_from, curr_to, amount):
    url = QUERY_URL_BASE.format(curr_from)
    resp = requests.get(url).json()
    unit_price = resp["rates"].get(curr_to)
    return amount * unit_price if unit_price else None


@app.get("/get_api_key/")
def get_api_key(name: str):
    print(f"{name} is requesting api")
    k = generate_random_api_key()
    print(f"Generated key {k}")
    user = User(user_name=name, api_key=k)
    USER_COLLECTION.append(user)
    VALID_APIS.add(k)
    return user


@app.get("/convert/")
def convert(api_key: str, curr_from: str, curr_to: str, amount: int = 1):
    if api_key not in VALID_APIS:
        return {"Error": "Your API KEY is invalid"}

    curr_to_amount = _convert(curr_from, curr_to, amount)
    return {
        "curr_from": curr_from,
        "curr_from_amount": amount,
        "curr_to": curr_to,
        "curr_to_amount": curr_to_amount
        }


if __name__ == "__main__":
    print('Running...')
    uvicorn.run(app)
