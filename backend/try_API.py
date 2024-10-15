# -*- coding: utf-8 -*-
"""
Created on Tue Oct 15 08:15:22 2024

@author: Mati
"""
"""
import requests
import json
headers = {
    "Content-Type": "application/json"
}
#%% REGISTER

body = {
    "username": "federico_viera_48",
    "password": "Fuimoss88",
    "email": "federico_viera@gmail.com",
    "first_name": "Federico",
    "last_name": "Viera"
}

# Convert the body to JSON
body_json = json.dumps(body)

# Make the registration request
response = requests.post("http://127.0.0.1:8000/api/register/", headers=headers, data=body_json)

# Check if registration was successful
print(response.json())
#%% LOGIN

login_body = {
    "username": "federico_viera_48",
    "password": "Fuimoss88",
}

login_json = json.dumps(login_body)

# Make the login request
login_response = requests.post("http://127.0.0.1:8000/api/login/", headers=headers, data=login_json)

# Extract the access token from the login response
access_token = login_response.json().get("access")

# Define headers with the access token
headers_with_auth = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {access_token}"
}

# Make the request to the profile endpoint
profile_response = requests.get("http://127.0.0.1:8000/api/profile/", headers=headers_with_auth)

# Print the profile information
print(profile_response.json())

#%% CREAR

body_comm = {
    'name': 'paraguas',
    'description': 'cuidate'
    }

body_comm = json.dumps(body_comm)

response_com = requests.post("http://127.0.0.1:8000/api/create/", headers=headers_with_auth, data=body_comm)

#%%  GET

response_myp = requests.get("http://127.0.0.1:8000/api/my-products/", headers=headers_with_auth)

print(response_myp.json())

#%% Delete Product

response_del_product = requests.delete("http://127.0.0.1:8000/api/delete/", headers=headers_with_auth)
"""