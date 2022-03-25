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