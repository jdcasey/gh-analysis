#!/usr/bin/env python

import sys
import gh

if len(sys.argv) < 3:
    print "Usage: %s <group-name> <label-name> [<org-name>]*" % sys.argv[0]
    exit(1)

total=0
group = sys.argv[1]
label = sys.argv[2]
tools = gh.GHTools(group=group)

if len(sys.argv) < 4:
    orgs = tools.get_group_orgs()
else:
    orgs = sys.argv[3:]

for org in orgs:
    print "Checking %s repos..." % org
    repos=tools.get_org_group_repos(org)

    for repo in repos:
        name=str(repo['name'])
        print "%s/%s:" % (org, name)
        
        issues = tools.get_issues(org, name, label=label, state='all')
        if len(issues) > 0:
            total += len(issues)
            for issue in issues:
                t = 'PR' if issue.get('pull_request') is not None else 'ISSUE'
                print "  - %(type)s #%(number)s: %(title)s [%(state)s]\n      URL: %(url)s" % {'number': issue['number'], 'title': issue['title'], 'state': issue['state'], 'type': t, 'url': issue['html_url']}
        else:
            print "-NONE-"

print "%s Issues found." % total
