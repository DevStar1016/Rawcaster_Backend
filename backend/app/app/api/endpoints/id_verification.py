import requests
from requests.auth import HTTPBasicAuth

# Replace these variables with your actual username and password
username = 'bpCwxSYDCuo'
password = 's7eXCWA0dOEqLuiaeqvu'

# URL you want to make a request to
url = 'https://ivs.idenfy.com/api/v2/token'
data={'clientId':"8903257051"}

# Making a GET request with Basic Auth
response = requests.post(url, json={'clientId':"1212"}, auth=HTTPBasicAuth(username, password))
print(response.content)
# Check the response
if response.status_code == 200:
    # If the request was successful (status code 200)
    print("Request successful")
    print(response.text)  # Response data
else:
    # If the request was not successful
    print("Request failed")
    print(f"Status code: {response.status_code}")
