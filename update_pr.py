#!/usr/bin/env python3

import json
import os
import requests
import time

token = os.environ['GITHUB_TOKEN']

ORG="zephyrproject-rtos"
REPO="zephyr"
LIMIT=100
PR_FILE="prs.json"

pr_list_url = f"https://api.github.com/repos/{ORG}/{REPO}/pulls?state=open&per_page={LIMIT}"
pr_base_url = f"https://api.github.com/repos/{ORG}/{REPO}/pulls"

headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/vnd.github+json',
        }

page = 1

print(f"Loading previous data from {PR_FILE}")

try:
    with open(PR_FILE, 'r') as infile:
        old_prs = json.load(infile)
except Exception as e:
    print(f"Cannot load {PR_FILE}: {e}, starting from empty")
    old_prs = {}

print(f"Fetching all open PR summary")

new_prs = {}

def fetch_prs():
    url = f"{pr_list_url}&page={page}"
    print(url)
    response = requests.get(url, headers=headers)
    prs = response.json();

    return prs

def fetch_reviews(number):
    url = f"{pr_base_url}/{number}/reviews"
    print(url)
    response = requests.get(url, headers=headers)
    reviews = response.json();

    #print(response.headers['X-RateLimit-Remaining'])
    time.sleep(0.5)

    return reviews

while True:
    prs = fetch_prs()
    for pr in prs:
        number = pr['number']
        new_prs[number] = {'pr': pr}

    if len(prs) < LIMIT:
        break

    page += 1

print(f"Found {len(new_prs)} open PRs, updating PR details")

for number, data in new_prs.items():
    if not f"{number}" in old_prs:
        print(f"new {number}");
        reviews = fetch_reviews(number)
        new_prs[number]['reviews'] = reviews
    elif data['pr']['updated_at'] == old_prs[f"{number}"]['pr']['updated_at']:
        print(f"cache {number}");
        new_prs[number]['reviews'] = old_prs[f"{number}"]['reviews']
    else:
        print(f"update {number}");
        reviews = fetch_reviews(number)
        new_prs[number]['reviews'] = reviews

print(f"Done, saving to {PR_FILE}")

with open(PR_FILE, 'w') as outfile:
    json.dump(new_prs, outfile)
