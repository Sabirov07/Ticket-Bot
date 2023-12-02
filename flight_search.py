import os
from dotenv import load_dotenv
import requests
from datetime import datetime, timedelta
from flight_data import FlightData


load_dotenv()
TICKETS_URL = os.getenv("TICKETS_URL")
TICKETS_KEY = os.getenv("TICKETS_KEY")
FLIGHT_FROM = "WAW"

header = {
            "apikey": TICKETS_KEY,
        }

# DATE
today = datetime.now().date()
tomorrow = today + timedelta(days=1)
six_month = today.replace(month=((today.month + 5) % 12) +1, year=today.year + 1 if today.month > 6 else today.year)



class FlightSearch:

    def __init__(self):
        self.shortened_urls = {}


    def get_iata(self, city):
        params = {
            "term": city
        }
        response = requests.get(TICKETS_URL + "/locations/query", params=params, headers=header)
        code = response.json()['locations'][0]['code']
        return code

    def search_flight(self, city_code):

        print(f'Ticket searching...{city_code}')

        params = {
            "fly_from": FLIGHT_FROM,
            "fly_to": city_code,
            "date_from": tomorrow,
            "date_to": six_month,
            # "price_to": 550,
            "limit": 2,
            "max_stopovers": 1,
            # "stopover_from":"24:00",
        }

        response = requests.get(url=TICKETS_URL + "/v2/search", params=params, headers=header)
        try:
            data = response.json()['data'][:2]
        except IndexError:
            print(f"NO FLIGHTS found for {city_code}")
            return None
        flights = []
        for datas in data:
            stops = len(datas['route']) - 1
            last_index = stops
            flight_data = FlightData(
                price=datas["price"],
                origin_city=datas["route"][0]["cityFrom"],
                origin_airport=datas["route"][0]["flyFrom"],
                destination_city=datas["route"][last_index]["cityTo"],
                destination_airport=datas["route"][last_index]["flyTo"],
                out_date=datas["route"][0]["local_departure"].split("T")[0],
                deeplink=datas['deep_link'],
                stops=stops
                # return_date=data["route"][1]["local_departure"].split("T")[0]
            )
            flights.append(flight_data)

        return flights


    def shorten_url(self, original_url):
        # Create a Shortener object
        suffix = len(self.shortened_urls) + 1
        shortened_url = f"http://short.url/{suffix}"

        # Store the original and shortened URLs in the dictionary
        self.shortened_urls[shortened_url] = original_url

        return shortened_url
