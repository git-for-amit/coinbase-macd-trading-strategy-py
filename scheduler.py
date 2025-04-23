import time
from macd_trading_lambda import lambda_handler

def run_every_five_minutes():
    while True:
        try:
            lambda_handler(None, None)
            time.sleep(300)
        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    run_every_five_minutes()
