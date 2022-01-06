#!/usr/bin/env python
import sys
from argparse import ArgumentParser

from utils import EnvDefault, PullRequest


def main():
    parser = ArgumentParser(description="Automerge")
    parser.add_argument("--owner", action=EnvDefault, env="OWNER",
                        help="github token, will try use env OWNER if empty")
    parser.add_argument("--repo", action=EnvDefault, env="REPO",
                        help="repo name, will try use env REPO if empty")
    parser.add_argument("--head", action=EnvDefault, env="HEAD",
                        help="HEAD ref, will try use env HEAD if empty")
    parser.add_argument("--base", action=EnvDefault, env="BASE",
                        help="Base ref, will try use env BASE if empty")
    parser.add_argument("--token", action=EnvDefault, env="AUTOMERGE_TOKEN",
                        help="github token, will try use env AUTOMERGE_TOKEN if empty")
    args = parser.parse_args()

    pr = PullRequest(head_owner=args.owner, head_repo=args.repo, head=args.head, head_token=args.token,
                     base_owner=args.owner, base_repo=args.repo, base=args.base, base_token=args.token)

    number, sha, term = pr.create_auto_merge()
    if term:
        sys.exit(0)
    # pr.auto_merge(number, sha)


if __name__ == '__main__':
    main()
