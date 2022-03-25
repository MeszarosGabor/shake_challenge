"""
Utils library implementing technical details and offering supporting functionalities.
"""

# Standard Library Imports
from datetime import datetime
from random import choices
from string import ascii_lowercase, digits

# Application Imports
from constants import API_KEY_LENGTH, QPM_LIMIT, REQUEST_CREDIT_COST


def generate_random_api_key():
    return ''.join(choices(ascii_lowercase + digits, k=API_KEY_LENGTH))


def generate_unused_api_key(valid_api_keys):
    for i in range(10 ** API_KEY_LENGTH):
        k = generate_random_api_key()
        if k not in valid_api_keys:
            valid_api_keys.add(k)
            return k


def validate_request(api_key,
                     valid_api_keys,
                     api_key_to_last_api_calls,
                     api_key_to_user):
    if api_key not in valid_api_keys:
        return False, {"Error": "Your API KEY is invalid"}
    user = api_key_to_user[api_key]
    if user.credits <= 0:
        return False, {"Error": "You do not have enough credits; consider top-up!"}
    now = datetime.utcnow().timestamp()
    api_key_to_last_api_calls[api_key] = [t for t in api_key_to_last_api_calls[api_key] if now - t < 60]
    if len(api_key_to_last_api_calls[api_key]) >= QPM_LIMIT:
        return False, {"Error": "You are being rate-limited"}
    return True, {}


def update_user_stats(api_key, api_key_to_user, api_key_to_last_api_calls):
    user = api_key_to_user[api_key]
    user.credits -= REQUEST_CREDIT_COST
    api_key_to_last_api_calls[api_key].append(datetime.utcnow().timestamp())

def charge_bank_account(user, credit):
    """ To be implemented """
    pass  # :) This is where the money is at, but implementation is out of scope.
