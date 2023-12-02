class FlightData:
    # Class attribute to store the list of valid cities
    valid_cities = [
        "Warsaw", "Tashkent", "Vienna", "Paris", "Milan", "Rome",
        "New York", "London", "Tokyo", "Berlin", "Barcelona", "Sydney",
        "Dubai", "Los Angeles", "Amsterdam", "Seoul", "Singapore", "Istanbul",
        "Toronto", "Moscow", "Rio de Janeiro", "Cape Town", "Mumbai", "Bangkok",
        "Urgench", "Samarkand", "Osh", "Namangan", "Almaty",
        "Madrid", "Prague", "Budapest", "Hanoi", "Stockholm", "Lisbon",
        "Athens", "Cairo", "Nairobi", "Copenhagen", "Kuala Lumpur", "Helsinki",
        "Dublin", "Edinburgh", "Auckland", "Wellington", "Manila", "Lima",
        "San Francisco", "Chicago", "Toronto", "Vancouver", "Montreal", "Mexico City",
        "Buenos Aires", "São Paulo", "Lagos", "Johannesburg", "Cairo", "Riyadh",
        "Kiev", "Minsk", "Bucharest", "Warsaw", "Belfast", "Cardiff",
        "Brisbane", "Melbourne", "Perth", "Adelaide", "Auckland", "Christchurch",
        "Osaka", "Kyoto", "Beijing", "Shanghai", "Guangzhou", "Shenzhen",
        "Delhi", "Kolkata", "Chennai", "Mumbai", "Hyderabad", "Bengaluru",
        "Jakarta", "Manila", "Bangalore", "Colombo", "Male", "Dhaka",
        # Add more cities as needed
    ]

    def __init__(self, price, origin_city, origin_airport, destination_city, destination_airport, out_date, deeplink, stops):
        self.price = price
        self.origin_city = origin_city
        self.origin_airport = origin_airport
        self.destination_city = destination_city
        self.destination_airport = destination_airport
        self.out_date = out_date
        self.deeplink = deeplink
        self.stops = stops
        # self.return_date = return_date

    @classmethod
    def get_valid_cities(cls):
        return cls.valid_cities