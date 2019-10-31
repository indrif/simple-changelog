from semantic_release.vcs_helpers import get_commit_log
from semantic_release.settings import current_commit_parser
from semantic_release.errors import UnknownCommitMessageStyleError
import re
from datetime import datetime

repo_url_format = 'https://phabricator.quinyx.com/rC{}'
from_commit = '1260446706d8'
version = datetime.today().strftime('%Y-%m-%d')

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
    'chore': 'Other'
}

changes = {x: [] for x in types.keys()}



def get_changes(gitfrom=None):
    re_breaking = re.compile('BREAKING CHANGE: (.*)')
    for _hash, commit_message in get_commit_log(gitfrom):
        try:
            message = current_commit_parser()(commit_message)
            if message[1] not in changes:
                continue

            changes[message[1]].append((_hash, message[2],message[3][0]))

            if message[3][1] and 'BREAKING CHANGE' in message[3][1]:
                parts = re_breaking.match(message[3][1])
                if parts:
                    changes['breaking'].append((_hash, parts.group(1)))

            if message[3][2] and 'BREAKING CHANGE' in message[3][2]:
                parts = re_breaking.match(message[3][2])
                if parts:
                    changes['breaking'].append((_hash, parts.group(1)))

        except UnknownCommitMessageStyleError:
            #print('Ignoring', err)
            pass
    return changes

def title(type):
    return types.get(type, type)

def markdown_changelog(version, changelog, header):
    output = ''
    if header:
        output += '## {0}\n'.format(version)

    for section in changes:
        if not changelog[section]:
            continue

        output += '\n\n### {0}\n\n'.format(title(section))
        for item in changelog[section]:
            output += '* **{0}:** {1} ([{2}]({3}))\n'.format(item[1], item[2], item[0][:7], repo_url_format.format(item[0]))

    return output

c = get_changes(from_commit)

m = markdown_changelog(version, c, True)
print(m)