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

# Testing

Due to the limited timeframe (4 hours) we needed to rely on manual/CLI testing of the endpoints. Given more time, a pytest-based unit tests suite would be recommended with mocked 3rd party behavior.

Some curl-based sample queries are indicated below:


# Proposed Additional Work

 - Unit testing: pytest-based unit test suite with mocked 3rd party API. Verification of the endpoints as well as the supporting utilities.

 - Data persistence: in line with the problem statement no data persistence layer was implemented in the current solution, all containers are in-memory. On the long run, I would recommend the replacement of such containers with a Redis-based persistence layer (sorted sets containing the last query timestamps for efficient retrieval and updates).

 - Fallback-results: this feature addition would cache the latest exchange responses and would return them (with a *cached result* markup) in case the 3rd party service is temporarily unavailable.

 - Further improvements on service-reliability: try-catch and retry blocks ensuring increased success rates (DISCLAIMER: at the time of testing, the 3rd party service did not show any signs of flakiness).
