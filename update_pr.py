#!/usr/bin/env python3

import argparse
import json
import os
import sys
from github import Github, GithubException

from dataclasses import dataclass

token = os.environ["GITHUB_TOKEN"]

PER_PAGE = 100
DATA_FILE = "cache/data_dump.json"
BOOTSTRAP_LIMIT = 400

@dataclass
class Stats:
    new: int = 0
    cached: int = 0
    updated: int = 0

def print_rate_limit(gh, org):
    response = gh.get_organization(org)
    for header, value in response.raw_headers.items():
        if header.startswith("x-ratelimit"):
            print(f"{header}: {value}")

def repo_from_url(url):
    return url.split('/')[-3]

def fetch_pr_issues(gh, org, repos):
    query = "is:pr is:open"
    for repo in repos:
        query += f" repo:{org}/{repo}"

    print(f"Query: {query}")

    pr_issues = {}
    issues = gh.search_issues(query=query)
    for issue in issues:
        repo = repo_from_url(issue.url)
        key = f"{repo}/{issue.number}"
        pr_issues[key] = issue
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

def update_entry(entry, pr_issue):
    pr = pr_issue.as_pull_request()
    entry["pr"] = pr.raw_data
    entry["reviews"] = fetch_reviews(pr)

def parse_args(argv):
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument("-o", "--org", default="zephyrproject-rtos",
                        help="Github organisation")
    parser.add_argument("-r", "--repos", default="zephyr,segger",
                        help="Github repositories, comma separated")

    return parser.parse_args(argv)

def main(argv):
    args = parse_args(argv)

    token = os.environ.get('GITHUB_TOKEN', None)
    gh = Github(token, per_page=PER_PAGE)

    print_rate_limit(gh, args.org)

    old_data = load_old_prs()
    pr_issues = fetch_pr_issues(gh, args.org, args.repos.split(","))

    new_data = {}
    stats = Stats()
    for key, pr_issue in pr_issues.items():
        if stats.new + stats.updated > BOOTSTRAP_LIMIT:
            print("bootstrap limit hit")
            break

        new_updated_at = pr_issue.updated_at.timestamp()
        new_data[key] = {"updated_at": new_updated_at}

        if not key in old_data:
            print(f"new {key}");
            stats.new += 1
            update_entry(new_data[key], pr_issue)
            continue

        old_data_entry = old_data[key]

        old_updated_at = old_data_entry["updated_at"]
        if new_updated_at == old_updated_at:
            # print(f"cache {key}");
            stats.cached += 1
            new_data[key]["pr"] = old_data_entry["pr"]
            new_data[key]["reviews"] = old_data_entry["reviews"]
            continue

        print(f"update {key}");
        stats.updated += 1
        update_entry(new_data[key], pr_issue)

    print(stats)
    print_rate_limit(gh, args.org)

    save_new_prs(new_data)

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
