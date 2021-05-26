
# TODO:
#
# (1) Is there an SVN python API that we should be using here (https://pypi.python.org/pypi/svn
#     for example) instead of shelling out to the SVN CLI?
#
# (2) This module should have an "SvnFile" class with get_version(), get_comment() and get_diff()
#     methods and then much of this logic could move into that.


# Some of this code was borrowed from project/buildScripts/dependencies.py in the cozmo-one git repo
# and some of the settings, eg. user and password, were borrowed from the DEPS file in that repo.


DEFAULT_BRANCH = "trunk"

ROOT_URL = "https://svn.ankicore.com/svn"

SVN_WORKSPACE = "$HOME/workspace"

DEFAULT_VERSION = "head"

VERBOSE = False

TOOL = "svn"

PACKAGING_TOOL = "tar"
PACKAGING_TOOL_OPTIONS = ['-v', '-x', '-z', '-f']

XCODE_BIN_DIR = "/Applications/Xcode.app/Contents/Developer/usr/bin"

DEFAULT_USER = "REDACTED"
PASSWORD = "REDACTED"

SVN_INFO_CMD = "svn info %s %s --xml"
SVN_LOG_CMD  = "svn log -r %s %s"
SVN_DIFF_CMD = "svn diff -r %s %s"
SVN_CHECK_MODIFIED_CMD = "svn status %s | grep -w ^M | wc -l"
SVN_CHECK_OUTDATED_CMD = "svn diff -r BASE:HEAD %s | wc -l"
SVN_MOVE_CMD = "svn move %s %s"
SVN_ADD_DIR_ONLY_ARG = "--depth=empty"
SVN_CRED = "--username %s --password %s --no-auth-cache --non-interactive --trust-server-cert"


import sys
import os
import shutil
import subprocess
import xml.etree.ElementTree as ET
import re
import copy
import time
import uuid


SVN_SIMPLE_DIR = os.path.join(os.getenv('HOME'), ".subversion", "auth", "svn.simple")


def is_up(url_string=ROOT_URL):
    """
    Checks to see if the SVN server is online
    :param url_string: the url of the server
    :return: true: if the server is reachable
    :return: false: if the server is not reachable
    """
    import urllib2
    try:
        urllib2.urlopen(url_string)
        return True
    except urllib2.HTTPError, e:
        if e.code == 401:
            # Authentication error site is up and requires login.
            return True
        print('is_up error: {0}'.format(e.code))
        return False
    except urllib2.URLError, e:
        return False


def _inject_credentials(cmd, credentials=None):
    """
    Given an SVN command and credentials, inject the credentials into the command
    :param cmd: SVN command to execute
    :param credentials: SVN credentials in the form of "--username USER --password XXXXXXXX"
    :return: the cmd with the credentials injected into
    """
    if not credentials:
        return cmd
    credentials = ' ' + credentials + ' '
    return cmd.replace(' ', credentials, 1)


def _run_command(cmd, stdout_pipe=subprocess.PIPE, stderr_pipe=subprocess.PIPE,
                 shell=False, split=False, verbose=VERBOSE, credentials=None):
    """
    Uses Popen to run a command
    :param cmd: the command to run
    :param stdout_pipe:
    :param stderr_pipe:
    :param shell: bool to determine whether or not to use the shell (environment variables)
    :param split: bool to split the string into an array of words
    :param verbose: bool to print extra debug info
    :param credentials: optional string with a username and password
    :return: status, stdout, stderr (or None, None, None)
    """
    cmd = _inject_credentials(cmd, credentials)
    if split:
        cmd = cmd.split()
    try:
        p = subprocess.Popen(cmd, stdout=stdout_pipe, stderr=stderr_pipe, shell=shell,
                             env=get_env_vars_for_svn())
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


def check_for_user_match(user_name, search_dir=SVN_SIMPLE_DIR):
    """
    Given an svn username, this function will look in
    $HOME/.subversion/auth/svn.simple/ to see if that is the current
    user and return True if the users match, else return False.
    :param user_name: svn username to look in up svn.simple credentials
    :param search_dir: directory of svn.simple
    :return: bool: true if the users match, false if they do not
    """
    cmd = "grep -r {0} {1}".format(user_name, search_dir)
    (status, stdout, stderr) = _run_command(cmd, shell=True)
    if status == 0:
        # one or more lines were selected, so user_name matches current svn user
        return True
    elif status == 1:
        # no lines were selected, so user_name does NOT match current svn user
        return False
    else:
        # an error occurred so UNKNOWN if user_name matches current svn user
        return None


def get_commit_info(file_path, raise_on_fail=True):
    file_name = os.path.basename(file_path)
    if os.path.isfile(file_path):
        file_ver = get_svn_file_rev(file_path, raise_on_fail=raise_on_fail)
    else:
        file_ver = None

    # TODO: Figure out why get_svn_comment() was hanging for Mooly Segal on
    # 5/23/2016 and then re-enable this functionality to get comments.
    #comment_lines = get_svn_comment(file_path, file_ver)
    comment_lines = []

    return (file_name, file_ver, comment_lines)


def get_env_vars_for_svn(path_var="PATH", xcode_bin=XCODE_BIN_DIR):

    # We do NOT currently want to use the svn command-line tool that is provided by Xcode
    xcode_bin = None

    # Prepend /usr/local/bin/ to $PATH since a few users have a newer (and
    # compatible) installation of the svn command-line tool installed there
    # (/usr/local/bin/svn is v1.9 and seems to work, but /usr/bin/svn is v1.7
    #  and doesn't allow this script to work on their machines).
    usr_local_bin = "/usr/local/bin"
    env_vars = copy.copy(os.environ)
    if xcode_bin and os.path.isdir(xcode_bin):
        if not env_vars[path_var].startswith(xcode_bin + os.pathsep):
            env_vars[path_var] = xcode_bin + os.pathsep + env_vars[path_var]
    if not env_vars[path_var].startswith(usr_local_bin + os.pathsep):
        env_vars[path_var] = usr_local_bin + os.pathsep + env_vars[path_var]
    return env_vars


def rename_svn_file(src, dst):
    """
    Given an SVN file, this will rename the file in the same directory.
    A temporary intermediate file is used in case we are simply trying
    to change the case of the name on a Mac.
    """
    dir_name = os.path.dirname(src)
    file_ext = os.path.splitext(src)[1]

    temp_file = str(uuid.uuid4())
    temp_file = os.path.join(dir_name, temp_file)

    dst = os.path.basename(dst)
    dst = os.path.join(dir_name, dst)
    if not dst.endswith(file_ext):
        dst += file_ext

    svn_move_cmd = SVN_MOVE_CMD % (src, temp_file)
    #print("Running: %s" % svn_move_cmd)
    p = subprocess.Popen(svn_move_cmd.split(), stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, env=get_env_vars_for_svn())
    (stdout, stderr) = p.communicate()
    status = p.poll()
    if status != 0:
        raise RuntimeError("Failed to move %s to %s" % (src, temp_file))

    svn_move_cmd = SVN_MOVE_CMD % (temp_file, dst)
    #print("Running: %s" % svn_move_cmd)
    p = subprocess.Popen(svn_move_cmd.split(), stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, env=get_env_vars_for_svn())
    (stdout, stderr) = p.communicate()
    status = p.poll()
    if status != 0:
        raise RuntimeError("Failed to move %s to %s" % (temp_file, dst))


def get_svn_file_rev(file_from_svn, cred='', raise_on_fail=False):
    """
    Given a file that was checked out from SVN, this function will
    return the revision of that file in the form of an integer. If
    the revision cannot be determined, this function returns None.
    """
    svn_info_cmd_vars = [cred, file_from_svn]
    if ' ' in file_from_svn:
        svn_info_cmd = []
        for cmd_parts in SVN_INFO_CMD.split():
            if cmd_parts == "%s":
                try:
                    cmd_parts = svn_info_cmd_vars.pop(0)
                except IndexError:
                    cmd_parts = ''
            if cmd_parts:
                svn_info_cmd.append(cmd_parts)
    else:
        svn_info_cmd = SVN_INFO_CMD % tuple(svn_info_cmd_vars)
        svn_info_cmd = svn_info_cmd.split()
    #print("Running: %s" % svn_info_cmd)
    p = subprocess.Popen(svn_info_cmd, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, env=get_env_vars_for_svn())
    (stdout, stderr) = p.communicate()
    status = p.poll()
    if status != 0:
        if raise_on_fail:
            raise RuntimeError("Unable to determine the SVN version of %s because:%s"
                               % (file_from_svn, os.linesep + stderr))
        else:
            return None
    root = ET.fromstring(stdout.strip())
    for entry in root.iter('entry'):
        try:
            rev = entry.find("commit").attrib['revision']
        except (KeyError, AttributeError):
            pass
        else:
            rev = int(rev)
            return rev


def get_svn_comment(svn_file, rev):
    file_stats = os.stat(svn_file)
    svn_log_cmd = SVN_LOG_CMD % (rev, svn_file)
    #print("Running: %s" % svn_log_cmd)
    p = subprocess.Popen(svn_log_cmd.split(), stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, env=get_env_vars_for_svn())
    (stdout, stderr) = p.communicate()
    status = p.poll()
    if status != 0:
        raise RuntimeError("Unable to determine the SVN commit comment for %s "
                           "(version %s) because:%s" % (svn_file, rev, os.linesep + stderr))
    comment_lines = stdout.split(os.linesep)[3:-2]
    return comment_lines


def check_svn_file_modified(svn_file):
    """
    This function can be used to determine if the local version
    of a file is modified.
    """
    file_stats = os.stat(svn_file)
    svn_check_modified_cmd = SVN_CHECK_MODIFIED_CMD % svn_file
    #print("Running: %s" % svn_check_modified_cmd)
    p = subprocess.Popen(svn_check_modified_cmd, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, env=get_env_vars_for_svn(), shell=True)
    (stdout, stderr) = p.communicate()
    status = p.poll()
    if status != 0:
        raise RuntimeError("Unable to check if the local version of %s is modified because:%s"
                           % (svn_file, os.linesep + stderr))
    num_modified_lines = int(stdout.strip())
    if num_modified_lines == 0:
        return False
    else:
        return True


def check_svn_file_outdated(svn_file):
    """
    This function can be used to determine if the local version
    of a file is outdated, i.e. if a version of this file has
    been committed since the local version was last updated.
    """
    file_stats = os.stat(svn_file)
    svn_check_outdated_cmd = SVN_CHECK_OUTDATED_CMD % svn_file
    #print("Running: %s" % svn_check_outdated_cmd)
    p = subprocess.Popen(svn_check_outdated_cmd, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, env=get_env_vars_for_svn(), shell=True)
    (stdout, stderr) = p.communicate()
    status = p.poll()
    if status != 0:
        raise RuntimeError("Unable to check if the local version of %s is outdated because:%s"
                           % (svn_file, os.linesep + stderr)) 
    num_diff_lines = int(stdout.strip())
    if num_diff_lines == 0:
        return False
    else:
        return True


def get_svn_diff(svn_file, rev, timeout=10):
    file_stats = os.stat(svn_file)
    svn_diff_cmd = SVN_DIFF_CMD % ((rev-1), svn_file)
    #print("Running: %s" % svn_diff_cmd)
    p = subprocess.Popen(svn_diff_cmd.split(), stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, env=get_env_vars_for_svn())
    status = None
    timer = 0
    while status is None and timer < timeout:
        time.sleep(1)
        timer += 1
        status = p.poll()
    if status is None:
        stdout = ""
        stderr = "timeout"
    else:
        (stdout, stderr) = p.communicate()
    if status != 0:
        print("Unable to determine the SVN diff for %s because:%s"
              % (svn_file, os.linesep + stderr))
        return None
    diff_lines = stdout.split(os.linesep)
    return diff_lines


def get_svn_workspace(svn_workspace=SVN_WORKSPACE):
    workspace_parts = svn_workspace.split(os.sep)
    for idx in range(len(workspace_parts)):
        part = workspace_parts[idx]
        if part.startswith("$"):
            part = os.getenv(part[1:])
            workspace_parts[idx] = part
    return os.sep.join(workspace_parts)


def get_svn_file_path(file_url, svn_workspace):
    # Given the URL for an SVN file, this function should return the corresponding file on disk.
    local_file_path = file_url.replace(ROOT_URL, svn_workspace)
    if not os.path.isfile(local_file_path) and DEFAULT_BRANCH in local_file_path:
        local_file_path = local_file_path.replace(DEFAULT_BRANCH, "")
    return local_file_path


def checkout_svn_package(pkg_name, repo, dest, branch=DEFAULT_BRANCH, root_url=ROOT_URL,
                         version=DEFAULT_VERSION, user=DEFAULT_USER, password=PASSWORD,
                         verbose=VERBOSE, tool=TOOL, ptool=PACKAGING_TOOL,
                         ptool_options=PACKAGING_TOOL_OPTIONS):
    """
    This function can be used to checkout a package from SVN.
    """
    if not is_up(root_url):
        raise ValueError("{0} is not available; check your network and VPN connections".format(root_url))

    cred = SVN_CRED % (user, password)
    url = os.path.join(root_url, repo, branch)
    checkout = [tool, 'checkout', '-r', '{0}'.format(version)] + cred.split() + [url, dest]
    cleanup = [tool, 'status', '--no-ignore'] + cred.split() + [dest]
    if pkg_name:
        package = os.path.join(dest, pkg_name)
        unpack = [ptool] + ptool_options + [package, '-C', dest]
    else:
        package = None
    l_rev = 'unknown'

    if l_rev != 0 and os.path.isdir(dest):
        l_rev = get_svn_file_rev(dest, cred)
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
    #print("Running: %s" % ' '.join(checkout))
    pipe = subprocess.Popen(checkout, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = pipe.communicate()
    status = pipe.poll()
    if stderr == '' and status == 0:
        return_val = stdout.strip()
        print(return_val)
        # Equivalent to a git clean
        pipe = subprocess.Popen(cleanup, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        extract_message, error = pipe.communicate()
        if extract_message != '':
            last_column = re.compile(r'\S+\s+(\S+)')
            unversioned_files = last_column.findall(extract_message)
            for a_file in unversioned_files:
                if os.path.isdir(a_file):
                    shutil.rmtree(a_file)
                elif os.path.isfile(a_file):
                    os.remove(a_file)
        if package:
            if os.path.isfile(package):
                # call waits for the result.  Moving on to the next checkout doesnt need this to finish.
                pipe = subprocess.Popen(unpack, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                if verbose:
                    stdout, stderr = pipe.communicate()
                    print(stderr)
            else:
                raise ValueError("Error in checking out {0}: {1}".format(repo, stderr.strip()))
        return return_val
    else:
        raise ValueError(stderr.strip())
        #print("{0} does not need to be updated.  Current {1} revision at {2} ".format(repo, tool, l_rev))


def add_svn_file(file_for_svn, credentials=None, args=None):
    """
    Adds a file to the SVN server.  Returns nothing if file is already under SVN control
    :param file_for_svn: local file system path to the file to add
    :param credentials: username and password, if necessary
    """
    file_stats = os.stat(file_for_svn)
    if check_file_in_svn(file_for_svn):
        msg = "The {0} file is already under version control".format(os.path.basename(file_for_svn))
        print(msg)
        return
    dirname = os.path.dirname(file_for_svn)
    if not check_file_in_svn(dirname):
        add_svn_file(dirname, credentials, SVN_ADD_DIR_ONLY_ARG)
        comment = "Adding directory to SVN: " + os.path.basename(dirname)
        commit_svn_file(dirname, comment, unlock=True, credentials=credentials)
    if args:
        cmd = "svn add {0} {1}".format(args, file_for_svn)
    else:
        cmd = "svn add {0}".format(file_for_svn)
    (status, stdout, stderr) = _run_command(cmd, shell=False, split=True, credentials=credentials)
    if status == 0:
        print("Added '{0}' file to SVN".format(file_for_svn))
    else:
        if not stderr:
            stderr = stdout
        msg = "Failed to add '{0}' file to SVN because: {1}".format(file_for_svn, stderr)
        raise ValueError(msg)


def update_svn_file(file_in_svn, credentials=None):
    file_stats = os.stat(file_in_svn)
    if not check_file_in_svn(file_in_svn):
        msg  = "The {0} file is not yet under version control".format(os.path.basename(file_in_svn))
        msg += ", so no need to update it"
        print(msg)
        return
    cmd = "svn update {0}".format(file_in_svn)
    (status, stdout, stderr) = _run_command(cmd, shell=False, split=True, credentials=credentials)
    if status == 0:
        rev_info = stdout.split(os.linesep)[1].rstrip('.')
        print("Updated '{0}' file ({1})".format(file_in_svn, rev_info.lower()))
    else:
        if not stderr:
            stderr = stdout
        msg = "Failed to update '{0}' file because: {1}".format(file_in_svn, stderr)
        raise ValueError(msg)


def check_file_never_committed(file_to_check, schedule_prefix="Schedule", info_delimiter=":",
                               credentials=None):
    file_stats = os.stat(file_to_check)
    cmd = "svn info {0}".format(file_to_check)
    (status, stdout, stderr) = _run_command(cmd, shell=False, split=True, credentials=credentials)
    if status == 0:
        #print("File '{0}' is already under version control".format(file_to_check))
        schedule = None
        schedule_prefix += info_delimiter
        output_lines = stdout.split(os.linesep)
        for output_line in output_lines:
            if output_line.startswith(schedule_prefix):
                schedule = output_line[len(schedule_prefix):]
                schedule = schedule.strip()
                break
        if not schedule:
            raise RuntimeError("Unable to determine status of {0}".format(file_to_check))
        else:
            if schedule in ["add"]:
                return True
            else:
                return False
    else:
        if not stderr:
            stderr = stdout
        if "155010" in stderr or "200009" in stderr or "was not found" in stderr or "some targets don't exist" in stderr:
            # file is not under version control
            #print("File '{0}' is not under version control".format(file_to_check))
            return True
        else:
            raise RuntimeError(stderr)


def check_file_in_svn(file_to_check, credentials=None):
    """
    Checks to see if a file is already under version control
    :param file_to_check: local file system path to file
    :param credentials: optional username and password
    :return: true if the file is in SVN, false if the file is not in SVN
    """
    file_stats = os.stat(file_to_check)
    cmd = "svn info {0}".format(file_to_check)
    (status, stdout, stderr) = _run_command(cmd, shell=False, split=True, credentials=credentials)
    if status == 0:
        #print("File '{0}' is already under version control".format(file_to_check))
        return True
    else:
        if not stderr:
            stderr = stdout
        if "155007" in stderr or "155010" in stderr or "200009" in stderr \
                or "not a working copy" in stderr or "was not found" in stderr \
                or "some targets don't exist" in stderr:
            # file is not under version control
            #print("File '{0}' is not under version control".format(file_to_check))
            return False
        else:
            raise RuntimeError(stderr)


def get_svn_file_url(file_in_svn, url_prefix="URL", info_delimiter=":", credentials=None):
    """
    Gets the remote URL of a local file under SVN version control
    :param file_in_svn: local file system path to file
    :param url_prefix:
    :param info_delimiter:
    :param credentials: optional username and password
    :return: remote URL of file
    """
    file_stats = os.stat(file_in_svn)
    cmd = "svn info {0}".format(file_in_svn)
    (status, stdout, stderr) = _run_command(cmd, shell=True, credentials=credentials)
    if status == 0:
        url = None
        url_prefix += info_delimiter
        output_lines = stdout.split(os.linesep)
        for output_line in output_lines:
            if output_line.startswith(url_prefix):
                url = output_line[len(url_prefix):]
                url = url.strip()
                return url
    else:
        if not stderr:
            stderr = stdout
        msg = "Failed to get svn info for '{0}' file because: {1}".format(file_in_svn, stderr)
        raise ValueError(msg)


def check_svn_file_lock_local(file_in_svn, lock_owner_prefix="Lock Owner", info_delimiter=":"):
    return check_svn_file_lock(file_in_svn, lock_owner_prefix, info_delimiter, remote=False)


def check_svn_file_lock(file_in_svn, lock_owner_prefix="Lock Owner", info_delimiter=":", remote=True):
    """
    It's probably best to check the lock on the server, so we first
    get the file URL from the file's svn info and then check that
    remote file for an SVN lock. You can set 'remote' to False to
    check the local file for an SVN lock.
    :param file_in_svn: local file system path to file already in SVN
    :param lock_owner_prefix: string to search for in return message
    :param info_delimiter:
    :param remote: bool to query remote server or local server for finding a file lock
    """
    file_stats = os.stat(file_in_svn)
    credentials = SVN_CRED % (DEFAULT_USER, PASSWORD)
    if remote:
        try:
            url = get_svn_file_url(file_in_svn, credentials=credentials)
        except ValueError, e:
            print(e)
        else:
            if url:
                file_in_svn = url
    cmd = "svn info {0}".format(file_in_svn)
    (status, stdout, stderr) = _run_command(cmd, shell=True, credentials=credentials)
    if status == 0:
        lock_owner = None
        lock_owner_prefix += info_delimiter
        output_lines = stdout.split(os.linesep)
        for output_line in output_lines:
            if output_line.startswith(lock_owner_prefix):
                lock_owner = output_line[len(lock_owner_prefix):]
                lock_owner = lock_owner.strip()
                return lock_owner
    else:
        if not stderr:
            stderr = stdout
        msg = "Failed to get svn info for '{0}' file because: {1}".format(file_in_svn, stderr)
        raise ValueError(msg)


def lock_svn_file(file_in_svn, credentials=None):
    """
    This function can be used to lock an SVN file using these steps:
     - abort if the file is not under version control yet
     - abort if the current user already has the file locked
     - raise IOError if a different user already has the file locked
     - svn lock the file
     :param file_in_svn: local filesystem path
     :param credentials: optional username and password
    """
    file_stats = os.stat(file_in_svn)
    if not check_file_in_svn(file_in_svn, credentials=credentials):
        msg = "The {0} file is not yet under version control".format(os.path.basename(file_in_svn))
        msg += ", so no need to lock it"
        print(msg)
        return
    lockOwner = check_svn_file_lock(file_in_svn)
    if lockOwner:
        msg = "The {0} file is locked by {1}".format(os.path.basename(file_in_svn), lockOwner)
        print(msg)
        if not check_for_user_match(lockOwner):
            raise IOError(msg)
    else:
        cmd = "svn lock {0}".format(file_in_svn)
        (status, stdout, stderr) = _run_command(cmd, shell=True, credentials=credentials)
        if status == 0:
            print("Locked '{0}' file in SVN".format(file_in_svn))
        else:
            if not stderr:
                stderr = stdout
            msg = "Failed to lock '{0}' file in SVN because: {1}".format(file_in_svn, stderr)
            raise ValueError(msg)


def unlock_svn_file(file_in_svn, credentials=None):
    """
    Unlocks a file in SVN
    :param file_in_svn: local file system path
    :param credentials: optional username and password
    """
    file_stats = os.stat(file_in_svn)
    if not check_file_in_svn(file_in_svn, credentials=credentials):
        msg  = "The {0} file is not yet under version control".format(os.path.basename(file_in_svn))
        msg += ", so no need to unlock it"
        print(msg)
        return
    cmd = "svn unlock {0}".format(file_in_svn)
    (status, stdout, stderr) = _run_command(cmd, shell=True, credentials=credentials)
    if status == 0:
        print("Unlocked '{0}' file in SVN".format(file_in_svn))
    else:
        if not stderr:
            stderr = stdout
        if "195013" in stderr or "not locked in this working copy" in stderr:
            # file is not locked in this working copy
            print("No need to unlock '{0}' file in SVN".format(file_in_svn))
        else:
            msg = "Failed to unlock '{0}' file in SVN because: {1}".format(file_in_svn, stderr)
            raise ValueError(msg)


def commit_svn_file(file_in_svn, comment, unlock=True, credentials=None):
    """Commits a file that may or may not already be under SVN version control
    :param file_in_svn: local filesystem path to file
    :param comment: mandatory comment message for SVN
    :param unlock: bool to unlock after commiting
    :param credentials: optional username and password
    :return: returns the revision number of the commit transaction
    """
    file_stats = os.stat(file_in_svn)
    if not check_file_in_svn(file_in_svn, credentials=credentials):
        add_svn_file(file_in_svn, credentials=credentials)

    # strip out any double-quotes from the comment
    comment = comment.replace('"', '')

    cmd = 'svn commit {0} -m "{1}"'.format(file_in_svn, comment)
    if not unlock:
        cmd += " --no-unlock"

    (status, stdout, stderr) = _run_command(cmd, shell=True, credentials=credentials)

    if status == 0:
        # Lookup and return the rev number if file was successfully committed
        rev_number = get_svn_file_rev(file_in_svn)
        print("Committed {0} revision {1} ".format(file_in_svn, rev_number))
        return rev_number
    else:
        if not stderr:
            stderr = stdout
        msg = "Failed to commit '{0}' file to SVN because: {1}".format(file_in_svn, stderr)
        raise ValueError(msg)


