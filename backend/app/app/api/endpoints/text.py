import requests


def get_ip():
    
    response = requests.get('https://api64.ipify.org?format=json').json()
    return response["ip"]

import socket

def get_location():
   
    refid = "RA"+str(1)
    return refid


print(get_location())
