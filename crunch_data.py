#!/usr/bin/env python3

from collections import defaultdict
import json
import os
from dataclasses import dataclass, field, fields

OUTDIR="public"
INFILE="cache/prs.json"

@dataclass
class User:
    author: set = field(default_factory=set)
    assignee: set = field(default_factory=set)
    blocking: set = field(default_factory=set)
    approved: set = field(default_factory=set)
    reviewer: set = field(default_factory=set)
    commented: set = field(default_factory=set)
    dismissed: set = field(default_factory=set)

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
    updated_at: str = None

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

users = defaultdict(User)
prs = {}

with open(INFILE, "r") as infile:
    pr_dump = json.load(infile)

for number, data in pr_dump.items():
    number = int(number)
    pr_data = data["pr"]
    reviews = data["reviews"]

    pr = PR()
    pr.title = pr_data["title"]
    pr.author = pr_data["user"]["login"]
    pr.base = pr_data["base"]["ref"],
    pr.updated_at = pr_data["updated_at"]

    users[pr.author].author.add(number)

    for assignee in pr_data["assignees"]:
        assignee_name = assignee["login"]
        users[assignee_name].assignee.add(number)
        pr.assignee_names.add(assignee_name)

    for reviewer in pr_data["requested_reviewers"]:
        reviewer_name = reviewer["login"]
        users[reviewer_name].reviewer.add(number)
        pr.reviewer_names.add(reviewer_name)

    final_review = defaultdict(str)
    for review in reviews:
        reviewer_name = review["user"]["login"]
        state = review["state"]
        final_review[reviewer_name] = state

    for reviewer_name, state in final_review.items():
        if state == "APPROVED":
            users[reviewer_name].approved.add(number)
            if reviewer_name in pr.assignee_names:
                pr.assignee_approved += 1
                pr.assignee_names.remove(reviewer_name)
                pr.assignee_names.add(f"+{reviewer_name}")
            else:
                pr.approved += 1
                pr.reviewer_names.add(f"+{reviewer_name}")
        elif state == "COMMENTED":
            users[reviewer_name].commented.add(number)
            pr.reviewer_names.add(reviewer_name)
        elif state == "CHANGES_REQUESTED":
            users[reviewer_name].blocking.add(number)
            if reviewer_name in pr.assignee_names:
                pr.assignee_names.remove(reviewer_name)
                pr.assignee_names.add(f"-{reviewer_name}")
            else:
                pr.reviewer_names.add(f"-{reviewer_name}")
            pr.blocked += 1
        elif state == "DISMISSED":
            users[reviewer_name].dismissed.add(number)
        else:
            print(f"Unkown state: f{state}")

    prs[number] = pr

for user, data in users.items():
    print(f"{user} {data}")

print("")
for pr, data in prs.items():
    print(f"PR {pr} {data}")

if not os.path.exists(OUTDIR):
    os.mkdir(OUTDIR);

with open(f"{OUTDIR}/users.json", "w") as outfile:
    json.dump(users, outfile, cls=Encoder)

with open(f"{OUTDIR}/prs.json", "w") as outfile:
    json.dump(prs, outfile, cls=Encoder)

