
# This script's main() should be executed by mayapy
# (/Applications/Autodesk/maya2016//Maya.app/Contents/bin/mayapy) NOT from within
# an interactive Maya session.


SVN_REPO_WITH_MAYA_FILES = "victor-animation"
MAYA_FILE_DIR = "scenes"
SUBDIRS_TO_SKIP = ["lo", "render"]

SET_VERSION_FLAG = "-set_version"
MOCK_FLAG = "-mock"
MAYA_FILE_FLAG = "-maya_file"
ALL_MAYA_FILES_FLAG = "-all_maya_files"
AUDIT_FLAG = "-audit"

TOOLS_DIR_ENV_VAR = "ANKI_TOOLS"


import sys
import os
import pprint
import maya.standalone
from maya import cmds

from ankiutils.anim_files import get_all_maya_files
from ankiutils.svn_tools import get_svn_workspace
import exporter_config


def get_flag_value(args, flag):
    try:
        flag_idx = args.index(flag)
    except ValueError:
        return None
    try:
        flag_value = args[flag_idx + 1]
    except IndexError:
        return None
    else:
        return flag_value


def get_set_version(args, set_version_flag=SET_VERSION_FLAG):
    set_version = get_flag_value(args, set_version_flag)
    try:
        set_version = int(set_version)
    except ValueError:
        return None
    else:
        return set_version


def get_maya_file(args, maya_file_flag=MAYA_FILE_FLAG):
    return get_flag_value(args, maya_file_flag)


def get_maya_files(svn_repo=SVN_REPO_WITH_MAYA_FILES, maya_file_dir=MAYA_FILE_DIR,
                   subdirs_to_skip=SUBDIRS_TO_SKIP):
    filtered_maya_files = []
    svn_workspace = get_svn_workspace()
    maya_files_dir = os.path.join(svn_workspace, svn_repo, maya_file_dir)
    print(os.linesep + "maya_files_dir = %s" % maya_files_dir)
    maya_files = get_all_maya_files(maya_files_dir)
    skip_dirs = map(lambda x: os.path.join(maya_file_dir, x), subdirs_to_skip)
    filtered_out = []
    for maya_file in maya_files:
        for skip_dir in skip_dirs:
            skip_dir = os.sep + skip_dir + os.sep
            if skip_dir in maya_file:
                filtered_out.append(maya_file)
                break
        else:
            filtered_maya_files.append(maya_file)
    return filtered_maya_files


def update_maya_file(maya_file, set_version, update_versions, audit=False, mock=True):
    cmds.file(maya_file, open=True, force=True)
    current_version = exporter_config.getExporterVersion()
    msg = "Exporter version for %s is %s" % (maya_file, current_version)
    if audit:
        msg = "[AUDIT] " + msg
    if mock:
        msg = "[MOCK] " + msg
    print(msg)
    if audit:
        return None
    if current_version in update_versions:
        if mock:
            msg = "Exporter version for %s should be set to %s" % (maya_file, set_version)
            msg = "[MOCK] " + msg
            print(msg)
        else:
            exporter_config.setExporterVersion(set_version)

            # Should we set "force=True" for this save?
            # Probably not since the file may be locked and in use by someone else.
            cmds.file(save=True, type='mayaAscii')

            current_version = exporter_config.getExporterVersion()
            print("Exporter version for %s is NOW %s" % (maya_file, current_version))
    else:
        msg = "Exporter version for %s is STILL %s" % (maya_file, current_version)
        if mock:
            msg = "[MOCK] " + msg
        print(msg)
    return current_version


def main(args=None, update_zero=True, mock_flag=MOCK_FLAG, audit_flag=AUDIT_FLAG):

    final_versions = {}
    problems = {}

    # What current exporter version(s) should be updated to the one being set?
    update_versions = [None]
    if update_zero:
        update_versions.append(0)

    if args is None:
        args = sys.argv[1:]

    mock_mode = mock_flag in args

    audit = audit_flag in args

    # Determine the desired exporter version, which should be an integer
    set_version = get_set_version(args)
    if set_version is None:
        raise ValueError("Unknown exporter version to set in Maya files")
    elif set_version <= 0:
        raise ValueError("Exporter version to set in Maya files must be > 0")

    maya_file = get_maya_file(args)
    if maya_file:
        maya_files = [maya_file]
    elif ALL_MAYA_FILES_FLAG in args:
        maya_files = get_maya_files()
    else:
        raise ValueError("Specify a Maya file to update or pass in %s for all Maya files"
                         % ALL_MAYA_FILES_FLAG)

    # Setup the Maya environment that is required for update_maya_file()
    maya.standalone.initialize()
    workspace_root_dir = os.path.dirname(os.getenv(TOOLS_DIR_ENV_VAR))
    cmds.workspace(workspace_root_dir, openWorkspace=True)

    for maya_file in maya_files:
        if not maya_file:
            continue
        if not os.path.isfile(maya_file):
            problems[maya_file] = "File not found"
            continue
        try:
            current_version = update_maya_file(maya_file, set_version, update_versions, audit, mock_mode)
        except RuntimeError, e:
            problems[maya_file] = str(e).strip()
            continue
        final_versions[maya_file] = current_version

    pprint.pprint(final_versions)

    if problems:
        raise ValueError("Problems detected:" + os.linesep + pprint.pformat(problems))

    return final_versions


