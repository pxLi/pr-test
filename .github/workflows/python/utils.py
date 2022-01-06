import argparse
import os
import sys

import requests

# constants
API_URL = 'https://api.github.com'


class PullRequest:
    """Pull Request class"""

    def __init__(self,
                 head_owner, head_repo, head, head_token,
                 base_owner, base_repo, base, base_token):
        self.head_owner = head_owner
        self.head_repo = head_repo
        self.head = head
        self.base_owner = base_owner
        self.base_repo = base_repo
        self.base = base
        self.pulls_url = f'{API_URL}/repos/{self.base_owner}/{self.base_repo}/pulls'
        self._head_auth_headers = {'Authorization': 'token ' + head_token}
        self._base_auth_headers = {'Authorization': 'token ' + base_token}

    def create(self, params):
        """create a pull request"""
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
        print(r.json())
        sys.exit(1)

    def create_auto_merge(self):
        """create an auto-merge pull request"""
        params = {
            # head share the same owner/repo with base in auto-merge
            'title': f'[auto-merge] {self.head} to {self.base} [skip ci] [bot]',
            'owner': self.head_owner,
            'repo': self.head_repo,
            'head': self.head,
            'base': self.base,
            'body': f'auto-merge triggered by github actions on `{self.head}` to create a PR keeping `{self.base}` up-to-date. If '
                    'this PR is unable to be merged due to conflicts, it will remain open until manually fix.',
            'maintainer_can_modify': True
        }
        return self.create(params)

    def merge(self, number, params):
        """merge a pull request"""
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
            sys.exit(0)
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
            print(r.json())
            sys.exit(1)

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
