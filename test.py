from coinbase_api_handler import CoinbaseAPI
if __name__ == "__main__":
     api = CoinbaseAPI()
     data = api.list_products(30)
     print(f"{data}")
