"""
This module provides some convenience functions for interacting with GitHub from
Python scripts. It was written when the Anki animation and audio content
creation pipelines were being updated to store data and tools in GitHub rather
than Subversion (SVN). Therefore, this module was originally written as the Git
equivalent of our existing ankiutils/svn_tools.py module for interacting with
SVN from Python scripts.

Notes of changes from SVN to Git:
- All functions use Git command lines and no third party Git libraries due to
  libraries not being compatible to Git LFS.
- Git commit IDs use hashes (which are 40-character alphanumeric strings that
  can usually be represented with a subset of those 40 characters) rather than
  the revision numbers used for SVN commit IDs.
- Individual files cannot be updated to a specific revision, but rather the
  commit that they are apart of must be updated along with all the other files
  that exist in that commit. Instead of just 'svn update' on an individual file,
  we would have to perform a 'git pull' or 'git fetch' followed by 'git merge'
  on the entire branch.
- It is important to understand how Git workflow works. Changes must be added to
  the staging index before committing

Deleted the following functions from SVN version:
- get_env_vars_for_svn()
- get_svn_file_url()
- check_git_file_lock_local()

TODO: This code should be refactored so it is organized into "GitFile" and
      "GitBranch" classes or something similar rather than the existing
      standalone functions.

Created by John Nguyen in Jan 2019 as a replacement for ankiutils/svn_tools.py
"""

import sys
import os
import shutil
import subprocess
import re
import time


DEFAULT_REMOTE = "origin"

DEFAULT_BRANCH = "master"

GITHUB_URL = "https://github.com/anki"

USER_WORKSPACE = "$HOME/workspace"

DEFAULT_VERSION_REF = "HEAD"

VERBOSE = False

TOOL = "git"

PACKAGING_TOOL = "tar"
PACKAGING_TOOL_OPTIONS = ['-v', '-x', '-z', '-f']

GIT_USERNAME = None
GIT_TOKEN = None

GIT_GET_COMMIT_MSG_CMD  = "git show %s --format=%%B --check '%s'"
GIT_DIFF_CMD = "git diff HEAD %s -- '%s'"
GIT_STATUS_CMD = "git status --porcelain %s" # --procelain is future-proof & backward compatible compared to --short
GIT_NUM_REV_BEHIND_CMD = "git rev-list --left-right --count %s...%s/%s -- %s | cut -f2"
GIT_GET_ROOT_DIR_CMD = "git rev-parse --show-toplevel"
GIT_RENAME_CMD = "git mv '%s' '%s'"
GIT_GET_FILE_REV_HASH_SHORT_CMD = "git log -1 --pretty=format:%%h HEAD -- '%s'"
GIT_GET_LOCKS_CMD = "git lfs locks"
GIT_LOCK_CMD = "git lfs lock '%s'"
GIT_UNLOCK_CMD = "git lfs unlock '%s'"
GIT_GET_FULL_FILE_PATH_CMD = "git ls-files --full-name '%s'"
GIT_STAGE_FILE_CMD = "git add '%s'"
GIT_UNSTAGE_FILE_CMD = "git reset HEAD '%s'"
GIT_COMMIT_CMD = "git commit -m \"%s\" \"%s\""
GIT_CHECKOUT_FILE_FETCH_HEAD_CMD = "git checkout FETCH_HEAD -- '%s'"
GIT_FETCH_CMD = "git fetch %s %s"
GIT_RESET_FETCH_HEAD_CMD = "git reset FETCH_HEAD"
GIT_PULL_CMD = "git pull %s %s"
GIT_PUSH_CMD = "git push %s %s"
GIT_CLONE_CMD = "git clone --progress %s '%s'"
GIT_CLONE_NO_CHECKOUT_CMD = "git clone -n --progress %s '%s'"
GIT_CONFIG_TOKEN_CMD = "git config --global github.token"
GIT_CHECKOUT_BRANCH_CMD = "git checkout %s"
GIT_CHECKOUT_BRANCH_NEW_CMD = "git checkout -b %s"
GIT_GET_CURRENT_BRANCH = "git rev-parse --abbrev-ref HEAD"
GIT_NUM_MODIFIED_FILES_CMD = "git ls-files -m | wc -l"
GIT_STASH_PUSH_CMD = "git stash push --quiet"
GIT_STASH_POP_CMD = "git stash pop --index"
GITHUB_NAME_FROM_SSH_CMD = "ssh -T -ai ~/.ssh/id_rsa git@github.com"
GIT_NO_CHANGES_MSG = "no changes added to commit"
GIT_NOTHING_ADDED_MSG = "nothing added to commit"
GIT_NOTHING_MSG = "nothing to commit"

# The following commands are used to be ran in different directories other than the current one.
GIT_CHECKOUT_CMD = "git --git-dir='{0}/.git' --work-tree='{0}' checkout {1}"
GIT_CLEAN_CMD = "git --git-dir='{0}/.git' --work-tree='{0}' clean -dfq '{1}'"

# Variables used for progress bar in _print_checkout_git_progress.
PROGRESS_BAR_LENGTH = 50
PROGRESS_UNICODE_CHAR = u"\u2592"
NO_PROGRESS_UNICODE_CHAR = u"\u2591"


#
# PUBLIC FUNCTIONS
#


# DONE
def get_git_root_dir(git_repo_path=None):
    """
    Returns the root directory of current Git directory from any of its
    subdirectory.

    :return
        The string of the Git root directory.
    """
    cmd = ""
    if git_repo_path:
        cmd = _chdir_cmd_prefix(git_repo_path)
    cmd += GIT_GET_ROOT_DIR_CMD
    (status, stdout, stderr) = _run_command(cmd, shell=True)
    if status == 0:
        git_root_dir = stdout.strip()
        return git_root_dir
    else:
        if not stderr:
            stderr = stdout
        msg = "Failed to show top level in Git because: %s" % stderr
        raise ValueError(msg)


# DONE
def is_up(url_string=GITHUB_URL):
    """
    Checks to see if the url_string is online and reachable.

    :param
        url_string: the url of the server that the program is trying to reach.

    :return
        'True': if the server is reachable
        'False': if the server is not reachable
    """
    import urllib2
    try:
        urllib2.urlopen(url_string)
        return True
    except urllib2.HTTPError, e:
        if e.code == 401:
            # Authentication error site is up and requires login.
            return True
        #print("is_up error: %s" % e.code)
        return False
    except urllib2.URLError, e:
        return False


# DONE
def check_for_user_match(user_name):
    """
    Given a Git username, this function will return True if it matches the
    current user or else return False.

    :param
        user_name: The username that function is comparing to the current user

    :return
        'True': provided username matches current user
        'False': provided username does NOT match current user
    """
    if get_github_username() == user_name:
        return True
    else:
        return False


# DONE
def get_commit_info(file_path, raise_on_fail=True, long_hash=False):
    """
    Given the path to a file on disk, this function returns a tuple containing
    the file name, file version and commit message.

    :param
        file_path: The file in Git that the function is trying to get the
                   commit information of.
        raise_on_fail: What to do when the function cannot retrieve the file
                       version. Raise a RunTimeError when this parameter is set
                       to 'True', else simply return 'None'.
        long_hash: If set to 'True', will display the file version hash as the
                   full 40-character hash instead of the short 7-character hash.

    :return
        3-item tuple containing string values: (file name, version, commit message)
    """
    file_name = os.path.basename(file_path)
    if os.path.isfile(file_path):
        file_ver = get_git_file_rev(file_path, raise_on_fail=raise_on_fail, long_hash=long_hash)
    else:
        file_ver = None
    commit_msg = get_git_commit_message(file_path, file_ver)
    return (file_name, file_ver, commit_msg)


# DONE
# was rename_svn_file()
def rename_git_file(src, dst):
    """
    Given the full path name of a file, this function will rename that file
    in the same directory and keep the same file extension.

    This function should be used purely for renaming.

    If dst has a different file path or file extension, this function will
    ignore it and use the src's file path or file extension respectively.

    Note that by renaming the file, this will also stage the file for committing.

    :param
        src: The file name that will be renamed.
        dst: The resulting file name of the file, src.
    """
    dir_name = os.path.dirname(src)
    file_ext = os.path.splitext(src)[1]

    # Force dst to use src's file path.
    dst = os.path.basename(dst)
    dst = os.path.join(dir_name, dst)

    # Force dst to use src's file extension.
    dst = os.path.splitext(dst)[0] + file_ext

    # No name change was actually made, so don't bother running Git rename.
    if src == dst:
        return

    cmd = _chdir_cmd_prefix(src)
    cmd += GIT_RENAME_CMD % (src, dst)
    (status, stdout, stderr) = _run_command(cmd, shell=True)
    if status != 0:
        if not stderr:
            stderr = stdout
        raise RuntimeError("Failed to move %s to %s because: %s" % (src, dst, stderr))


# DONE
# was get_svn_file_rev()
def get_git_file_rev(file_from_git, raise_on_fail=False, long_hash=False, from_remote=False):
    """
    Given a file, return the latest revision as a hash.

    If the revision cannot be determined, this function returns 'None' or raises
    a RunTimeError (depending on the 'raise_on_fail' input parameter).

    :param
        file_path: The file in Git that the function is trying to get the commit
                   information of.
        raise_on_fail: What to do when the function cannot retrieve the file
                       version. Raise a RunTimeError when this parameter is set
                       to 'True', else simply return 'None'.
        long_hash: If set to 'True', will display the file version hash as the
                   full 40-character hash instead of the short 7-character hash.
        from_remote: If 'True', gets the revision from the remote instead of
                     locally. The remote information can be obtain once the user
                     has fetched the remote information with 'git fetch' or
                     'git pull'. Note: git_fetch() and git_pull() functions
                     exist in this module.

    :return
        The revision hash of the file.
    """
    cmd = _chdir_cmd_prefix(file_from_git)
    cmd += GIT_GET_FILE_REV_HASH_SHORT_CMD % os.path.basename(file_from_git)

    if long_hash:
        cmd = cmd.replace("%h", "%H")

    if from_remote:
        cmd = cmd.replace(DEFAULT_VERSION_REF, DEFAULT_REMOTE + "/" + DEFAULT_VERSION_REF)

    (status, stdout, stderr) = _run_command(cmd, shell=True)
    stdout = stdout.strip()
    if status != 0 or not stdout:
        if raise_on_fail:
            if not stderr:
                stderr = stdout
            raise RuntimeError("Unable to determine the Git version of %s because: %s"
                               % (file_from_git, stderr))
        else:
            return None
    return stdout


# DONE
# was get_svn_comment()
def get_git_commit_message(git_file, rev_hash):
    """
    Returns the commit message of git_file at revision rev_hash.

    :param
        git_file: The file in the Git repository.
        rev_hash: The hash revision string used to obtain the commit message of
                  git_file. Note: Git recommends that the provided hash revision
                  string is 8-characters or longer to guarantee uniqueness
                  within a project.

    :return
        The commit message of git_file at rev_hash
    """
    cmd = _chdir_cmd_prefix(git_file)
    cmd += GIT_GET_COMMIT_MSG_CMD % (rev_hash, os.path.basename(git_file))
    (status, stdout, stderr) = _run_command(cmd, shell=True)
    if status == 0:
        return stdout.strip()
    else:
        if not stderr:
            stderr = stdout
        msg = "Failed to get the commit message because: %s" % stderr
        raise ValueError(msg)


# DONE
# was check_svn_file_modified()
def check_git_file_modified(git_file):
    """
    This function can be used to determine if the local version
    of a file is modified or not.
    Whether the file is staged or not does not matter.
    This function only checks if modified, not the other statuses.

    :param
        git_file: The file to check if it is modified or not.

    :return
        'True': The file is modified locally.
        'False': The file is not modified locally.
    """
    (index, worktree) = get_git_status_of_file(git_file)
    return index == 'M' or worktree == 'M'


# DONE
def get_git_status_of_file(git_file):
    """
    Please read: https://git-scm.com/docs/git-status#_short_format
    Returns the index status and worktree status of git_file.

    Index is the same thing is as the staging status.
    Worktree is the same thing as local, unstaged status.

    Output of this file is of the format:
        IW git_file
    where I represent the status of the Index,
    and W represents the status of the Worktree.
    It is possible for either I or W to be empty.

    :param
        git_file: The file to check the status of.

    :return
        A tuple that contains 2 single-character statuses of
        both the Index and the Worktree of the file.
    """
    cmd = _chdir_cmd_prefix(git_file)
    cmd += GIT_STATUS_CMD % os.path.basename(git_file)
    (status, stdout, stderr) = _run_command(cmd, shell=True)
    if status != 0:
        if not stderr:
            stderr = stdout
        msg = "Failed to check file status because: %s" % stderr
        raise ValueError(msg)
    if stdout:
        index = stdout[0].strip() if stdout[0] else None
        worktree = stdout[1].strip() if stdout[1] else None
    else:
        index = None
        worktree = None
    return (index, worktree)


# DONE
# was check_svn_file_outdated()
def check_git_file_outdated(git_file, remote=DEFAULT_REMOTE, branch=DEFAULT_BRANCH):
    """
    Checks if the git_file is outdated or not.

    This function will only works if the user has performed 'git fetch' before
    using this function.

    :param
        git_file: The file in the Git directory to check.
        remote: The name of the remote server, typically 'origin'.
        branch: The name of the branch.

    :return
        'True': The file is outdated.
        'False': The file is not outdated.
    """
    cmd = _chdir_cmd_prefix(git_file)
    cmd += GIT_NUM_REV_BEHIND_CMD % (branch, remote, branch, os.path.basename(git_file))
    (status, stdout, stderr) = _run_command(cmd, shell=True)
    if status != 0:
        if not stderr:
            stderr = stdout
        msg = "Failed to check if file is outdated because: %s" % stderr
        raise ValueError(msg)

    # The number in stdout represents how many revisions behind the file is, so return True
    # to indicate that the file is outdated if it is more than zero revisions behind, else
    # return False

    return int(stdout) > 0


# DONE
# was get_svn_diff()
def get_git_diff(git_file, rev_hash, timeout_secs=10):
    """
    Returns the diff result of a file with its current version and the
    version from revision rev_has.

    :param
        git_file: The file in the Git directory to compare.
        rev_hash: The revision hash to compare the current file to.
        timeout_secs: Times out after X seconds.

    :return
        The typical results of running the diff command on two files, showing
        the lines in the file that are different.
    """
    cmd = _chdir_cmd_prefix(git_file)
    cmd += GIT_DIFF_CMD % (rev_hash, os.path.basename(git_file))
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, shell=True)
    status = None
    timer = 0
    while status is None and timer < timeout_secs:
        time.sleep(1)
        timer += 1
        status = p.poll()
    if status is None:
        stdout = ""
        stderr = "timeout"
    else:
        (stdout, stderr) = p.communicate()
    if status != 0:
        print("Unable to determine the Git diff for %s because: %s"
              % (git_file, os.linesep + stderr))
        return None
    diff_lines = stdout.split(os.linesep)
    return diff_lines


# DONE
# was get_svn_workspace()
def get_user_workspace(workspace=USER_WORKSPACE):
    """
    Returns workspace as a full path. If workspace contains a environment
    variable, such as $HOME, this function will expand it to its full path.

    :param
        workspace: The workspace directory that will be returned as a full path.

    :return
        Returns the workspace parameter as a full path, and expands workspace
        if it has an environment variable that needs to be expanded.
    """
    workspace_parts = workspace.split(os.sep)
    for idx in range(len(workspace_parts)):
        part = workspace_parts[idx]
        if part.startswith("$"):
            part = os.getenv(part[1:])
            workspace_parts[idx] = part
    return os.sep.join(workspace_parts)


# DONE
# was get_svn_file_path()
def get_git_file_path(file_url, git_workspace, removal_tokens=["blob"]):
    """
    Given the GitHub URL for a Git file, this function should return
    the corresponding file on disk.

    The path does not necessarily have to exist, but rather this function
    suggests the path given the file_url and the git_workspace.

    :param
        file_url: The file url from GitHub.
        git_workspace: The local workspace directory that contains
                       the local git repo.
        removal_tokens: A list of tokens to be parsed out of the file_url.
    """
    local_file_path = file_url.replace(GITHUB_URL, git_workspace)
    if not os.path.isfile(local_file_path) and DEFAULT_BRANCH in local_file_path.split(os.sep):
        local_file_path = local_file_path.replace(DEFAULT_BRANCH, "")
    for removal_token in removal_tokens:
        if not os.path.isfile(local_file_path) and removal_token in local_file_path.split(os.sep):
            local_file_path = local_file_path.replace(removal_token, "")
    return os.path.normpath(local_file_path)


# DONE-ish - parts of code are commented out because of unknown use in checkout_git_repo().
# This is used to get the latest version of the SoundBanks repo.
# was checkout_svn_package()
def checkout_git_package(repo, dest, branch=DEFAULT_BRANCH, remote_url=GITHUB_URL,
                         version=DEFAULT_VERSION_REF, user="", password="", verbose=VERBOSE):
    """
    This function can be used to checkout a package from Git.

    :param
        repo: The other repo that we are checking out.
        dest: The destination folder where we'll place the repo.
        branch: The branch we want to check out from the repo.
        remote_url: The remote url that we are trying to reach
        version: The Git version hash.
        (Deprecated) user: GitHub username. Deprecated because user name can be retrieved from .gitconfig.
        (Deprecated) password: GitHub SSO Token. Deprecated because password can be retrieved from .gitconfig.
        verbose: Whether or not the output will be verbose or not.
    """
    # Checks to see if the GitHub servers are accessible
    if not is_up(remote_url):
        raise ValueError("{0} is not available; check your network connections".format(remote_url))

    # Gets the last revision
    l_rev = 'unknown'
    if l_rev != 0 and os.path.isdir(dest):
        l_rev = get_git_file_rev(dest)
        print("The version of [%s] is [%s]" % (dest, l_rev))
        if l_rev is None:
            l_rev = 0
            msg = "Clearing out [%s] directory before getting a fresh copy."
            if os.path.exists(dest):
                print(msg % dest)
                shutil.rmtree(dest)
    else:
        l_rev = 0

    print("Checking out {0} (version {1}), this could take several minutes...".format(repo, version))
    checkout_git_repo(repo, dest, version, user, password, verbose)


# NEW
def checkout_git_repo(repo, dest="", version=DEFAULT_VERSION_REF, username="", password="",
                      verbose=VERBOSE):
    """
    Checks out the Git repo from GitHub at a specific version to the path, dest.

    This function will initially checkout the Git repository without downloading
    any files from the repository and then files will be downloaded if checkout
    was successful.

    Enable the verbose parameter to display a progress bar, otherwise this
    function will run silently.

    :param
        repo: The repo to check out.
        dest: The local location to place the checked out repo.
        version: The revision hash of the repo to check out.
        username: The GitHub username used to check out the repo.
        password: The GitHub SSO token or password to check out the repo.
        verbose: Enable the check out output to be verbose or not.
    """
    clone_git_repo_without_checking_out(repo=repo, dest=dest, username=username, password=password)

    checked_out_dir = os.path.join(dest, repo)
    checkout_repo_cmd = GIT_CHECKOUT_CMD.format(checked_out_dir, version)

    if verbose == True:
        return_val = _print_checkout_git_progress(checkout_repo_cmd)
    else:
        p = subprocess.Popen(checkout_repo_cmd, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, shell=True)
        (stdout, stderr) = p.communicate()
        return_val = p.poll()
    if return_val != 0:
        raise RuntimeError("Failed to check out '%s' at %s" % (version, checked_out_dir))

    # If check out was successful, then clean the directory to remove
    # any file that doesn't belong to the repo.
    git_clean_directory(checked_out_dir)


def unpack_package(package, ptool=PACKAGING_TOOL, ptool_options=PACKAGING_TOOL_OPTIONS,
                   verbose=VERBOSE):
    """
    Unpacks a tarball.

    :param
        package: The tarball to unpack.
        ptool: The packaging tool that is used to unpack the package.
        ptool_options: Options and flags used with ptool.
        verbose: If 'True', prints out the output of this command.
    """
    dest = os.path.dirname(package)
    if package and os.path.isfile(package):
        unpack_cmd = [ptool] + ptool_options + [package, '-C', dest]
        pipe = subprocess.Popen(unpack_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if verbose:
            stdout, stderr = pipe.communicate()
            print(stderr)
    else:
        raise ValueError("Failed to unpack %s" % package)


# NEW
def clone_git_repo_without_checking_out(repo, dest="", username="", password=""):
    """
    Clones the repo from GitHub, but doesn't check out any files, leaving the
    directory empty after cloning.

    :param
        repo: The name of the repository from GitHub that will be cloned.
        dest: The destination to clone the repository.
        username: The username used to clone the repository.
        password: The SSO token or password used to clone the repository.
    """
    if not dest:
        raise ValueError("Please specify a destination to clone repo.")

    # Creates the GitHub checkout URL that will be used with 'git clone'
    git_checkout_url = get_github_url_with_credentials(username, password)
    git_checkout_url = os.path.join(git_checkout_url, repo)
    git_checkout_url += ".git"

    # Form the command to clone the repository 'repo' into the directory 'dest'.
    dest_dir = os.path.join(dest, repo)
    clone_repo_cmd = GIT_CLONE_NO_CHECKOUT_CMD % (git_checkout_url, dest_dir)

    (status, stdout, stderr) = _run_command(clone_repo_cmd, shell=True)
    if status != 0:
        if not stderr:
            stderr = stdout
        msg = "Failed to clone '%s' to %s because: %s" % (repo, dest_dir, stderr)
        raise ValueError(msg)


# NEW
def get_github_url_with_credentials(username=None, password=None, github_url=GITHUB_URL):
    """
    Returns the GitHub URL and includes the username and password within the URL

    :param
        username: The GitHub username. If this parameter is empty, this
                  function will retrieve it.
        password: The GitHub SSO token or password. If this parameter is
                  empty, this function will retrieve it from .gitconfig.

    :return
        Returns the string 'https://<username>:<password>@github.com/anki'
    """
    if not username:
        username = get_github_username()
    if not password:
        password = _get_github_token()
    return github_url.replace("//", "//" + username + ":" + password + "@")


# NEW
def git_clean_directory(git_repo_dir=None, sub_dir=None):
    """
    Runs 'git clean' on the provided git repo directory (or the current
    working directory if no directory is provided).

    This will remove any files that are not tracked or staged by Git in
    every directory recursively.

    :param
        git_repo_dir: A specified local Git directory. If empty, then it
                      cleans the current working directory.
        sub_dir: A subdirectory of git_repo_dir.
    """
    # Use the current working directory if no repo dir was supplied
    if not git_repo_dir:
        git_repo_dir = "."

    # If a repo's subdirectory is not specified, check the entire Git directory.
    if not sub_dir:
        sub_dir = "."

    cleanup_cmd = GIT_CLEAN_CMD.format(git_repo_dir, sub_dir)

    (status, stdout, stderr) = _run_command(cleanup_cmd, shell=True)
    if status != 0:
        if not stderr:
            stderr = stdout
        msg = "Failed to clean up '%s' because: %s" % (sub_dir, stderr)
        raise ValueError(msg)


# DONE
# was check_file_in_svn()
# use this function in place of: check_file_never_committed()
def is_file_tracked_in_git(file_to_check, check_remote=False):
    """
    Checks to see if a file is already under version control/tracked by Git

    :param
        file_to_check: The local filesystem path in the Git directory.
        check_remote: Bool for whether to check if the file is tracked remotely
                      rather than locally.

    :return
        'True': If the file is tracked in Git.
        'False': If the file is not tracked in Git.
    """
    if get_git_file_rev(file_to_check, from_remote=check_remote):
        return True
    else:
        return False


# NEW
def is_file_staged_in_git(git_file):
    """
    Checks to see if git_file is staged or not.
    A file is staged if a status exists for the Index, but not for the Worktree.

    :param
        git_file: The local filesystem path in the Git directory.

    :return
        'True': The file is staged.
        'False': The file is not staged.
    """
    (index, worktree) = get_git_status_of_file(git_file)
    return bool(index and not worktree)


# DEPR - Files in Git are either locked or not and does not matter
# if files are locked locally or remotely.
# Use check_git_file_lock() in place of this function.
#def check_git_file_lock_local(file_in_svn):
#    return check_git_file_lock(file_in_svn, remote=False)


# DONE
# was check_svn_file_lock()
# Use this function in place of check_git_file_lock_local()
def check_git_file_lock(file_in_git):
    """
    Returns the lock owner for file_in_git.
    If lock for file_in_git doesn't exist, return None.

    :param
        file_in_git: The local file system path in the Git directory.

    :return
        The username that locked file_in_git.
        'None' if no one has the file locked.
    """
    cmd = _chdir_cmd_prefix(file_in_git)
    cmd += GIT_GET_LOCKS_CMD
    (status, stdout, stderr) = _run_command(cmd, shell=True)
    if status == 0:
        all_locked_files = stdout.splitlines()
        for line in all_locked_files:
            locked_file = line.split("\t")
            if locked_file[0].strip() == os.path.basename(file_in_git):
                return locked_file[1].strip()
        return None
    else:
        if not stderr:
            stderr = stdout
        msg = "Failed to get lock list for '%s' file because: %s" % (file_in_git, stderr)
        raise ValueError(msg)


# DONE
# was lock_svn_file()
def lock_git_file(file_in_git):
    """
    Locks a file that resides in a Git repo via Git LFS.

    :param
        file_in_git: The local file system path in the Git directory.
    """
    cmd = _chdir_cmd_prefix(file_in_git)
    cmd += GIT_LOCK_CMD % os.path.basename(file_in_git)
    (status, stdout, stderr) = _run_command(cmd, shell=True)
    if status == 0:
        print("Locked '%s' file in Git." % file_in_git)
    else:
        lock_owner = check_git_file_lock(file_in_git)
        if check_for_user_match(lock_owner):
            print("%s is already locked by current user." % file_in_git)
            return
        if not stderr:
            stderr = stdout
        msg = "Failed to lock '%s' file in Git because: %s" % (file_in_git, stderr)
        raise ValueError(msg)


# DONE
# was unlock_svn_file()
def unlock_git_file(file_in_git):
    """
    Unlocks a file that resides in a Git repo via Git LFS.

    :param
        file_in_git: The local file system path in the Git directory.
    """
    cmd = _chdir_cmd_prefix(file_in_git)
    cmd += GIT_UNLOCK_CMD % os.path.basename(file_in_git)
    (status, stdout, stderr) = _run_command(cmd, shell=True)
    if status == 0:
        print("Unlocked '%s' file in Git." % (file_in_git))
    else:
        lock_owner = check_git_file_lock(file_in_git)
        if lock_owner == None:
            print("%s is not locked by anyone, so no need to unlock it." % file_in_git)
            return
        if not stderr:
            stderr = stdout
        msg = "Failed to unlock '%s' file in Git because: %s" % (file_in_git, stderr)
        raise ValueError(msg)


# NEW
# was add_svn_file() WITHOUT committing the file after adding
def stage_git_file(file_in_git):
    """
    Stages file_in_git to the Git Index.

    :param
        file_in_git: The local file system path in the Git directory.
    """
    cmd = _chdir_cmd_prefix(file_in_git)
    cmd += GIT_STAGE_FILE_CMD % os.path.basename(file_in_git)
    (status, stdout, stderr) = _run_command(cmd, shell=True)
    if status == 0:
        print("'%s' is staged for commit" % file_in_git)
    else:
        if not stderr:
            stderr = stdout
        msg = "Failed to stage file '%s' to index because: %s" % (file_in_git, stderr)
        raise ValueError(msg)


# NEW
def unstage_git_file(file_in_git):
    """
    Unstages file_in_git from the Git Index.

    :param
        file_in_git: The local file system path in the Git directory.
    """
    cmd = _chdir_cmd_prefix(file_in_git)
    cmd += GIT_UNSTAGE_FILE_CMD % os.path.basename(file_in_git)
    (status, stdout, stderr) = _run_command(cmd, shell=True)
    if status == 0:
        print("'%s' is unstaged from commit" % file_in_git)
    else:
        if not stderr:
            stderr = stdout
        msg = "Failed to unstage file '%s' in Git because: %s" % (file_in_git, stderr)
        raise ValueError(msg)


# DONE
# was add_svn_file() WITH the added functionality of committing and pushing after adding
def add_and_push_new_git_file(file_for_git):
    """
    Adds, commits and pushes the file_for_git to the remote on GitHub.
    This works just like 'svn add' followed by 'svn commit'.

    :param
        file_for_git: The local file system path in the Git directory.

    :return
        The new commit hash string for pushing this file.
    """
    _get_file_stats(file_for_git)
    if is_file_tracked_in_git(file_for_git, check_remote=True):
        msg = "The %s file is already under Git version control" % os.path.basename(file_for_git)
        print(msg)
        return
    stage_git_file(file_for_git)
    commit_msg = "Added: " + file_for_git
    return commit_and_push_git_file(file_for_git, comment=commit_msg, unlock=False)


# DONE - but with very specific instructions on usage.
# was update_svn_file()
def update_git_file(file_in_git):
    """
    This is the recommended usage of this function to make it work similar
    to 'svn update':

    1. Before checking any files, use git_fetch() (i.e. 'git fetch') to pull
    in changes like new commits and file updates, but not apply them (see
    https://git-scm.com/docs/git-fetch for additional details)

    2. After Step 1, this update_git_file() function may be used to update
    each file individually.

    3. After running Step 2 for all files, use git_reset_fetch_head()
    (i.e. 'git reset FETCH_HEAD'). This will update the local commit version
    to latest one that was fetched. All files that were updated in Step 2
    will be consistent with this latest commit. Any files that were not
    updated in Step 2 will be shown as modified or conflicted.

    :param
        file_in_git: The local file system path in the Git directory.
    """
    _get_file_stats(file_in_git)
    if not is_file_tracked_in_git(file_in_git):
        msg  = "The %s file is not yet under version control" % os.path.basename(file_in_git)
        msg += ", so no need to update it."
        print(msg)
        return

    prev_rev_hash = get_git_file_rev(file_in_git)
    rev_hash = get_git_file_rev(file_in_git, from_remote=True)
    if prev_rev_hash == rev_hash:
        msg = "File is already up to date at version (%s)." % (rev_hash)
        print(msg)
        return

    cmd = _chdir_cmd_prefix(file_in_git)
    cmd += GIT_CHECKOUT_FILE_FETCH_HEAD_CMD % os.path.basename(file_in_git)
    (status, stdout, stderr) = _run_command(cmd, shell=True)
    if status == 0:
        print("Updated '{0}' file from version ({1}) to ({2})".format(file_in_git, prev_rev_hash, rev_hash))
    else:
        if not stderr:
            stderr = stdout
        msg = "Failed to update '{0}' file because: {1}".format(file_in_git, stderr)
        raise ValueError(msg)


# NEW
def commit_git_file(file_in_git, comment, branch=DEFAULT_BRANCH, create_new_branch=False):
    """
    Performs 'git commit' on file_in_git.
    Careful: This will commit the file even if the file isn't staged.

    For something more like 'svn commit', please use commit_and_push_git_file()
    instead.

    :param
        file_in_git: The local file system path in the Git directory.
        comment: The commit message.
        branch: Git branch to commit file to.
        create_new_branch: If True, create the branch if it doesn't exist yet.
                           Otherwise, an error will be thrown.

    :return
        The revision hash string of the new commit.
    """
    rev_number = None
    err_msg = None

    # If a branch name was provided as an input parameter and that branch is
    # different from the current one, then checkout that named branch.
    is_different_branch = not is_git_branch_same_as_current(branch, file_in_git)
    if is_different_branch:
        # Save current branch name so we can return to it after committing completes.
        current_branch = get_current_git_branch(file_in_git)
        try:
            git_checkout_branch(branch, file_in_git, create_new_branch)
        except ValueError as err:
            git_checkout_branch(current_branch, file_in_git)
            raise err

    # Commit the file (after adding/staging it if needed).
    if not is_file_tracked_in_git(file_in_git, check_remote=False):
        stage_git_file(file_in_git)
    cmd = _chdir_cmd_prefix(file_in_git)
    cmd += GIT_COMMIT_CMD % (comment, os.path.basename(file_in_git))
    (status, stdout, stderr) = _run_command(cmd, shell=True)
    if status == 0:
        # Look up and return the rev number if file was successfully committed
        rev_number = get_git_file_rev(file_in_git)
        print("Committed '%s' revision %s " % (file_in_git, rev_number))
    else:
        if not stderr:
            stderr = stdout
        if GIT_NO_CHANGES_MSG in stderr:
            stderr = GIT_NO_CHANGES_MSG
        elif GIT_NOTHING_MSG in stderr:
            stderr = GIT_NOTHING_MSG
        elif GIT_NOTHING_ADDED_MSG in stderr:
            stderr = GIT_NOTHING_ADDED_MSG
        err_msg = "Failed to commit '{0}' file to Git because: {1}".format(file_in_git, stderr)

    # Restore the original branch if a different branch was checked out above
    if is_different_branch:
        git_checkout_branch(current_branch, file_in_git)

    if err_msg:
        raise ValueError(err_msg)

    return rev_number


# DONE
# was commit_svn_file()
def commit_and_push_git_file(file_in_git, comment, branch=DEFAULT_BRANCH, create_new_branch=False,
                             unlock=True):
    """
    Commits a file that may or may not already be under Git version control.

    This will push all commits between origin/HEAD and the last local commits.

    This function assumes that users will not add other commits from other tools,
    and assumes that only one commit will be pushed.

    If the file isn't modified, this function will do nothing and return 'None'.

    :param
        file_in_git: The local file system path in the Git directory.
        comment: Mandatory commit message for Git
        unlock: If True, attempts to unlock the file after committing it.
                Otherwise, proceeds without unlocking the file.
        branch: Git branch to commit and push changes to.
        create_new_branch: If True, create the branch if it doesn't exist yet.
                           Otherwise, an error will be thrown.

    :return
        The revision number of the commit transaction if commit was successful.
        (possibly 'None' if the commit failed but likely to raise ValueError
        in that case)
    """
    _get_file_stats(file_in_git)

    # Commit the file.
    rev_number = commit_git_file(file_in_git, comment, branch, create_new_branch)

    if rev_number:
        # Push the commit to GitHub.
        git_push(branch=branch, git_repo_path=file_in_git)

        # Unlocks the file after pushing.
        if unlock:
            unlock_git_file(file_in_git)

    return rev_number


# NEW
def git_checkout_branch(branch, git_repo_path=None, create_new_branch=False):
    """
    Performs 'git checkout <branch>'
    If create_new_branch is True, then create the branch if it doesn't exist.
    """
    # First attempt to fetch the specified branch before attempting to check it out locally.
    try:
        git_fetch(branch=branch, git_repo_path=git_repo_path)
    except ValueError:
        pass

    cmd = ""
    if git_repo_path:
        cmd = _chdir_cmd_prefix(git_repo_path)
    if create_new_branch:
        cmd += GIT_CHECKOUT_BRANCH_NEW_CMD % branch
    else:
        cmd += GIT_CHECKOUT_BRANCH_CMD % branch
    (status, stdout, stderr) = _run_command(cmd, shell=True)
    if status != 0:
        if not stderr:
            stderr = stdout
        msg = "Failed to checkout branch: {0}".format(stderr)
        raise ValueError(msg)


# NEW
def is_git_branch_same_as_current(other_branch, git_repo_path=None):
    """
    This function returns True if the provided branch is the same
    as the one currently active in the local workspace/repo.
    """
    return (get_current_git_branch(git_repo_path) == other_branch)


# NEW
def get_current_git_branch(git_repo_path=None):
    """
    Returns the name of the current branch that is checked out.
    """
    cmd = ""
    if git_repo_path:
        cmd = _chdir_cmd_prefix(git_repo_path)
    cmd += GIT_GET_CURRENT_BRANCH
    stdout = _run_command_wrapper(cmd)
    return stdout.strip()


# NEW
def get_num_modified_git_files():
    """
    Returns the number of modified tracked files.
    """
    cmd = GIT_NUM_MODIFIED_FILES_CMD
    stdout = _run_command_wrapper(cmd)
    return int(stdout.strip())


# NEW
def git_stash_push():
    """
    Performs 'git stash push'
    Doesn't push newly added, untracked files at the moment.
    """
    cmd = GIT_STASH_PUSH_CMD
    stdout = _run_command_wrapper(cmd)


# NEW
def git_stash_pop():
    """
    Performs 'git stash pop --index'
    """
    cmd = GIT_STASH_POP_CMD
    stdout = _run_command_wrapper(cmd)


# NEW
def git_fetch(remote=DEFAULT_REMOTE, branch=DEFAULT_BRANCH, git_repo_path=None):
    """
    Performs a 'git fetch' in the current working directory
    or the directory of the provided file.
    """
    cmd = ""
    if git_repo_path:
        cmd = _chdir_cmd_prefix(git_repo_path)
    cmd += GIT_FETCH_CMD % (remote, branch)
    (status, stdout, stderr) = _run_command(cmd, shell=True)
    if status != 0:
        if not stderr:
            stderr = stdout
        msg = "Failed to fetch from GitHub because: %s" % stderr
        raise ValueError(msg)


# NEW
def git_reset_fetch_head(git_repo_path=None):
    """
    Performs a 'git reset' to the reference FETCH_HEAD.
    This is a niche function used after update_git_file().
    Must first update the local Git repository with
    'git fetch <remote> <branch>' or git_fetch() to get
    remote changes, otherwise the local Git directory will
    update to the last Git fetch.
    """
    cmd = ""
    if git_repo_path:
        cmd = _chdir_cmd_prefix(git_repo_path)
    cmd += GIT_RESET_FETCH_HEAD_CMD
    (status, stdout, stderr) = _run_command(cmd, shell=True)
    if status != 0:
        if not stderr:
            stderr = stdout
        msg = "Failed to reset to FETCH_HEAD because: %s" % stderr
        raise ValueError(msg)


# NEW
def git_pull(remote=DEFAULT_REMOTE, branch=DEFAULT_BRANCH, git_repo_path=None):
    """
    Performs a 'git pull' from GitHub which will fetch remote changes
    and attempt to merge the file.
    """
    cmd = ""
    if git_repo_path:
        cmd = _chdir_cmd_prefix(git_repo_path)
    cmd += GIT_PULL_CMD % (remote, branch)
    try:
        stdout = _run_command_wrapper(cmd)
    except ValueError, e:
        msg = "Failed to pull from GitHub because: %s" % e
        raise ValueError(msg)
    else:
        print("Git pull was successful")


# NEW
def git_push(remote=DEFAULT_REMOTE, branch=DEFAULT_BRANCH, git_repo_path=None):
    """
    Pushes all local commits on the branch to the remote.

    :param
        remote: The name of the remote.
        branch: The name of the branch.
    """
    cmd = ""
    if git_repo_path:
        cmd = _chdir_cmd_prefix(git_repo_path)
    cmd += GIT_PUSH_CMD % (remote, branch)
    try:
        stdout = _run_command_wrapper(cmd)
    except ValueError, e:
        msg = "Failed to push to GitHub because: %s" % e
        raise ValueError(msg)
    else:
        print("Push to GitHub was successful")


def get_github_username():
    """
    This function returns the current user's GitHub username.

    The current implemenation uses the user's existing RSA private key
    (~/.ssh/id_rsa) to remotely login to github.com, which does not work
    but does return the authenticated user's name with this message:
        Hi <username>! You've successfully authenticated, but GitHub
        does not provide shell access.
    """
    global GIT_USERNAME
    if GIT_USERNAME:
        return GIT_USERNAME
    regex = re.compile(r"Hi (\S+)!")
    username = None
    status, stdout, stderr = _run_command(GITHUB_NAME_FROM_SSH_CMD, shell=True)
    if not stderr:
        stderr = stdout
    for username in regex.findall(stderr):
        #print("username: {0}".format(username))
        GIT_USERNAME = username
        return GIT_USERNAME
    msg = "Failed to get GitHub username: {0}".format(stderr)
    raise ValueError(msg)


#
# PRIVATE FUNCTIONS
#


# The Git version of this function might not correlate a 100% with SVN.
# credentials are stored in .git/config either in local or global,
# so there might be no need to use this function.
#def _inject_credentials(cmd, credentials=None):
#    """
#    Given an SVN command and credentials, inject the credentials into the command
#
#    :param
#        cmd: SVN command to execute
#        credentials: SVN credentials in the form of "--username USER --password XXXXXXXX"
#
#    :return
#        the cmd with the credentials injected into
#    """
#    if not credentials:
#        return cmd
#    credentials = ' ' + credentials + ' '
#    return cmd.replace(' ', credentials, 1)



def _get_file_stats(filepath):
    """
    Simply runs os.stat(filepath).

    An easy check to see if a file exists on disk and either return its stats,
    if it is a valid file, or raise an OSError exception.

    :param
        file: local filesystem path to file

    :return
        The stats of a file.
    """
    return os.stat(filepath)


def _chdir_cmd_prefix(git_repo_path):
    """
    Given a file name/path, this function returns "cd <dir> && ",
    where <dir> is the directory where that file resides.
    """
    _get_file_stats(git_repo_path)
    git_repo_path = os.path.abspath(git_repo_path)
    if os.path.isdir(git_repo_path):
        git_repo_dir = git_repo_path
    else:
        git_repo_dir = os.path.dirname(git_repo_path)
    chdir_cmd_prefix = "cd \"%s\" && " % git_repo_dir
    return chdir_cmd_prefix


def _get_github_token():
    """
    Returns the GitHub SSO token that resides in the global .gitconfig.

    :return
        The SSO GitHub Token used with credentails. Otherwise, an empty string.
    """
    global GIT_TOKEN
    if not GIT_TOKEN:
        (status, stdout, stderr) = _run_command(GIT_CONFIG_TOKEN_CMD, shell=True)
        if status == 0:
            GIT_TOKEN = stdout.strip()
        else:
            if not stderr:
                stderr = stdout
            # If stderr is still empty, that means the GIT_CONFIG_TOKEN_CMD returned
            # an empty string.
            if not stderr:
                stderr = "github.token is not setup via git config --global"
            msg = "Failed to get GitHub token password: {0}".format(stderr)
            raise ValueError(msg)
    return GIT_TOKEN


def _get_repo_name():
    """
    Returns the name of the current Git repo.
    """
    return os.path.basename(get_git_root_dir())


def _run_command(cmd, stdout_pipe=subprocess.PIPE, stderr_pipe=subprocess.PIPE, shell=False,
                 split=False, verbose=VERBOSE, credentials=None):
    """
    Uses Popen to run a command

    :param
        cmd: the command to run
        stdout_pipe:
        stderr_pipe:
        shell: bool to determine whether or not to use the shell (environment variables)
        split: bool to split the string into an array of words
        verbose: bool to print extra debug info
        credentials: deprecated

    :return
        status, stdout, stderr (or None, None, None)
    """
    if split:
        cmd = cmd.split()
    try:
        p = subprocess.Popen(cmd, stdout=stdout_pipe, stderr=stderr_pipe, shell=shell)
    except OSError as err:
        print("%s: Failed to execute '%s' because: '%s'" % (type(err).__name__, cmd, err))
        return (None, None, None)
    (stdout, stderr) = p.communicate()
    status = p.poll()
    if verbose:
        if 'password' not in cmd:
            print('command=\t{0}'.format(cmd))
        print('status=\t{0}'.format(status))
        print('stdout=\t{0}'.format(stdout))
        print('stderr=\t{0}'.format(stderr))
    return (status, stdout, stderr)


def _run_command_wrapper(cmd):
    """
    Given a command to execute, this function will call _run_command()
    with 'shell=True' (all other input arguments accepted by that
    function will have their default values) and return stdout if
    successful (or raise ValueError if there is an execution failure).
    """
    (status, stdout, stderr) = _run_command(cmd, shell=True)
    if status != 0:
        if not stderr:
            stderr = stdout
        raise ValueError(stderr)
    return stdout


def _print_checkout_git_progress(checkout_cmd):
    """
    Prints the progress of the checkout_cmd.

    :param
        checkout_cmd: The Git command used to check out a repo.

    :return
        '0': Check out was successful.
        '-1': Check out was unsuccesful.
    """
    final_output = ""
    percentage = 0

    for out in _execute_git_clone_cmd_generator(checkout_cmd):
        if "Filtering content:" in out:
            # Git clone outputs something like:
            # 'Filtering content: X% (X/X), X MiB | X MiB/s, done.'
            # Splitting output to get percentage.
            percentage = int(out.split()[2].replace("%", ""))
            _print_progress_bar(percentage, "Downloading")
            time.sleep(0.2)

    if percentage != 100:
        return -1
    else:
        print("Checkout completed!")
        return 0


def _print_progress_bar(progress_percentage=0, status=''):
    """
    Returns the text image representation of a progress bar.

    :param
        progress_percentage: The integer value of a percentage out of 100
        status: An optional string status to provide extra information of the progress

    :return
        The string that represents a progress bar based on the value,
        progress_percentage.
    """

    # Using '* 0.01' because it's faster than and the same thing as '/ 100'
    filled_len = int(round(PROGRESS_BAR_LENGTH * progress_percentage * 0.01))

    percents = round(100.0 * progress_percentage * 0.01, 1)
    bar = PROGRESS_UNICODE_CHAR * filled_len + NO_PROGRESS_UNICODE_CHAR * (PROGRESS_BAR_LENGTH - filled_len)

    sys.stdout.write('[%s] %s%s -- %s\r' % (bar, progress_percentage, '%', status))
    sys.stdout.flush()


def _execute_git_clone_cmd_generator(clone_cmd):
    """
    A generator that yields output from the git clone clone_cmd.

    :param
        clone_cmd: The 'git clone' command to clone a GitHub repo.

    :yield
        The output from clone_cmd.
    """
    pipe = subprocess.Popen(clone_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            shell=True, universal_newlines=True)
    for stdout_line in iter(pipe.stderr.readline, ""):
        yield stdout_line
    pipe.stderr.close()
    return_code = pipe.poll()
    if return_code != 0:
        raise subprocess.CalledProcessError(return_code, clone_cmd)


