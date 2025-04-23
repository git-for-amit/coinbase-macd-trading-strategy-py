import pandas as pd
import requests
from ta.trend import MACD
from datetime import datetime, timedelta, UTC
from jwt_token_gen import get_jwt_token

request_method = "GET"
request_path = "/api/v3/brokerage/products"

def get_macd_signals_using_candles(candles):
    if not candles:
        raise ValueError("No candle data returned from Coinbase API")

    # Format: [start, low, high, open, close, volume]
    df = pd.DataFrame(candles, columns=["start", "low", "high", "open", "close", "volume"])
    #df["start"] = pd.to_datetime(df["start"])
    df["start"] = pd.to_datetime(df["start"], unit="s")
    df.sort_values("start", inplace=True)
    df.reset_index(drop=True, inplace=True)

    df["close"] = df["close"].astype(float)

    macd = MACD(close=df["close"])
    df["macd"] = macd.macd()
    df["macd_signal"] = macd.macd_signal()

    if df["macd"].iloc[-1] > df["macd_signal"].iloc[-1] and df["macd"].iloc[-2] < df["macd_signal"].iloc[-2]:
        return "buy"
    elif df["macd"].iloc[-1] < df["macd_signal"].iloc[-1] and df["macd"].iloc[-2] > df["macd_signal"].iloc[-2]:
        return "sell"
    else:
        return "hold"

def get_macd_signals(token: str, product_id="BTC-USD", lookback_minutes=350):
    granularity = "ONE_MINUTE"  # Options: ONE_MINUTE, FIVE_MINUTE, etc.
    now = datetime.now(UTC)
    end_time = int(now.timestamp())
    start_time = int((now - timedelta(minutes=lookback_minutes)).timestamp())

    url = f"https://api.coinbase.com{request_path}/{product_id}/candles"

    headers = {
        "Authorization": f"Bearer {token}",
        'Content-Type': 'application/json'
    }

    params = {
        "start": start_time,
        "end": end_time,
        "granularity": granularity
    }

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()

    candles = response.json().get("candles", [])

    if not candles:
        raise ValueError("No candle data returned from Coinbase API")

    # Format: [start, low, high, open, close, volume]
    df = pd.DataFrame(candles, columns=["start", "low", "high", "open", "close", "volume"])
    #df["start"] = pd.to_datetime(df["start"])
    df["start"] = pd.to_datetime(df["start"], unit="s")
    df.sort_values("start", inplace=True)
    df.reset_index(drop=True, inplace=True)

    df["close"] = df["close"].astype(float)

    macd = MACD(close=df["close"])
    df["macd"] = macd.macd()
    df["macd_signal"] = macd.macd_signal()

    if df["macd"].iloc[-1] > df["macd_signal"].iloc[-1] and df["macd"].iloc[-2] < df["macd_signal"].iloc[-2]:
        return "buy"
    elif df["macd"].iloc[-1] < df["macd_signal"].iloc[-1] and df["macd"].iloc[-2] > df["macd_signal"].iloc[-2]:
        return "sell"
    else:
        return "hold"

def main():
    product_id="BTC-USD"
    jwt_token = get_jwt_token(method=request_method, path=request_path + f"/{product_id}/candles")
    signal = get_macd_signals(token=jwt_token)
    print("MACD Signal:", signal)

if __name__ == "__main__":
    main()