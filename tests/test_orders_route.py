import os
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, "src")))

from metatrader_openapi.main import app
import metatrader_openapi.main as main_module


class DummyOrder:
    def __init__(self):
        self.calls = []

    def place_market_order(self, **kwargs):
        self.calls.append(kwargs)
        return {
            "error": False,
            "message": "mocked market order success",
            "data": {
                "symbol": kwargs["symbol"],
                "volume": kwargs["volume"],
                "type": kwargs["type"],
                "stop_loss": kwargs["stop_loss"],
                "take_profit": kwargs["take_profit"],
            },
        }


class DummyClient:
    def __init__(self):
        self.order = DummyOrder()

    def disconnect(self):
        pass


@pytest.fixture(autouse=True)
def stub_lifespan(monkeypatch):
    client = DummyClient()
    monkeypatch.setattr(main_module, "load_dotenv", lambda: None)
    monkeypatch.setattr(main_module, "init", lambda login, password, server, path=None: client)
    yield client


def test_place_market_order_api_with_sl_tp(stub_lifespan):
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/order/market",
            json={
                "symbol": "XAUUSD",
                "volume": 0.01,
                "type": "BUY",
                "stop_loss": 4600.0,
                "take_profit": 4650.0,
            },
        )

    assert response.status_code == 200, response.text
    assert response.json()["error"] is False
    assert stub_lifespan.order.calls == [
        {
            "symbol": "XAUUSD",
            "volume": 0.01,
            "type": "BUY",
            "stop_loss": 4600.0,
            "take_profit": 4650.0,
        }
    ]


def test_place_market_order_api_defaults_sl_tp(stub_lifespan):
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/order/market",
            json={
                "symbol": "XAUUSD",
                "volume": 0.01,
                "type": "BUY",
            },
        )

    assert response.status_code == 200, response.text
    assert response.json()["error"] is False
    assert stub_lifespan.order.calls == [
        {
            "symbol": "XAUUSD",
            "volume": 0.01,
            "type": "BUY",
            "stop_loss": 0.0,
            "take_profit": 0.0,
        }
    ]
