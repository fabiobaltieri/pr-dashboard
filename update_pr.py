#!/usr/bin/env python3

import json
import os
import requests
import time

token = os.environ['GITHUB_TOKEN']

ORG="zephyrproject-rtos"
REPO="zephyr"
LIMIT=30
OUTFILE="prs.json"

base_url = f"https://api.github.com/repos/{ORG}/{REPO}/pulls?state=open&per_page={LIMIT}"
pr_base_url = f"https://api.github.com/repos/{ORG}/{REPO}/pulls"

headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/vnd.github+json',
        }

data = {}
page = 1

while True:
    url = f"{base_url}&page={page}"
    print(url)
    response = requests.get(url, headers=headers)

    print(response.headers['X-RateLimit-Remaining'])

    prs = response.json();

    for pr in prs:
        number = pr['number']

        url = f"{pr_base_url}/{number}/reviews"
        print(url)
        response = requests.get(url, headers=headers)
        reviews = response.json();

        print(response.headers['X-RateLimit-Remaining'])
        time.sleep(0.5)

        data[number] = {'pr': pr, 'reviews': reviews}

    if len(prs) < LIMIT:
        break

    page += 1

with open(OUTFILE, 'w') as outfile:
    json.dump(data, outfile)
