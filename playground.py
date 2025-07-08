import requests
import os
import json


MINECRAFT_FILE = 'minecraft_data.json'


def load_minecraft_data():
    if os.path.exists(MINECRAFT_FILE):
        with open(MINECRAFT_FILE, "r") as f:
            return json.load(f)
    return {}


def save_minecraft_data(data):
    with open(MINECRAFT_FILE, "w") as f:
        json.dump(data, f, indent=4)

def fetch_new_token():
    data = None
    with open('stories_data.json', 'r') as file:
        data = json.load(file)

    for key in data:
        data[key]['image'] = input(f'{key} URL: ')

        with open('stories_data.json', 'w') as file:
            json.dump(data, file, indent=4)

fetch_new_token()