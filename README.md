# shake_challenge - Currency Converter

# Summary

The Currency converter implementation offers currency exchange related information exposed
on various endpoints. The users can register by requesting an api key, request historical as well as real-time exchange rates, manage their accounts (query/top-up credits) etc.
The service is powered by https://currency.getgeoapi.com/

# Endpoints

- /supported_currencies: returns a list of 3-letter abbreviations of the currencies supported by the site. No API Key is needed for this functionality.

- /get_api_key: registers a new user and provides an api key for querying.

- /convert/: executes real-time conversion

- /convert_historical/: executes historical conversion

- /credits/: returns the credits available to the user.

- /top_up_credits/: adds credits to the user's account


# Running

The implementation was created and tested under Python 3.8.5. In case you are using a different Python version, please consult the third party library documentations.

Install the dependencies indicated under requirement.txt:
$ pip3.8 install -r requirements.txt

Run the application (from the repo root) as:
$ python3.8 app.py


# Testing

Due to the limited timeframe (4 hours) we needed to mainly rely on manual/CLI testing of the endpoints. A minimal unit test coverage is provided under tests.py (with directions of additional test coverage indicated). 

Run:
$ pytest -sv tests.py

Given more time, additional pytest-based unit tests are be recommended with mocked 3rd party behavior (see test case proposals within the file).

Some curl-based sample queries are indicated below:

$ curl http://127.0.0.1:8000/get_api_key/?name=bob
{"user_name":"bob","api_key":"qp0iyz85kdva","credits":5}

$ curl http://127.0.0.1:8000/credits/?api_key=abc
{"Error":"Your API KEY is invalid"}

$ curl http://127.0.0.1:8000/top_up_credits/?api_key=qp0iyz85kdva&credit=10
{"user":"bob","credits":10}

$ curl http://127.0.0.1:8000/convert/?curr_from=USD&curr_to=HUF&amount=1&api_key=j4kll1kng6dk
{"curr_from":"USD","curr_from_amount":1,"curr_to":"HUF","curr_to_amount":"339.3739"}


# Proposed Additional Work

 - Unit testing: pytest-based unit test suite with mocked 3rd party API. Verification of the endpoints as well as the supporting utilities.

 - Data persistence: in line with the problem statement no data persistence layer was implemented in the current solution, all containers are in-memory. On the long run, I would recommend the replacement of such containers with a Redis-based persistence layer (sorted sets containing the last query timestamps for efficient retrieval and updates).

 - Fallback-results: this feature addition would cache the latest exchange responses and would return them (with a *cached result* markup) in case the 3rd party service is temporarily unavailable.

 - Further improvements on service-reliability: try-catch and retry blocks ensuring increased success rates (DISCLAIMER: at the time of testing, the 3rd party service did not show any signs of flakiness).

 - Refactoring: the real-time and historical endpoints contain duplicated code. We could merge the two endpoints into one by defaulting to real time if no historical year/month/day are provided.
