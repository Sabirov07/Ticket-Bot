import os
from dotenv import load_dotenv
import requests


class DataManager:
    def __init__(self):
        load_dotenv()
        self.header = {
            "Content-Type": "application/json",
            "Authorization": os.getenv('BEARER_TOKEN')
        }
        self.prices_data = os.getenv("SILVER_PRICES")
        self.users_data = os.getenv("SILVER_USERS")
        self.data = None
        self.response = None

    def switch_api_configuration(self, api_configs):
        for config in api_configs:
            self.prices_data = os.getenv(config["prices_env"])
            self.users_data = os.getenv(config["users_env"])
            self.response = requests.get(self.prices_data, headers=self.header)

            try:
                self.data = self.response.json()['prices']
                print(f'Data Usage: {config["api_name"]} api')
                return self.data
            except KeyError:
                print(f'KeyError encountered for {config["api_name"]} api. Switching to the next API.')

        return None

    def get_data(self):
        """Fetches data implementing exception handling"""
        api_configs = [
            {"prices_env": "SILVER_PRICES", "users_env": "SILVER_USERS", "api_name": "Silver"},
            {"prices_env": "SOFIA_PRICES", "users_env": "SOFIA_USERS", "api_name": "Sofia"},
            {"prices_env": "SAM_PRICES", "users_env": "SAM_USERS", "api_name": "Sam"}
        ]

        self.data = self.switch_api_configuration(api_configs)

        if self.data is None:
            print('All API configurations failed. Retrying with the first configuration.')
            self.data = self.switch_api_configuration(api_configs)

        if self.data is None:
            return None

        return self.data

    def register(self, first_name, last_name, city, email):
        new_user_data = {
            'user': {
                'firstName': first_name,
                'lastName': last_name,
                'interestedCity': city,
                'email': email
            }
        }

        requests.post(url=self.users_data, json=new_user_data, headers=self.header)

    def add_new_city(self, city_name, city_code):
        new_city_data = {
            'price': {
                'city': city_name,
                'iataCode': city_code
            }
        }
        requests.post(url=self.prices_data, json=new_city_data, headers=self.header)
