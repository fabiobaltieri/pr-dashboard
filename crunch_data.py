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

    assignee_names = set([])
    reviewer_names = set([])
    assignee_approved = 0
    approved = 0
    blocked = 0

    for assignee in pr['assignees']:
        assignee_name = assignee['login']
        users[assignee_name]['assignee'].append(number)
        assignee_names.add(assignee_name)

    for reviewer in pr['requested_reviewers']:
        reviewer_name = reviewer['login']
        users[reviewer_name]['reviewer'].append(number)
        reviewer_names.add(reviewer_name)

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
                assignee_names.remove(reviewer_name)
                assignee_names.add(f"+{reviewer_name}")
            else:
                approved += 1
                reviewer_names.add(f"+{reviewer_name}")
        elif state == 'COMMENTED':
            users[reviewer_name]['commented'].append(number)
        elif state == 'CHANGES_REQUESTED':
            users[reviewer_name]['blocking'].append(number)
            if reviewer_name in assignee_names:
                assignee_names.remove(reviewer_name)
                assignee_names.add(f"-{reviewer_name}")
            else:
                reviewer_names.add(f"-{reviewer_name}")
            blocked += 1
        elif state == 'DISMISSED':
            users[reviewer_name]['dismissed'].append(number)
        else:
            print(f"Unkown state: f{state}")

    prs[number]['title'] = pr['title']
    prs[number]['author'] = author
    prs[number]['base'] = pr['base']['ref']
    prs[number]['assignee_names'] = assignee_names
    prs[number]['reviewer_names'] = reviewer_names
    prs[number]['assignee_approved'] = assignee_approved
    prs[number]['approved'] = approved
    prs[number]['blocked'] = blocked
    prs[number]['updated_at'] = pr['updated_at']

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
    print("PR %d %d %d %d %s %s %s %s %s %s" % (
        pr,
        data['assignee_approved'],
        data['approved'],
        data['blocked'],
        data['title'],
        data['updated_at'],
        data['author'],
        data['base'],
        data['assignee_names'],
        data['reviewer_names'],
        ))
