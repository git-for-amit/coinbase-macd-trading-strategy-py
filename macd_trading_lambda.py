import os
import json
import boto3
from datetime import datetime
from macd_strategy import get_macd_signals_using_candles
from jwt_token_gen import get_jwt_token
from coinbase_api_handler import CoinbaseAPI
from datetime import datetime, timedelta, timezone
import logging

logger = logging.getLogger()

if logger.hasHandlers():
    logger.setLevel(logging.INFO)
else:
    logging.basicConfig(level=logging.INFO)

UTC = timezone.utc

# Constants
TRADE_FILENAME = "trade_record.json"
S3_BUCKET = os.getenv("S3_BUCKET")  # Set this in Lambda environment
IS_AWS = os.getenv("AWS_EXECUTION_ENV") is not None
PRODUCT_ID = "TAO-USD"
PROFIT_THRESHOLD = 0.06  # 3%
ORDER_BUFFER = 2  # $2 cheaper for buy / $2 higher for sell
LOOKBACK_MINUTES = 350
GRANULARITY = "ONE_MINUTE" 

def load_trade_record():
    if IS_AWS:
        s3 = boto3.client("s3")
        try:
            response = s3.get_object(Bucket=S3_BUCKET, Key=TRADE_FILENAME)
            return json.loads(response["Body"].read().decode())
        except s3.exceptions.NoSuchKey:
            return {}
    else:
        if os.path.exists(TRADE_FILENAME):
            with open(TRADE_FILENAME, "r") as f:
                return json.load(f)
        return {}


def save_trade_record(record):
    if IS_AWS:
        s3 = boto3.client("s3")
        s3.put_object(
            Bucket=S3_BUCKET,
            Key=TRADE_FILENAME,
            Body=json.dumps(record)
        )
    else:
        with open(TRADE_FILENAME, "w") as f:
            json.dump(record, f)


def lambda_handler(event, context):

    api = CoinbaseAPI()

    now = datetime.now(UTC)
    end_time = int(now.timestamp())
    start_time = int((now - timedelta(minutes=LOOKBACK_MINUTES)).timestamp())

    signal = get_macd_signals_using_candles(api.get_candles(product_id=PRODUCT_ID, 
                                                            start_time=start_time,
                                                            end_time=end_time,
                                                            granularity=GRANULARITY))
    logger.info(f"MACD Signal: {signal}")

    product_data = api.get_product_data(PRODUCT_ID)
    current_price = product_data["price"]
    logger.info(f"Current Price: {current_price}")

    trade_record = load_trade_record()
    trade_state = trade_record.get(PRODUCT_ID, {})


    if trade_state.get("status") == "FILLED_BUY":
        buy_price = trade_state["avg_price"]
        filled_size = trade_state["filled_size"]
        target_price = buy_price * (1 + PROFIT_THRESHOLD)
        limit_price = target_price
        order_response = api.place_limit_sell_order(
            product_id=PRODUCT_ID,
            base_size=f"{filled_size:.4f}",
            limit_price=f"{limit_price:.2f}"
        )

        if order_response.get("success") == True:
            order_id = order_response.get("success_response").get("order_id")
            trade_state.update({
                "sell_order_id": order_id,
                "status": "PENDING_SELL",
                "sell_price": limit_price
            })
            logger.info(f"Sell order placed: {order_id} at price={limit_price}")
            trade_record[PRODUCT_ID] = trade_state
            save_trade_record(trade_record)
        else:
            logger.error(f"Error while placing the sell order {order_response}")
        return
    elif trade_state.get("status") == "PENDING_SELL":
        sell_details = api.get_order_details(trade_state["sell_order_id"])
        if sell_details["status"] == "FILLED":
            logger.info(f"Sell order filled: {sell_details}")
            trade_state = {}
            trade_record[PRODUCT_ID] = trade_state
            save_trade_record(trade_record)
        elif sell_details["status"] == "EXPIRED" or sell_details["status"] == "CANCELLED":
            buy_details = api.get_order_details(trade_state["buy_order_id"])
            if buy_details["status"] == "FILLED":
                logger.info(f"Sell order Expired or canclled: {sell_details}")
                trade_state.update({
                    "sell_order_id":  "",
                    "status": "FILLED_BUY",
                    "sell_price": 0
                })
                logger.info(f"updated trade sate in the file")
                trade_record[PRODUCT_ID] = trade_state
                save_trade_record(trade_record)
        return
    elif trade_state.get("status") == "PENDING_BUY":
        buy_details = api.get_order_details(trade_state["buy_order_id"])
        if buy_details["status"] == "FILLED":
            trade_state.update({
                "status": "FILLED_BUY",
                "filled_size": buy_details["filled_size"],
                "avg_price": buy_details["average_filled_price"]
            })
            trade_record[PRODUCT_ID] = trade_state
            save_trade_record(trade_record)
            logger.info(f"Buy order filled: size={buy_details['filled_size']} at price={buy_details['average_filled_price']}")
        elif buy_details["status"] == "EXPIRED"  or buy_details["status"] == "CANCELLED":
            trade_state = {}
            trade_record[PRODUCT_ID] = trade_state
            save_trade_record(trade_record)
            logger.info(f"Buy order expired or cancelled: {buy_details}")
        else:
            logger.info(f"Buy order Pending: {buy_details}")

        return
    elif signal == "buy":
        limit_price = current_price - ORDER_BUFFER
        usd_balance = 100
        base_size = usd_balance / limit_price

        order_response = api.place_limit_buy_order(
            product_id=PRODUCT_ID,
            base_size=f"{base_size:.4f}",
            limit_price=f"{limit_price:.2f}"
        )

        if order_response.get("success") == True:
            order_id = order_response.get("success_response").get("order_id")
            logger.info(f"Buy order placed: {order_response}")
            trade_state.update({
                "buy_order_id": order_id,
                "status": "PENDING_BUY",
                "timestamp": datetime.now(UTC).isoformat()
            })
            trade_record[PRODUCT_ID] = trade_state
            save_trade_record(trade_record)
        else:
            logger.info(f"buy order failed {order_response}")
        return
