
# This script's main() should be executed by mayapy
# (/Applications/Autodesk/maya2016//Maya.app/Contents/bin/mayapy) NOT from within
# an interactive Maya session.

TOOLS_DIR_ENV_VAR = "ANKI_TOOLS"

import sys
import os
import glob
import stat
import pprint
import maya.standalone
from maya import cmds
from ankimaya import export_for_robot
from ankiutils.anim_files import MAYA_FILE_EXT, OUTPUT_PACKAGE_EXT


def get_files_to_process(args):
    if args is None:
        args = sys.argv
    if args[0] == "-c":
        args = args[1:]
    maya_files = []
    for arg in args:
        expanded_args = glob.glob(arg)
        for expanded_arg in expanded_args:
            if expanded_arg.endswith(MAYA_FILE_EXT):
                maya_files.append(expanded_arg)
    print("maya files = %s" % maya_files)
    return maya_files


def process(maya_file):
    # Redirect output stream to hide verbose output from the export
    sys_stdout = sys.stdout
    dev_null = open(os.devnull, 'w')
    sys.stdout = dev_null

    # Make sure maya_file is writable in case we need to save it, eg. after updating any anim
    # clip names, and stash the last modified time of the file so we know if we had to save it.
    maya_file_stat = os.stat(maya_file)
    os.chmod(maya_file, maya_file_stat.st_mode | stat.S_IWUSR)
    orig_maya_file_mod_time = maya_file_stat.st_mtime

    # Open the maya file and export data
    workspace_root_dir = os.path.dirname(os.getenv(TOOLS_DIR_ENV_VAR))
    cmds.workspace(workspace_root_dir, openWorkspace=True)
    cmds.file(maya_file, open=True, force=True)
    output_files = export_for_robot.export_robot_anim(all_clips=True, save_maya_file=False)

    # Restore output stream after export
    dev_null.close()
    sys.stdout = sys_stdout

    # Return the list of files that should be committed (.tar and .ma files)
    files_to_commit = [str(output_file) for output_file in output_files if output_file.endswith(OUTPUT_PACKAGE_EXT)]
    if orig_maya_file_mod_time != os.stat(maya_file).st_mtime:
        files_to_commit.append(os.path.realpath(maya_file))
    return files_to_commit


def main(args=None):
    files_to_commit = []
    maya_files = get_files_to_process(args)
    if maya_files:
        try:
            maya.standalone.initialize()
        except RuntimeError:
            # no need to initialize() within Maya
            if os.path.basename(sys.executable) != "Maya":
                raise
    for maya_file in maya_files:
        files_to_commit.extend(process(maya_file))
    if files_to_commit:
        print(os.linesep + ("-" * 80) + os.linesep)
        print("Commit the following files to SVN (in Cornerstone):%s%s%s"
              % (os.linesep, pprint.pformat(files_to_commit), os.linesep))


