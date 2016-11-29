#!/usr/bin/env python

import sys
import gh

if len(sys.argv) < 4:
    print "Usage: %s <repo-group-name> <tag> <tag-color-hex> [<org-name>]*" % sys.argv[0]
    exit(1)

total=0
group = sys.argv[1]
tag = sys.argv[2]
color = sys.argv[3]

tools = gh.GHTools(group=group)

if len(sys.argv) < 5:
    print "Reading org list from group: %s" % group
    orgs = tools.get_group_orgs()
else:
    orgs = sys.argv[4:]

print "Creating tag: %(tag)s with color: %(color)s" % {'tag': tag, 'color': color}

for org in orgs:
    print "Updating %s repos..." % org
    repos=tools.get_org_group_repos(org)

    for repo in repos:
        name=str(repo['name'])
        print "%(org)s/%(repo)s:" % {'org': org, 'repo': name}

        tag_details = tools.create_tag(tag, color, org, name)
