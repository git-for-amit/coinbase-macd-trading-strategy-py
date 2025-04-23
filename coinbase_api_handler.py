import os
import requests
from datetime import datetime, timedelta, timezone
import uuid
from jwt_token_gen import get_jwt_token

class CoinbaseAPI:
    BASE_URL = "https://api.coinbase.com"
    PRODUCT_BASE_PATH = "/api/v3/brokerage/products"
    ORDER_BASE_PATH = "/api/v3/brokerage/orders"
    ORDER_HISTORICAL_BASE_PATH = f"{ORDER_BASE_PATH}/historical"

    def __init__(self):
        pass

    def _headers(self, token: str):
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

    def get_candles(self, product_id: str, start_time: int, end_time: int, granularity: str):
        path = f"{self.PRODUCT_BASE_PATH}/{product_id}/candles"
        token = get_jwt_token("GET", path)
        url = f"{self.BASE_URL}{path}"
        headers = self._headers(token)
        params = {
            "start": start_time,
            "end": end_time,
            "granularity": granularity
        }
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json().get("candles", [])

    def get_product_data(self, product_id: str):
        path = f"{self.PRODUCT_BASE_PATH}/{product_id}"
        token = get_jwt_token("GET", path)
        url = f"{self.BASE_URL}{path}"
        headers = self._headers(token)
        params = {
            "get_tradability_status": "true"
        }
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()

        price = data.get("price")
        volume_24h = data.get("volume_24h")

        if price is None or volume_24h is None:
            raise ValueError("Missing price or volume_24h in the response")

        return {
            "product_id": product_id,
            "price": float(price),
            "volume_24h": float(volume_24h)
        }

    def place_limit_buy_order(self, product_id: str, base_size: str, limit_price: str):
        path = self.ORDER_BASE_PATH
        token = get_jwt_token("POST", path)
        url = f"{self.BASE_URL}{path}"
        headers = self._headers(token)
        end_time = (datetime.now(timezone.utc) + timedelta(minutes=7)).isoformat()
        payload = {
            "client_order_id": str(uuid.uuid4()),
            "product_id": product_id,
            "side": "BUY",
            "order_configuration": {
                "limit_limit_gtd": {
                    "base_size": base_size,
                    "limit_price": limit_price,
                    "end_time": end_time,
                    "post_only": False
                }
            }
        }
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()

    def place_limit_sell_order(self, product_id: str, base_size: str, limit_price: str):
        path = self.ORDER_BASE_PATH
        token = get_jwt_token("POST", path)
        url = f"{self.BASE_URL}{path}"
        headers = self._headers(token)
        end_time = (datetime.utcnow() + timedelta(minutes=7)).isoformat("T") + "Z"
        payload = {
            "client_order_id": str(uuid.uuid4()),
            "product_id": product_id,
            "side": "SELL",
            "order_configuration": {
                "limit_limit_gtd": {
                    "base_size": base_size,
                    "limit_price": limit_price,
                    "end_time": end_time,
                    "post_only": False
                }
            }
        }
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()

    def get_order_details(self, order_id: str):
        path = f"{self.ORDER_HISTORICAL_BASE_PATH}/{order_id}"
        token = get_jwt_token("GET", path)
        url = f"{self.BASE_URL}{path}"
        headers = self._headers(token)
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        order = data.get("order")
        status = order.get("status")
        if status == 'FILLED':
            filled_size = order.get("filled_size")
            average_filled_price = order.get("average_filled_price")
        else:
            filled_size = 0.0
            average_filled_price = 0.0

        return {
            "status": status,
            "filled_size": float(filled_size),
            "average_filled_price": float(average_filled_price)
        }
