#!/usr/bin/env python3

import json
import os
import requests
import sys
import time

from dataclasses import dataclass

token = os.environ["GITHUB_TOKEN"]

ORG="zephyrproject-rtos"
REPO="zephyr"
LIMIT=100
PR_FILE="cache/prs.json"

pr_list_url = f"https://api.github.com/repos/{ORG}/{REPO}/pulls?state=open&per_page={LIMIT}"
pr_base_url = f"https://api.github.com/repos/{ORG}/{REPO}/pulls"

headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        }

@dataclass
class Stats:
    new: int = 0
    cached: int = 0
    updated: int = 0

def print_rate_limit():
    response = requests.get("https://api.github.com/users/octocat/orgs", headers=headers)
    for header, value in response.headers.items():
        if header.startswith("X-RateLimit"):
            print(f"{header}: {value}")

def fetch_prs():
    page = 1
    prs = []

    while True:
        url = f"{pr_list_url}&page={page}"
        print(url)
        response = requests.get(url, headers=headers)
        resp_prs = response.json()
        prs.extend(resp_prs);

        if len(resp_prs) < LIMIT:
            break

        page += 1

    return prs

def fetch_reviews(number):
    page = 1
    reviews = []

    while True:
        url = f"{pr_base_url}/{number}/reviews?per_page={LIMIT}&page={page}"
        print(url)
        response = requests.get(url, headers=headers)
        resp_reviews = response.json()
        reviews.extend(resp_reviews)

        if len(resp_reviews) < LIMIT:
            break

        page += 1

        time.sleep(0.5)

    return reviews

def load_old_prs():
    try:
        with open(PR_FILE, "r") as infile:
            out = json.load(infile)
            print(f"Old data loaded: {len(out)} PRs")
            return out
    except Exception as e:
        print(f"Cannot load {PR_FILE}: {e}, starting from empty")
        return {}

def save_new_prs(data):
    if not os.path.exists("cache"):
        os.mkdir("cache");

    with open(PR_FILE, "w") as outfile:
        json.dump(data, outfile)

def fetch_new_prs():
    prs = fetch_prs()

    out = {}
    for pr in prs:
        number = pr["number"]
        out[number] = {"pr": pr}

    return out

def main(argv):
    print(f"Loading previous data from {PR_FILE}")

    old_prs = load_old_prs()

    print_rate_limit()

    print(f"Fetching all open PR summary")

    new_prs = fetch_new_prs()
    print(f"Found {len(new_prs)} open PRs, updating PR details")

    stats = Stats()
    for number, data in new_prs.items():
        if not str(number) in old_prs:
            #print(f"new {number}");
            stats.new += 1
            new_prs[number]["reviews"] = fetch_reviews(number)
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
        new_prs[number]["reviews"] = fetch_reviews(number)

    print_rate_limit()

    print(f"Done, saving to {PR_FILE} {stats}")
    save_new_prs(new_prs)

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
