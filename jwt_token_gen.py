from coinbase import jwt_generator

from util import read_cb_key_file
import logging

logger = logging.getLogger()

if logger.hasHandlers():
    logger.setLevel(logging.INFO)
else:
    logging.basicConfig(level=logging.INFO)

API_KEY, API_SECRET = read_cb_key_file()

request_method = "GET"
request_path = "/api/v3/brokerage/products"

def get_jwt_token(method: str, path: str):
    jwt_uri = jwt_generator.format_jwt_uri(method, path)
    return jwt_generator.build_rest_jwt(jwt_uri, API_KEY, API_SECRET)

def main():
    product_id="BTC-USD"
    jwt_headers = get_jwt_token(method=request_method, path=request_path + f"/{product_id}/candles")
    print("jwt_headers:", jwt_headers)

if __name__ == "__main__":
    main()