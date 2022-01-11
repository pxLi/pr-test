#!/usr/bin/env python
import sys
from argparse import ArgumentParser
from distutils.util import strtobool

from utils import EnvDefault, PullRequest


def main():
    parser = ArgumentParser(description="Submodule Sync")
    parser.add_argument("--owner", action=EnvDefault, env="OWNER",
                        help="github token, will try use env OWNER if empty")
    parser.add_argument("--repo", action=EnvDefault, env="REPO",
                        help="repo name, will try use env REPO if empty")
    parser.add_argument("--head", action=EnvDefault, env="HEAD",
                        help="HEAD ref, will try use env HEAD if empty")
    parser.add_argument("--base", action=EnvDefault, env="BASE",
                        help="Base ref, will try use env BASE if empty")
    parser.add_argument("--token", action=EnvDefault, env="TOKEN",
                        help="github token, will try use env TOKEN if empty")
    parser.add_argument("--sha", required=True,
                        help="current HEAD commit SHA")
    parser.add_argument("--cudf_sha", required=True,
                        help="cudf commit SHA")
    parser.add_argument("--passed", default=False, type=lambda x: bool(strtobool(x)), required=True,
                        help="if the test passed")
    args = parser.parse_args()

    pr = PullRequest(head_owner=args.owner, head=args.head, head_token=args.token,
                     base_owner=args.owner, repo=args.repo, base=args.base, base_token=args.token)
    try:
        if exist := pr.get_open():
            number = exist[0].get('number')
            sha = exist[0].get('head').get('sha')
        else:
            params = {
                'title': f"[submodule-sync] {args.head} to {args.base} [skip ci] [bot]",
                'head': f"{args.head_owner}:{args.head}",
                'base': args.base,
                'body': "submodule-sync to create a PR keeping thirdparty/cudf up-to-date.  "
                        f"HEAD commit SHA: {args.sha}, CUDF commit SHA: {args.cudf_sha}  "
                        "The scheduled sync pipeline gets triggered every 6 hours.  "
                        "This PR will be auto-merged if test passed.  "
                        "If failed, it will remain open until test pass or manually fix.",
                'maintainer_can_modify': True
            }
            number, sha, term = pr.create(params)
            if term:  # no change between HEAD and BASE
                sys.exit(0)

        pr.comment(number, content=f"HEAD commit SHA: {args.sha}, CUDF commit SHA: {args.cudf_sha}  "
                                   f"Test passed: {args.passed}")

        if args.passed and args.sha == sha:
            pr.auto_merge(number, sha)
    except Exception as e:
        print(e)
        sys.exit(1)


if __name__ == '__main__':
    main()
