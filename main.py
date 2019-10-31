"""simple-changelog

CHANGELOG.md for lazy ppl

Author: Daniel Möller (danne.moeller@gmail.com)

Usage:
    simple-changelog [--from-commit=COMMIT]
                     [--repo-web-url=URL_PREFIX]
                     [--version=VERSION]

Options:
    --from-commit=COMMIT                    Generate output from the specific commit and forward
    --repo-web-url=URL_PREFIX               Set the URL format string to prefix weburls to commits (example: "https://foo.a/commits/{}")
    --version=VERSION                       Set version (header title)
"""
from semantic_release.vcs_helpers import get_commit_log, get_repository_owner_and_name
from semantic_release.settings import current_commit_parser
from semantic_release.errors import UnknownCommitMessageStyleError
from git import GitCommandError, InvalidGitRepositoryError, Repo, TagObject
import re
from datetime import datetime
from docopt import docopt
types = {
    'feature': 'Features',
    'fix': 'Bug Fixes',
    'perf': 'Performance Improvements',
    'revert': 'Reverts',
    'docs': 'Documentation',
    'stype': 'Styles',
    'refactor': 'Code Refactoring',
    'test': 'Tests',
    'build': 'Build System',
    'ci': 'Continuous Integration',
    'chore': 'Other',
    'breaking': 'Breaking Changes'
}

changes = {x: [] for x in types.keys()}

def arg(key, default):
    v = args.get(key, default)
    if v:
        return v
    return default

def get_changes(gitfrom=None):
    re_breaking = re.compile('BREAKING CHANGE: (.*)')
    for _hash, commit_message in get_commit_log(gitfrom):
        try:
            message = current_commit_parser()(commit_message)
            if message[1] not in changes:
                continue

            changes[message[1]].append((_hash, message[2], message[3][0]))

            if message[3][1] and 'BREAKING CHANGE' in message[3][1]:
                parts = re_breaking.match(message[3][1])
                if parts:
                    changes['breaking'].append((_hash, parts.group(1)))

            if message[3][2] and 'BREAKING CHANGE' in message[3][2]:
                parts = re_breaking.match(message[3][2])
                if parts:
                    changes['breaking'].append((_hash, parts.group(1)))

        except UnknownCommitMessageStyleError:
            pass
    return changes

def title(type):
    return types.get(type, type)

def markdown_changelog(version, changelog, header):
    output = ''
    if header:
        output += '## {}\n'.format(version)

    for section in changes:
        if not changelog[section]:
            continue

        output += '\n\n### {}\n\n'.format(title(section))
        for item in changelog[section]:
            output += '*'
            if item[1]:
                output += ' **{}:**'.format(item[1])
            output += ' {} ([{}]({}))\n'.format(item[2], item[0][:7], repo_url_format.format(item[0]))

    return output

args = docopt(__doc__)
if not arg('--repo-web-url', False):
    repo_url_format = Repo('.', search_parent_directories=True).remote('origin').url.split('.git')[0] + '/commit/'
else:
    repo_url_format = arg('--repo-web-url', 'https://foo/{}')
if '{}' not in repo_url_format:
    repo_url_format += '{}'
from_commit = arg('--from-commit', None)
version = arg('--version', datetime.today().strftime('%Y-%m-%d'))

c = get_changes(from_commit)
m = markdown_changelog(version, c, True)
print(m)