from datetime import datetime, timedelta
from apscheduler.schedulers.background import BlockingScheduler
import requests
from requests import HTTPError

API_URL = "https://api.binance.com/api/v1/"


class BinanceFuture:
    def __init__(self):
        self.session = requests.Session()
        self.price_list = []
        self.max_hour_price_time = 0

    def get_ticker(self, symbol):
        url = f"{API_URL}ticker/price?symbol={symbol}"
        response = self.session.get(url)
        if response.status_code != 200:
            raise HTTPError(response.status_code)
        return response.json()

    def get_max_hour_price(self):
        current_timestamp = datetime.utcnow()
        min_timestamp = datetime.utcnow() - timedelta(hours=1)
        max_hour_price_list = [
            price
            for price in self.price_list
            if min_timestamp <= price["timestamp"] <= current_timestamp
        ]
        if not max_hour_price_list:
            return None
        return max(max_hour_price_list, key=lambda x: x["price"])["price"]


BinanceHandler = BinanceFuture()


def get_price(ticket: str):
    price = BinanceHandler.get_ticker(ticket)
    print(price)
    price["timestamp"] = datetime.utcnow()
    BinanceHandler.price_list.append(
        {"price": price["price"], "timestamp": price["timestamp"]}
    )
    max_hour_price = BinanceHandler.get_max_hour_price()
    dif = (
        (float(max_hour_price) - float(price["price"])) / float(price["price"])
    ) * 100.0
    if price["price"] < max_hour_price and dif >= 10:
        print(
            f'Max price is down! New price: {price["price"]}, lower for max price on {dif}%'
        )
    return price["price"]


if __name__ == "__main__":
    scheduler = BlockingScheduler({"apscheduler.job_defaults.max_instances": 2})
    scheduler.add_job(lambda: get_price("XRPUSDT"), "interval", seconds=0.5)
    scheduler.start()
