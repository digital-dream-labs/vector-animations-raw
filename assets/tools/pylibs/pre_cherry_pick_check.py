#!/usr/bin/env python

import sys
import os
import stat
import pprint
from audit_anim_clips import TAR_FILE_DIR, unpack_tarball


def main(args):
    tar_file_to_check = args[0]
    orig_tar_file = os.path.join(TAR_FILE_DIR, tar_file_to_check)
    orig_stat = os.stat(orig_tar_file)
    branch_tar_file = os.path.join(os.getcwd(), tar_file_to_check)
    branch_stat = os.stat(branch_tar_file)
    if orig_stat == branch_stat:
        print(os.linesep + "No need to compare %s to %s since they are identical" % (orig_tar_file, branch_tar_file))
        return None
    print(os.linesep + "Comparing %s (%s) to %s (%s)..." % (orig_tar_file, orig_stat.st_size, branch_tar_file, branch_stat.st_size))
    orig_tar_files = unpack_tarball(orig_tar_file)
    branch_tar_files = unpack_tarball(branch_tar_file)
    orig_tar_files = map(lambda x: os.path.basename(x), orig_tar_files)
    branch_tar_files = map(lambda x: os.path.basename(x), branch_tar_files)
    orig_tar_files.sort()
    branch_tar_files.sort()
    if orig_tar_files == branch_tar_files:
        print(os.linesep + "Both tar files contain the same set of animations")
        return None
    orig = set(orig_tar_files)
    branch = set(branch_tar_files)
    added = orig - branch
    removed = branch - orig
    if added:
        added = list(added)
        added.sort()
        print(os.linesep + "Cherry-picking that tar file will ADD these animations:")
        pprint.pprint(added)
    if removed:
        removed = list(removed)
        removed.sort()
        print(os.linesep + "Cherry-picking that tar file will REMOVE these animations:")
        pprint.pprint(removed)
        raise ValueError("Cherry-picking that tar file will REMOVE these animations: %s" % removed)


if __name__ == "__main__":
    main(sys.argv[1:])

