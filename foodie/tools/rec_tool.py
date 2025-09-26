import requests
from dotenv import load_dotenv
from pathlib import Path
import os


load_dotenv(Path(Path(__file__).parents[1], '.env'))
brave_key = os.environ.get('BRAVE_KEY')


def search_web(location, cuisine="", top_n=5):
    queries = [
        f"top {top_n} {cuisine} restaurants in {location}"
    ]


    response = requests.get(
        "https://api.search.brave.com/res/v1/web/search",
        headers={
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "x-subscription-token": brave_key,
        },
        params={
            "q": queries,
            "count": 10,
            "result_filter": "web"
        },
    ).json()

    return response


def get_info(restaurant_name, location):
    queries = [
        f"What is street address for {restaurant_name} restaurant near {location}",
        f"What is famous / good for {restaurant_name} restaurant near {location}",
    ]


    response = requests.get(
        "https://api.search.brave.com/res/v1/web/search",
        headers={
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "x-subscription-token": brave_key,
        },
        params={
            "q": queries,
            "count": 3,
            "result_filter": "web"
        },
    ).json()

    return response
