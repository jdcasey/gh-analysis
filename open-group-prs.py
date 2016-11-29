#!/usr/bin/env python

import sys
import gh

if len(sys.argv) < 2:
    print "Usage: %s <group-name> [<org-name>]*" % sys.argv[0]
    exit(1)

total=0
group = sys.argv[1]
tools = gh.GHTools(group=group)

if len(sys.argv) < 3:
    orgs = tools.get_group_orgs()
else:
    orgs = sys.argv[2:]

for org in orgs:
    print "Checking %s repos..." % org
    repos=tools.get_org_group_repos(org)

    for repo in repos:
        name=str(repo['name'])
        print "%s/%s:" % (org, name)
        
        pulls = tools.get_pulls(repo['pulls_url'])
        if len(pulls) > 0:
            total += len(pulls)
            for pull in pulls:
                print "  - %s" % pull['html_url']
        else:
            print "-NONE-"

print "%s Pull requests found." % total
