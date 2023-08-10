#!/usr/bin/env python3

import json
from collections import defaultdict

INFILE="prs.json"

users = defaultdict(lambda: defaultdict(list))
prs = defaultdict(lambda: defaultdict(list))

with open(INFILE, 'r') as infile:
    pr_data = json.load(infile)

for number, data in pr_data.items():
    number = int(number)
    pr = data['pr']
    reviews = data['reviews']

    author = pr['user']['login']
    users[author]['author'].append(number)

    assignee_names = []
    assignee_approved = 0
    approved = 0
    blocked = 0

    for assignee in pr['assignees']:
        assignee_name = assignee['login']
        users[assignee_name]['assignee'].append(number)
        assignee_names.append(assignee_name)

    for reviewer in pr['requested_reviewers']:
        reviewer_name = reviewer['login']
        users[reviewer_name]['reviewer'].append(number)

    final_review = defaultdict(str)
    for review in reviews:
        reviewer_name = review['user']['login']
        state = review['state']
        final_review[reviewer_name] = state

    for reviewer_name, state in final_review.items():
        if state == 'APPROVED':
            users[reviewer_name]['approved'].append(number)
            if reviewer_name in assignee_names:
                assignee_approved += 1
            else:
                approved += 1
        elif state == 'COMMENTED':
            users[reviewer_name]['commented'].append(number)
        elif state == 'CHANGES_REQUESTED':
            users[reviewer_name]['blocking'].append(number)
            blocked += 1
        elif state == 'DISMISSED':
            users[reviewer_name]['dismissed'].append(number)
        else:
            print(f"Unkown state: f{state}")

    prs[number]['assignee_approved'] = assignee_approved
    prs[number]['approved'] = approved
    prs[number]['blocked'] = blocked
    prs[number]['updated_at'] = pr['updated_at']
    prs[number]['title'] = pr['title']

for user, data in users.items():
    print(f"")
    print(f"#### user: {user}")
    print(f"blocking {data['blocking']}")
    print(f"assignee {data['assignee']}")
    print(f"reviewer {data['reviewer']}")
    print(f"commented {data['commented']}")
    print(f"approved {data['approved']}")
    print(f"dismissed {data['dismissed']}")
    print(f"author {data['author']}")

print("")
for pr, data in prs.items():
    print("PR %d %d %d %d %s %s" % (
        pr,
        data['assignee_approved'],
        data['approved'],
        data['blocked'],
        data['title'],
        data['updated_at'],
        ))
