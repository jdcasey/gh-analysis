#!/usr/bin/env python

import sys
import gh

if len(sys.argv) < 2:
    print "Usage: %s <org-name> [<org-name>]*" % sys.argv[0]
    exit(1)

total=0
for org in sys.argv[1:]:
	tools = gh.GHTools()
	repos=tools.get_org_repos(org)

	for repo in repos:
	    name=str(repo['name'])
	    pulls = tools.get_pulls(repo['pulls_url'])
	    if len(pulls) > 0:
	        print "%s:" % name
	        total += len(pulls)
	        for pull in pulls:
	            print "  - %s" % pull['html_url']

print "%s Pull requests found." % total
