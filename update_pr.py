#!/usr/bin/env python3

import json
import os
import requests
import time

from dataclasses import dataclass

token = os.environ["GITHUB_TOKEN"]

ORG="zephyrproject-rtos"
REPO="zephyr"
LIMIT=100
PR_FILE="prs.json"

pr_list_url = f"https://api.github.com/repos/{ORG}/{REPO}/pulls?state=open&per_page={LIMIT}"
pr_base_url = f"https://api.github.com/repos/{ORG}/{REPO}/pulls"

headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        }

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

    #print(response.headers["X-RateLimit-Remaining"])
    time.sleep(0.5)

    return reviews

@dataclass
class Stats:
    new: int = 0
    cached: int = 0
    updated: int = 0

print(f"Loading previous data from {PR_FILE}")

try:
    with open(PR_FILE, "r") as infile:
        old_prs = json.load(infile)
        print(f"Old data loaded: {len(old_prs)} PRs")
except Exception as e:
    print(f"Cannot load {PR_FILE}: {e}, starting from empty")
    old_prs = {}

print(f"Fetching all open PR summary")

new_prs = {}

page = 1
while True:
    prs = fetch_prs()
    for pr in prs:
        number = pr["number"]
        new_prs[number] = {"pr": pr}

    if len(prs) < LIMIT:
        break

    page += 1

print(f"Found {len(new_prs)} open PRs, updating PR details")

stats = Stats()

for number, data in new_prs.items():
    if not str(number) in old_prs:
        #print(f"new {number}");
        stats.new += 1
        reviews = fetch_reviews(number)
        new_prs[number]["reviews"] = reviews
        continue

    old_data = old_prs[str(number)]

    new_updated_at = data["pr"]["updated_at"]
    old_updated_at = old_data["pr"]["updated_at"]
    if new_updated_at == old_updated_at:
        #print(f"cache {number}");
        stats.cached += 1
        new_prs[number]["reviews"] = old_data["reviews"]
        continue

    #print(f"update {number}");
    stats.updated += 1
    reviews = fetch_reviews(number)
    new_prs[number]["reviews"] = reviews

print(f"Done, saving to {PR_FILE} {stats}")

with open(PR_FILE, "w") as outfile:
    json.dump(new_prs, outfile)
