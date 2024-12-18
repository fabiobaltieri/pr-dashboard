#!/usr/bin/env python3

# Copyright 2024 Google LLC
# Copyright (c) 2024 The Linux Foundation
# SPDX-License-Identifier: Apache-2.0

from collections import defaultdict
from dataclasses import dataclass, field, fields
import json
import os
import sys

OUTDIR = "public"
INFILE = "cache/data_dump.json"


@dataclass
class User:
    author: set = field(default_factory=set)
    assignee: set = field(default_factory=set)
    blocking: set = field(default_factory=set)
    approved: set = field(default_factory=set)
    reviewer: set = field(default_factory=set)
    commented: set = field(default_factory=set)
    last_action: dict = field(default_factory=dict)

    def toJSON(self):
        out = {}
        for f in fields(self):
            out[f.name] = getattr(self, f.name)
        return out


@dataclass
class PR:
    title: str = None
    author: str = None
    base: str = None
    assignee_names: set = field(default_factory=set)
    reviewer_names: set = field(default_factory=set)
    assignee_approved: int = 0
    approved: int = 0
    blocked: int = 0
    created_at: str = None
    updated_at: str = None
    draft: bool = False
    mergeable: bool = True
    unknown_mergeable_status: bool = False
    needs_rebase: bool = False
    ci_passes: bool = True
    ci_pending: bool = True

    def toJSON(self):
        out = {}
        for f in fields(self):
            out[f.name] = getattr(self, f.name)
        return out


class Encoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        elif isinstance(obj, User):
            return obj.toJSON()
        elif isinstance(obj, PR):
            return obj.toJSON()
        return json.JSONEncoder.default(self, obj)


def main(argv):
    users = defaultdict(User)
    prs = {}

    with open(INFILE, "r") as infile:
        pr_dump = json.load(infile)

    for pr_data in pr_dump:
        key = f"{pr_data["repository"]["name"]}/{pr_data['number']}"
        pr = PR()
        pr.title = pr_data["title"]
        pr.author = pr_data["author"]["login"]
        pr.base = pr_data["baseRefName"]
        pr.created_at = pr_data["createdAt"]
        pr.updated_at = pr_data["updatedAt"]
        pr.draft = pr_data["isDraft"]

        pr.mergeable = pr_data["mergeable"] == "MERGEABLE"
        pr.needs_rebase = pr_data["mergeable"] == "CONFLICTING"
        pr.unknown_mergeable_status = pr_data["mergeable"] == "UNKNOWN"

        commits_nodes = pr_data["commits"]["nodes"]
        if commits_nodes:
            status_check = commits_nodes[0]["commit"]["statusCheckRollup"]
            pr.ci_passes = status_check and status_check.get("state") == "SUCCESS"
            pr.ci_pending = status_check and status_check.get("state") == "PENDING"

        users[pr.author].author.add(key)

        for assignee in pr_data["assignees"]["edges"]:
            assignee_name = assignee["node"]["login"]
            users[assignee_name].assignee.add(key)
            pr.assignee_names.add(assignee_name)

        for reviewer in pr_data["reviewRequests"]["nodes"]:
            reviewer_name = reviewer["requestedReviewer"]["login"]
            users[reviewer_name].reviewer.add(key)
            pr.reviewer_names.add(reviewer_name)

        approved = defaultdict(str)
        changes_requested = defaultdict(str)
        for review in pr_data["latestOpinionatedReviews"]["nodes"]:
            state = review["state"]
            if review["author"] is None:
                continue
            reviewer_name = review["author"]["login"]
            print(f"PR {key} {reviewer_name} {state}")
            match state:
                case "COMMENTED":
                    users[reviewer_name].commented.add(key)
                    pr.reviewer_names.add(reviewer_name)
                case "APPROVED":
                    approved[reviewer_name] = review
                case "CHANGES_REQUESTED":
                    changes_requested[reviewer_name] = review
                case "PENDING":
                    # ignore pending reviews from the user associated to the GitHub token being used
                    pass
            users[reviewer_name].last_action[key] = review["submittedAt"]

        for comment in pr_data["comments"]["nodes"]:
            if comment["author"] is None:
                continue
            commenter_name = comment["author"]["login"]
            # TODO: it might make sense to populate the commented set with the PRs where the user
            # *only* commented, not when they also actually reviewed.
            users[commenter_name].commented.add(key)

        for reviewer_name, review in approved.items():
            users[reviewer_name].approved.add(key)
            if reviewer_name in pr.assignee_names:
                pr.assignee_approved += 1
                pr.assignee_names.remove(reviewer_name)
                pr.assignee_names.add(f"+{reviewer_name}")
            else:
                pr.approved += 1
                pr.reviewer_names.add(f"+{reviewer_name}")

        for reviewer_name, review in changes_requested.items():
            users[reviewer_name].blocking.add(key)
            if reviewer_name in pr.assignee_names:
                pr.assignee_names.remove(reviewer_name)
                pr.assignee_names.add(f"-{reviewer_name}")
            else:
                pr.reviewer_names.add(f"-{reviewer_name}")
            pr.blocked += 1

        prs[key] = pr

    for user, data in users.items():
        print(f"{user} {data}")

    print("")
    for pr, data in prs.items():
        print(f"PR {pr} {data}")

    if not os.path.exists(OUTDIR):
        os.mkdir(OUTDIR)

    with open(f"{OUTDIR}/users.json", "w") as outfile:
        json.dump(users, outfile, cls=Encoder, indent=4)

    with open(f"{OUTDIR}/prs.json", "w") as outfile:
        json.dump(prs, outfile, cls=Encoder, indent=4)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
