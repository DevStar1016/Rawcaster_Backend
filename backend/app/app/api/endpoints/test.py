import requests

import json

my_json_string = '["14", "27", "32"]'
my_list = json.loads(my_json_string)

for string_number in my_list:
    integer_number = int(string_number)
    print(integer_number)

# def get_ip():
#     response = requests.get('https://api64.ipify.org?format=json').json()
#     return response["ip"]


# def get_location():
#     ip_address = get_ip()
#     response = requests.get(f'https://ipapi.co/{ip_address}/json/').json()
#     location_data = {
#         "ip": ip_address,
#         "city": response.get("city"),
#         "region": response.get("region"),
#         "country": response.get("country_name")
#     }
#     return location_data


# print(get_location())
