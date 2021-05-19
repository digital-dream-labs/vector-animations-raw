#!/usr/bin/env python2
"""
This is a git hook for 'pre-commit' so it runs when a user tries to
locally commit files. Here is a command line to make sure it is
executable and to make a symbolic link from this python script to your
project's .git/hooks/pre-commit file:

chmod a+x ~/workspace/victor-animation/tools/pylibs/ankiutils/git_lock_check_precommit.py
ln -s ~/workspace/victor-animation/tools/pylibs/ankiutils/git_lock_check_precommit.py ~/workspace/<GIT_REPO>/.git/hooks/pre-commit

See the comment for check_list_to_be_commited() for details

The goal of this script is to:
    1. check if the files being committed are locked
    2. if those files are locked by the current user or not locked at
       all, then do nothing and allow the commit/push to go through
    3. if any of those files are locked by a different user, then
       display an error/warning message and prevent all of the files
       from being committed

(c) Anki, Inc 2019
chris rogers 1/19
"""

import os
import json
import subprocess
import re


VERBOSE = True

GITHUB_NAME_FROM_SSH = 'ssh -T -ai ~/.ssh/id_rsa git@github.com'

LIST_TO_BE_COMMITED = 'git diff --cached --name-status'

#LIST_LOCKED_FILES = 'git lfs locks list --json'
LIST_LOCKED_FILES = 'git lfs locks --json'


def printDebug(msg, indent=False):
    if VERBOSE:
        if indent:
            msg = '\t' + msg
        print(msg)


def _run_command(cmd, stdout_pipe=subprocess.PIPE, stderr_pipe=subprocess.PIPE,
                 shell=True, split=False):
    """
    Uses Popen to run a command
    :param cmd: the command to run
    :param stdout_pipe:
    :param stderr_pipe:
    :param shell: bool to determine whether or not to use the shell (environment variables)
    :param split: bool to split the string into an array of words
    :return: status, stdout, stderr (or None, None, None)
    """
    if split:
        cmd = cmd.split()
    printDebug("Running: %s" % cmd)
    try:
        p = subprocess.Popen(cmd, stdout=stdout_pipe, stderr=stderr_pipe, shell=shell)
    except OSError as err:
        print("%s: Failed to execute '%s' because: '%s'" % (type(err).__name__, cmd, err))
        return (None, None, None)
    (stdout, stderr) = p.communicate()
    status = p.poll()
    printDebug('status: {0}'.format(status))
    printDebug('stdout: {0}'.format(stdout.rstrip()))
    printDebug('stderr: {0}'.format(stderr.rstrip()))
    return (status, stdout, stderr)


def check_list_to_be_commited():
    """
    This gathers the git files that are to be committed in this git repo
    (where this hook is installed). It then makes a list of all the
    locked files in this repo and compares the two lists. When it finds
    a locked file that is to be committed, it checks the GitHub username
    of the lock owner with the current users GitHub username. If there
    is one file that does not match, an error message is printed and
    non-zero(1) will be returned to abort the commit.
    """
    files_to_commit = []
    status, stdout, stderr = _run_command(LIST_TO_BE_COMMITED)
    if status != 0:
        msg = "Failed to get list of files to be committed (status={0}) because:".format(status)
        msg += os.linesep + stderr
        raise ValueError(msg)
    files = stdout.split(os.linesep)
    printDebug("files to be commited:")
    for f in files:
        f = f.strip()
        # ignore empty lines
        if f:
            path = f.split('\t')[1]
            printDebug(path, indent=True)
            files_to_commit.append(path)

    files_that_are_locked = []
    status, stdout, stderr = _run_command(LIST_LOCKED_FILES)
    if status != 0:
        msg = "Failed to get list of files currently locked (status={0}) because:".format(status)
        msg += os.linesep + stderr
        raise ValueError(msg)
    printDebug("files that are locked:")
    for f in json.loads(stdout):
        printDebug(f['path'], indent=True)
        files_that_are_locked.append(f)

    to_commit_but_locked_by_other = []
    this_username = get_github_username()
    for locked in files_that_are_locked:
        for to_commit in files_to_commit:
            if locked['path'] == to_commit:
                locked_username = str(locked['owner']['name'])
                msg = "{0} is locked by {1}".format(to_commit, locked_username)
                if locked_username == this_username:
                    printDebug(msg)
                else:
                    to_commit_but_locked_by_other.append(to_commit)
                    print("ERROR: " + msg)
    if to_commit_but_locked_by_other:
        msg = "The following files are locked by another user:"
        msg += os.linesep + os.linesep.join(to_commit_but_locked_by_other)
        raise ValueError(msg)


def get_github_username():
    """
    This function returns the current user's GitHub username.

    The current implemenation uses the user's existing RSA private key
    (~/.ssh/id_rsa) to remotely login to github.com, which does not work
    but does return the authenticated user's name with this message:
        Hi <username>! You've successfully authenticated, but GitHub
        does not provide shell access.
    """
    regex = re.compile(r"Hi (\S+)!")
    username = None
    status, stdout, stderr = _run_command(GITHUB_NAME_FROM_SSH)
    for username in regex.findall(stderr):
        printDebug("username: {0}".format(username))
        return username


if __name__ == "__main__":
    check_list_to_be_commited()


