#!/usr/bin/env python

import os
import sys
import gh
import json

if len(sys.argv) > 1:
	user = sys.argv[1]
else:
	user = os.getenv('USER')

tools = gh.GHTools(user)
repos=tools.get_user_repos()

print "Looking for %s's repository branches that have fallen out of sync." % user
out_of_sync = 0
in_sync = 0
private = 0
for repo in repos:
	repo_name = str(repo['name'])
	org = repo.get('owner')
	if org is None or org['login'] == user:
		private += 1
		continue

	org_name = str(org['login'])

	my_branches = [str(b['name']) for b in tools.get_branches(user, repo_name)]
	org_branches = [str(b['name']) for b in tools.get_branches(org_name, repo_name)]

	for my_branch in my_branches:
		org_branch = my_branch
		if my_branch not in org_branches:
			org_branch = None
			for b in org_branches:
				if my_branch.startswith(b):
					org_branch = b
					break

		if org_branch is not None:
			diff = tools.get_diff(repo_name, {'owner': org_name, 'branch': org_branch}, {'owner': user, 'branch': my_branch})
			# print diff
			if diff is not None and len(diff) > 0:
				print "%s#%s" % (repo_name, my_branch)
				out_of_sync += 1
			else:
				in_sync += 1
		else:
			private += 1

print "%s repository branches are out of sync." % str(out_of_sync)
print "%s repository branches are in sync." % str(in_sync)
print "%s repository branches are private." % str(private)

