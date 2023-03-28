import requests


login_user_id = 2  # Example login user ID
user_ids = [1, 2, 3, 4, 5]  # Example list of user IDs

del user_ids[login_user_id]

print(user_ids)

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
