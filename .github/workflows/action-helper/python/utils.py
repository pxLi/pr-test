import argparse
import os
import sys

import requests

# constants
API_URL = 'https://api.github.com'


class PullRequest:
    """Pull Request class"""

    def __init__(self,
                 head_owner, head, head_token,
                 base_owner, repo, base, base_token):
        self.head_owner = head_owner
        self.head = head
        self.base_owner = base_owner
        self.base_repo = repo
        self.base = base
        self.pulls_url = f'{API_URL}/repos/{self.base_owner}/{self.base_repo}/pulls'
        self._head_auth_headers = {
            'Accept': 'application/vnd.github.v3+json',
            'Authorization': f"token {head_token}"
        }
        self._base_auth_headers = {
            'Accept': 'application/vnd.github.v3+json',
            'Authorization': f"token {base_token}"
        }

    def get_open(self):
        """get open pull request if existed"""
        params = {
            'state': 'open',
            'head': f"{self.head_owner}:{self.head}",
            'base': self.base,
        }
        print(params)
        r = requests.get(self.pulls_url, headers=self._base_auth_headers, params=params)
        if r.status_code == 200:
            return r.json()
        if r.status_code == 304:
            return None
        # FAILURE
        print('FAILURE - list PR')
        print(f'status code: {r.status_code}')
        raise Exception(f"Failed to create PR: {r.json()}")

    def create(self, params):
        """create a pull request"""
        # the token here must have write access to head owner/repo
        r = requests.post(self.pulls_url, headers=self._head_auth_headers, json=params)
        if r.status_code == 201:
            print('SUCCESS - create PR')
            pull = r.json()
            number = str(pull['number'])
            sha = str(pull['head']['sha'])
            return number, sha, False
        if r.status_code == 422:  # early-terminate if no commits between HEAD and BASE
            print('SUCCESS - No commits')
            print(r.json())
            return '', '', True
        # FAILURE
        print('FAILURE - create PR')
        print(f'status code: {r.status_code}')
        raise Exception(f"Failed to create PR: {r.json()}")

    def merge(self, number, params):
        """merge a pull request"""
        # the token here must have write access to base owner/repo
        url = f'{self.pulls_url}/{number}/merge'
        return requests.put(url, headers=self._head_auth_headers, json=params)

    def auto_merge(self, number, sha):
        """merge a auto-merge pull request"""
        params = {
            'sha': sha,
            'merge_method': 'merge'
        }
        r = self.merge(number, params)
        if r.status_code == 200:
            self.comment(number, '**SUCCESS** - auto-merge')
            print('SUCCESS - auto-merge')
            return
        else:
            print('FAILURE - auto-merge')
            self.comment(number=number, content=f"""**FAILURE** - Unable to auto-merge. Manual operation is required.
```
{r.json()}
```

Please use the following steps to fix the merge conflicts manually:
```
# Assume upstream is {self.base_owner}/{self.base_repo} remote
git fetch upstream {self.head} {self.base}
git checkout -b fix-auto-merge-conflict-{number} upstream/{self.base}
git merge upstream/{self.head}
# Fix any merge conflicts caused by this merge
git commit -am "Merge {self.head} into {self.base}"
git push <personal fork> fix-auto-merge-conflict-{number}
# Open a PR targets {self.base_owner}/{self.base_repo} {self.base}
```
**IMPORTANT:** Before merging this PR, be sure to change the merging strategy to `Create a merge commit` (repo admin only).

Once this PR is merged, the auto-merge PR should automatically be closed since it contains the same commit hashes
""")
            print(f'status code: {r.status_code}')
            raise Exception(f"Failed to auto-merge PR: {r.json()}")

    def comment(self, number, content):
        """comment in a pull request"""
        url = f'{API_URL}/repos/{self.base_owner}/{self.base_repo}/issues/{number}/comments'
        params = {
            'body': content
        }
        r = requests.post(url, headers=self._base_auth_headers, json=params)
        if r.status_code == 201:
            print('SUCCESS - create comment')
        else:
            print('FAILURE - create comment')
            print(f'status code: {r.status_code}')
            print(r.json())


class EnvDefault(argparse.Action):
    """EnvDefault argparse action class"""

    def __init__(self, env, default=None, required=True, **kwargs):
        if not default and env:
            if env in os.environ:
                default = os.environ[env]
        if required and default:
            required = False
        super(EnvDefault, self).__init__(default=default, required=required, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, values)
