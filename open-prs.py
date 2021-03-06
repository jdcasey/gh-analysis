#!/usr/bin/env python

import sys
import gh

if len(sys.argv) < 2:
    print "Usage: %s <org-name> [<org-name>]*" % sys.argv[0]
    exit(1)

total=0
for org in sys.argv[1:]:
    print "Checking %s repos..." % org
    tools = gh.GHTools()
    repos=tools.get_org_repos(org)

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
