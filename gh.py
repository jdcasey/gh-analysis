import os
import sys
import requests
import getpass
import yaml
from requests.auth import HTTPBasicAuth

TOKEN_FILE=os.path.join(os.getenv('HOME'), '.gh', 'token')
OPT_OUT_FILE=os.path.join(os.getenv('HOME'), '.gh', 'opt-out.yaml')

API_URL='https://api.github.com%s'


class GHTools(object):
    def __init__(self):
        self.headers = {'Accept': 'application/vnd.github.v3+json'}
        token_ready=False
        if os.path.exists(TOKEN_FILE):
            with open(TOKEN_FILE) as f:
                token = f.read()
                self.headers['Authorization'] = "token %s" % token
            try:
                self.do_get(API_URL % '/', "Failed to verify OAuth token")
                token_ready=True
            except:
                print "Stale token detected."

        if token_ready is False:
            user=getpass.getuser()
            password=getpass.getpass('GitHub Password: ')
            r=requests.post(API_URL % '/authorizations', auth=HTTPBasicAuth(user, password), json={'scopes': ['public_repo'], 'note': 'gh-utils python scripts'})
            if r.status_code != requests.codes.created:
                raise Exception("Failed to get OAuth token.")

            token = r.json()['token']
            self.headers['Authorization'] = "token %s" % token
            d = os.path.dirname(TOKEN_FILE)
            if not os.path.isdir(d):
                os.makedirs(d)

            with open(TOKEN_FILE, 'w') as f:
                f.write(token)

        if os.path.exists(OPT_OUT_FILE):
            with open(OPT_OUT_FILE) as f:
                self.opt_out = yaml.load(f)
        else:
            self.opt_out = {}

    def _filter_opt_out_repos(self, repos, owner):
        excluded = self.opt_out.get(owner)
        if repos is not None and excluded is not None:
            result = []
            for repo in repos:
                if str(repo['name']) not in excluded:
                    result.append(repo)
            repos = result

        return repos

    def get_user_repos(self):
        url=API_URL % ("/user/repos")
        return self._filter_opt_out_repos(self.do_get(url, "Failed to retrieve user repos.") or [], os.getenv('USER'))

    def get_org_repos(self, org):
        url=API_URL % ("/orgs/%s/repos" % org)
        return self._filter_opt_out_repos(self.do_get(url, "Failed to retrieve organization repos.") or [], org)

    def get_branches(self, owner, repo):
        url=API_URL % ("/repos/%s/%s/branches" % (owner, repo))
        return self.do_get(url, "Failed to retrieve branches of: %s owned by: %s." % (repo, owner)) or []

    def get_diff(self, repo, org_branch_data, user_branch_data):
        url=API_URL % ('/repos/%(org)s/%(repo)s/compare/%(org)s:%(org_branch)s...%(user)s:%(user_branch)s' % {
            'org': org_branch_data['owner'],
            'repo': repo,
            'org_branch': org_branch_data['branch'],
            'user': user_branch_data['owner'],
            'user_branch': user_branch_data['branch']
            })

        # print "Diff URL: %s" % url
        h = self.headers.copy()
        h['Accept'] = 'application/vnd.github.v3.diff'
        r=requests.get( url, headers=h)
        if r.status_code == requests.codes.ok:
            return r.text
        elif r.status_code == requests.codes.not_found:
            return None

        print "Failed to compare %s with %s in repo: %s. Reason: %s\nURL: %s" % (org_branch_data, user_branch_data, repo, str(r), url)
        return None

    def get_pulls(self, pulls_url):
        return self.do_get(pulls_url.replace('{/number}', ''), "Failed to retrieve pull requests.") or []

    def do_get(self, url, fail_message, headers=None):
        # print "GET %s" % url

        h = headers or self.headers
        r=requests.get( url, headers=h)
        if r.status_code == requests.codes.ok:
            return r.json()
        elif r.status_code == requests.codes.not_found:
            return None
        else:
            raise Exception(fail_message + ' ' + str(r))




