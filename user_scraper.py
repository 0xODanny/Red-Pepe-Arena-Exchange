import logging
import requests
from datetime import datetime
import json
#from dotenv import load_dotenv
import os


#load_dotenv()

BEARER = 'eyJhbGciOiJSUzUxMiIsInR5cCI6IkpXVCJ9.eyJ1c2VyIjp7ImlkIjoiYzc5MTk5NTItZDAyNC00OTNjLTgzMzgtY2FjMmEzODkyMmMxIiwidHdpdHRlcklkIjoiMTc3NTk3NTI5ODA3ODc1Mjc2OCIsInR3aXR0ZXJIYW5kbGUiOiIweFJlZFBlcGUiLCJ0d2l0dGVyTmFtZSI6IlJlZCBQZXBlIEV4Y2hhbmdlIiwidHdpdHRlclBpY3R1cmUiOiJodHRwczovL3N0YXRpYy5zdGFyc2FyZW5hLmNvbS91cGxvYWRzL2UzYzk5MGU2LWNmMWItYzg0Ni02ODI5LTE4YmIwNDFlZWEyNTE3MTM3MjU2OTcwOTcucG5nIiwiYWRkcmVzcyI6IjB4ZmUwNmI1YWU0Mjg4ZGY0NjU4NWNlZjIwNTc5ZjM1OTgzNGFiYzVjYyJ9LCJpYXQiOjE3MTcyMTE4MDQsImV4cCI6MTcyNTg1MTgwNH0.mviByQDfhABeRUXwxdKO325QyAdacjdbmBfzMamBtYlgbbRPsKwIiDIEiX8urwgwJRXb1RQl9G4V4NvFMLcvoHQ6bpNBOPAvAnC4zOB0GNQHhmUpwlfsG46MDJAR7PLbF6g1paGsvz4ASNXPYzvW0nrtqnz8zZhyJzPTyo6mXwXSMhG38LP7LmYSmsGWwyJnJqAPtAN0-VldmDroIog_LFEKaBcFWelbmPnt9_sPz28AFhYrY-M5cMG-p-Q0r5jzL89_pHXmQLALTdwlM9HZvzuZ3bNllQ0RLYEzhIMb4GPUZ4QyZVhx9r15kUafUMT7iD4raWsNF7P-HtYZnM7XDRI7IkObq7-Ph7bQ51iSh7E7re4hjAonaiEPbcxmIJr-LyOTzMivfhUIgHdsqeNnXBP36gS4tfDLFQJfh3lykExihhb3zbFpQpBxz8zTXQZBXirnbMkaZBJBn4e5rwlPyLDMRFGq6Zj29mavzhFWDNYUdSpr6q52hojmr7dx0g0GWQH0WhCK2TZQGuwn6zAj78jwJSrfaTrCuXpsopAgYlm-0XHb1d-Yp9NEDWY9rNQDy390_qZOtZgKtVxrp61KKQSoBoKGU0BVUlX0Q-7-fCCGxsfOOCr0TxFSuw0kQ7qbbfODIR2GuDZ045--W0UgewVuSsjprqfW7Cb1cclPlX4' # bearer token WITHOUT the 'Bearer ' part

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0',
    'Accept': 'application/json',
    'Accept-Language': 'en-US,en;q=0.5',
    # 'Accept-Encoding': 'gzip, deflate, br',
    'Origin': 'https://starsarena.com',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-site',
    'Authorization': f'Bearer {BEARER}',
    'Connection': 'keep-alive',
}


def get_latest_trades():
    try:
        headers = HEADERS.copy()  # Copy the headers and add Authorization dynamically
        headers['Authorization'] = f'Bearer {BEARER}'
        response = requests.get('https://api.starsarena.com/trade/recent', headers=headers, timeout=2)
        response.raise_for_status()
        trades = response.json().get('trades', [])
        # logging.info(trades)
        # logging.info(json.dumps({'message': 'Successfully retrieved trades.'}))
        return trades
    except requests.exceptions.RequestException as e:
        logging.info(f"Failed to retrieve trades: {e}")
        return []  # Return an empty list in case of an error
    except json.JSONDecodeError as e:
        # logging.info(f"Error decoding JSON: {e}")
        return []  # Return an empty list in case of a JSON decoding error


def get_latest_joiners():
    try:
        headers = HEADERS.copy()  # Copy the headers and add Authorization dynamically
        headers['Authorization'] = f'Bearer {BEARER}'
        response = requests.get('https://api.starsarena.com/user/page', headers=headers, timeout=2)
        response.raise_for_status()
        # logging.info(response.json())
        trades = response.json().get('users', [])
        return trades
    except requests.exceptions.RequestException as e:
        logging.info(f"Failed to retrieve trades: {e}")
        return []  # Return an empty list in case of an error
    except json.JSONDecodeError as e:
        # logging.info(f"Error decoding JSON: {e}")
        return []  # Return an empty list in case of a JSON decoding error

def read_json():
    with open('users.json', 'r') as openfile:
        # Reading from json file
        json_object = json.load(openfile)

    return json_object

def write_json(json_object):
    with open("users.json", "w") as outfile:
        outfile.write(json.dumps(json_object))

#print(get_latest_trades())
userJson = read_json()
if userJson != {}:
    for user in get_latest_joiners():
        userJson[user['address']] = user['twitterHandle']

    write_json(userJson)
