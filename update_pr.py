#!/usr/bin/env python3

import json
import os
import sys
from github import Github, GithubException

from dataclasses import dataclass

token = os.environ["GITHUB_TOKEN"]

ORG = "zephyrproject-rtos"
REPO = "zephyr"
PER_PAGE = 100
DATA_FILE = "cache/data_dump.json"
BOOTSTRAP_LIMIT = 400

pr_list_query = f"is:pr is:open repo:{ORG}/{REPO}"

@dataclass
class Stats:
    new: int = 0
    cached: int = 0
    updated: int = 0

def print_rate_limit(gh):
    response = gh.get_organization(ORG)
    for header, value in response.raw_headers.items():
        if header.startswith("x-ratelimit"):
            print(f"{header}: {value}")

def fetch_pr_issues(gh):
    pr_issues = {}
    issues = gh.search_issues(query=pr_list_query)
    for issue in issues:
        pr_issues[issue.number] = issue
    print(f"Found {len(pr_issues)} issues")
    return pr_issues

def fetch_reviews(pr):
    reviews = []
    review_data = pr.get_reviews()
    for review in review_data:
        reviews.append(review.raw_data)
    return reviews

def load_old_prs():
    print(f"Loading previous data from {DATA_FILE}")

    try:
        with open(DATA_FILE, "r") as infile:
            out = json.load(infile)
            print(f"Old data loaded: {len(out)} PRs")
            return out
    except Exception as e:
        print(f"Cannot load {DATA_FILE}: {e}, starting from empty")
        return {}

def save_new_prs(data):
    if not os.path.exists("cache"):
        os.mkdir("cache");

    with open(DATA_FILE, "w") as outfile:
        json.dump(data, outfile)

def main(argv):
    token = os.environ.get('GITHUB_TOKEN', None)
    gh = Github(token, per_page=PER_PAGE)

    print_rate_limit(gh)

    old_data = load_old_prs()
    pr_issues = fetch_pr_issues(gh)

    new_data = {}
    stats = Stats()
    for number, pr_issue in pr_issues.items():
        data = pr_issue.raw_data
        new_data[number] = {"pr_issue": data}

        if not str(number) in old_data:
            print(f"new {number}");
            stats.new += 1
            pr = pr_issues[number].as_pull_request()
            new_data[number]["pr"] = pr.raw_data
            new_data[number]["reviews"] = fetch_reviews(pr)
            continue

        old_data_entry = old_data[str(number)]

        new_updated_at = data["updated_at"]
        old_updated_at = old_data_entry["pr_issue"]["updated_at"]
        if new_updated_at == old_updated_at:
            print(f"cache {number}");
            stats.cached += 1
            new_data[number]["pr"] = old_data_entry["pr"]
            new_data[number]["reviews"] = old_data_entry["reviews"]
            continue

        print(f"update {number}");
        stats.updated += 1
        pr = pr_issues[number].as_pull_request()
        new_data[number]["pr"] = pr.raw_data
        new_data[number]["reviews"] = fetch_reviews(pr)

        if stats.new + stats.updated > BOOTSTRAP_LIMIT:
            print("bootstrap limit hit")
            break

    print(stats)
    print_rate_limit(gh)

    save_new_prs(new_data)

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
