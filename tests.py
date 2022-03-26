# Application Imports
from unittest import mock

# Third Party Imports
import pytest
from fastapi.testclient import TestClient

# Application Imports
import app
from models import User


################################ FIXTURES ########################
@pytest.fixture
def client():
    return TestClient(app.app)


@pytest.fixture
def invalid_user():
    user = User(user_name='test_user', api_key='abc', credits=3)
    return user


@pytest.fixture
def valid_user():
    user = User(user_name='test_user', api_key='abc', credits=3)
    app.USER_COLLECTION = [user]
    app.VALID_API_KEYS.add(user.api_key)
    app.API_KEY_TO_USER = {user.api_key: user}
    app.API_KEY_TO_LAST_API_CALLS[user.api_key] = []
    return user


################################ TESTS ###################################
def test_credits_invalid_api(client, invalid_user):
    response = client.get(f"/credits/?api_key={invalid_user.api_key}")
    assert response.status_code == 503
    assert response.json() == {'detail': 'Your API KEY is invalid'}


def test_credits_valid_api(client, valid_user):
    response = client.get(f"/credits/?api_key={valid_user.api_key}")
    assert response.status_code == 200
    assert response.json() == {'credits': 3, 'user': 'test_user'}


# TODO: this could be fixturized; needs nested fixturized tests to combine it with mock.
MOCK_3RD_PARTY_RESPONSE_GET = mock.MagicMock()
MOCK_3RD_PARTY_RESPONSE_GET_JSON = {
    "rates": {
        "HUF": {
            "rate_for_amount": 42
        }
    }
}
MOCK_3RD_PARTY_RESPONSE_GET.json = lambda: MOCK_3RD_PARTY_RESPONSE_GET_JSON


@mock.patch('app.requests.get')
def test_currency_conversion(mock_get, client, valid_user):
    mock_get.return_value = MOCK_3RD_PARTY_RESPONSE_GET
    from_, to, amount = "USD", "HUF", 1
    url = f"/convert/?api_key={valid_user.api_key}&curr_from={from_}&curr_to={to}&amount={amount}&format=json"
    response = client.get(url)
    assert response.status_code == 200
    assert response.json()["curr_to_amount"] == 42


@pytest.mark.skip(reason="To be implemented...")
def test_currency_conversion_rate_limit_hit():
    pass


@pytest.mark.skip(reason="To be implemented...")
def test_currency_conversion_invalid_api_key():
    pass


@pytest.mark.skip(reason="To be implemented...")
def test_currency_conversion_no_credit():
    pass


@pytest.mark.skip(reason="To be implemented...")
def test_historical_currency_conversion():
    pass


@pytest.mark.skip(reason="To be implemented...")
def test_credit_top_up():
    pass


@pytest.mark.skip(reason="To be implemented...")
def test_credit_top_up_negative_value():
    pass
