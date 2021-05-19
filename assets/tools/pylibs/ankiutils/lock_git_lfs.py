#!/usr/bin/env python
"""
This is a helper script for Sourcetree to be able to lock/unlock files in Git.
"""

VALID_OPERATIONS = ["lock", "unlock"]


import os
import sys
from git_tools import get_github_username
from git_tools import check_git_file_lock, lock_git_file, unlock_git_file


def display_usage():
   this_script = sys.argv[0]
   usage_msg = "{0} [lock|unlock] <file1> <file2> ...".format(this_script)
   print(usage_msg)


def get_arguments():
    """
    This function will parse sys.argv and return a 2-item tuple of:
        (operation, list_of_files)
    where the 'operation' is either the "lock" or "unlock" string and the
    list of files indicates which file(s) should be locked or unlocked.
    """
    # 0 is name of this script, 1 is the lock or unlock command
    # and everything else is a file to operate on
    operation = sys.argv[1]
    file_list = sys.argv[2:]
    if operation not in VALID_OPERATIONS:
        # the operation should be 'lock' or 'unlock' as defined by the
        # parameters in the Sourcetree custom action
        error_msg = "'{0}'is an invalid operation".format(operation)
        error_msg += " (should be one of {0})".format(str(VALID_OPERATIONS))
        raise ValueError(error_msg)
    return (operation, file_list)


def main():
    try:
        operation, file_list = get_arguments()
    except (ValueError, IndexError):
        display_usage()
        sys.exit(1)

    github_username = get_github_username()

    changed = []
    problems = []
    for filename in file_list:
        lock_owner = check_git_file_lock(filename)

        if lock_owner != None and github_username != lock_owner:
            # file is currently locked by someone else, so the current user cannot lock or unlock it
            msg = "Unable to {0} {1} because {2} has it locked".format(operation, filename, lock_owner)
            problems.append(msg)
            continue

        if operation == 'lock':
            if github_username == lock_owner:
                print("%s is already locked by current user" % filename)
                continue
            try:
                lock_git_file(filename)
            except ValueError, e:
                problems.append(str(e))
            else:
                changed.append(filename)

        elif operation == 'unlock':
            if lock_owner == None:
                print("%s is not locked, so no need to unlock" % filename)
                continue
            try:
                unlock_git_file(filename)
            except ValueError, e:
                problems.append(str(e))
            else:
                changed.append(filename)

    if problems:
        raise ValueError(os.linesep.join(problems))
    elif changed:
        print("{0}ed these files: {1}".format(operation, str(changed)))


if __name__ == "__main__":
    main()


