import os
import sys
import requests
import getpass
import yaml
import json
import logging
from requests.auth import HTTPBasicAuth

try:
    import http.client as http_client
except ImportError:
    # Python 2
    import httplib as http_client

def init_debug():
    http_client.HTTPConnection.debuglevel = 1
    
    # initialize logging
    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)

    requests_log = logging.getLogger("requests.packages.urllib3")
    requests_log.setLevel(logging.DEBUG)
    requests_log.propagate = True    

GH_HOME=os.path.join(os.getenv('HOME'), '.gh')
TOKEN_FILE=os.path.join(GH_HOME, 'token')
OPT_OUT_FILE=os.path.join(GH_HOME, 'opt-out.yaml')

API_URL='https://api.github.com%s'

#init_debug()

class GHTools(object):
    def __init__(self, user=None, group=None):
        self.user = user or os.getenv('USER')

        self.headers = {'Accept': 'application/vnd.github.v3+json'}
        self.post_headers = {'Content-Type': 'application/vnd.github.v3+json'}
        token_ready=False
        if os.path.exists(TOKEN_FILE):
            with open(TOKEN_FILE) as f:
                token = f.read()
                self.headers['Authorization'] = "token %s" % token
                self.post_headers['Authorization'] = "token %s" % token

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
            self.post_headers['Authorization'] = "token %s" % token
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

        if group is not None:
            group_path = os.path.join(GH_HOME, group + ".yaml")
            if os.path.exists(group_path):
                with open(group_path) as f:
                    self.group = yaml.load(f)
            else:
                raise Exception("No such project grouping found: %s" % group_path)
        else:
            self.group = {}

    def _filter_opt_out_repos(self, repos, owner):
        excluded = self.opt_out.get(owner)
        if repos is not None and excluded is not None:
            result = []
            for repo in repos:
                if str(repo['name']) not in excluded:
                    result.append(repo)
            repos = result

        return repos

    def _filter_group_repos(self, repos, owner):
        included = self.group.get(owner)
        if repos is not None and included is not None:
            result = []
            for repo in repos:
                if str(repo['name']) in included:
                    result.append(repo)
            repos = result

        return repos

    def get_group_orgs(self):
        return self.group.keys()

    def get_user_repos(self):
        url=API_URL % ("/user/repos")
        return self._filter_opt_out_repos(self.do_get(url, "Failed to retrieve user repos.") or [], self.user)

    def get_org_repos(self, org):
        url=API_URL % ("/orgs/%s/repos" % org)
        return self._filter_opt_out_repos(self.do_get(url, "Failed to retrieve organization repos.") or [], org)

    def get_user_group_repos(self):
        url=API_URL % ("/user/repos")
        return self._filter_group_repos(self.do_get(url, "Failed to retrieve user repos.") or [], self.user)

    def get_org_group_repos(self, org):
        url=API_URL % ("/orgs/%s/repos" % org)
        return self._filter_group_repos(self.do_get(url, "Failed to retrieve organization repos.") or [], org)

    def get_branches(self, owner, repo):
        url=API_URL % ("/repos/%s/%s/branches" % (owner, repo))
        return self.do_get(url, "Failed to retrieve branches of: %s owned by: %s." % (repo, owner)) or []

    def get_issues(self, owner, repo, label=None, state=None):
        params = {}
        if label is not None:
            params["labels"] = label
        if state is not None:
            params["state"] = state

        if len(params) > 0:
            query = "?" + "&".join(["%s=%s" % (k,params[k]) for k in params])
        else:
            query = ""

        url=API_URL % ("/repos/%s/%s/issues%s" % (owner, repo, query))

        return self.do_get(url, "Failed to retrieve issues of: %s owned by: %s." % (repo, owner)) or []

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

    def create_tag(self, tag_name, tag_color_hex, owner, repo):
        url = API_URL % ("/repos/%(owner)s/%(repo)s/labels" % {'owner': owner, 'repo': repo})

        fail_message = "Failed to create tag: %(tag)s with color: %(color)s in: %(owner)s/%(repo)s." % {
                'tag': tag_name, 
                'color': tag_color_hex, 
                'owner': owner, 
                'repo': repo
                }

        json_dict= {'name': tag_name, 'color': tag_color_hex}

        return self.do_post(url, json_dict, fail_message)

    def do_post(self, url, json_dict, fail_message):
        print "POST: %s\n%s" % (url, json.dumps(json_dict))
        r=requests.post(url, json=json_dict, headers=self.post_headers)
        if r.status_code == requests.codes.created:
            return r.json()
        else:
            raise Exception("%(fail_message)s. Reason: %(response)s" % {
                'fail_message': fail_message,
                'response': str(r)
                })


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




