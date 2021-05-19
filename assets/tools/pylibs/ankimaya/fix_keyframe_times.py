
# This script's main() should be executed by mayapy
# (/Applications/Autodesk/maya2016//Maya.app/Contents/bin/mayapy) NOT from within
# an interactive Maya session.

# If a keyframe time is not a whole number but close to a whole number, where "close"
# is less than this value, then the keyframe will be moved to that whole number time.
MAX_DELTA = 0.09

AUDIO_NODE = "x:AnkiAudioNode"
EVENT_NODE = "x:event_ctrl"
NODES_TO_FIX = [AUDIO_NODE, EVENT_NODE]

MAYA_VERSION_TO_PROCESS = "2018"

TOOLS_DIR_ENV_VAR = "ANKI_TOOLS"


import sys
import os
import glob
import stat
import pprint
import maya.standalone
from maya import cmds
from ankiutils.anim_files import MAYA_FILE_EXT


def get_files_to_process(args, version=MAYA_VERSION_TO_PROCESS):
    if args is None:
        args = sys.argv
    if args[0] == "-c":
        args = args[1:]
    maya_files = []
    for arg in args:
        expanded_args = glob.glob(arg)
        for expanded_arg in expanded_args:
            if expanded_arg.endswith(MAYA_FILE_EXT):
                if not version or check_version_match(version, expanded_arg):
                    maya_files.append(expanded_arg)
    print("maya files = %s" % maya_files)
    return maya_files


def check_version_match(version, maya_file):
    fh = open(maya_file, 'r')
    maya_file_version = fh.readlines()[0]
    fh.close()
    if version in maya_file_version:
        return True
    else:
        print("%s file does not match version %s" % (maya_file, version))
        return False


def move_keyframes_to_int_times(node, mock=True):
    if not cmds.objExists(node):
        return []
    cmds.select(node, replace=True)
    try:
        keyframes = cmds.keyframe(node, query=True)
    except ValueError:
        print("WARNING: Unable to get keyframe times for %s" % node)
        return []
    if not keyframes:
        print("INFO: There are no %s keyframes" % node)
        return []
    moved = []
    for keyframe in keyframes:
        if keyframe in moved:
            # this keyframe was already moved
            continue
        fixed_time = round(keyframe)
        if keyframe == fixed_time:
            # this keyframe is good, no need to move it
            continue
        elif abs(keyframe - fixed_time) > MAX_DELTA:
            print("INFO: The %s keyframe at %s is not close enough to %s to be moved there"
                  % (node, keyframe, fixed_time))
            continue
        move_error_msg_part = "move %s keyframe from %s to %s" % (node, keyframe, fixed_time)
        if fixed_time in keyframes:
            print("ERROR: Unable to %s because there is already a keyframe at that time"
                  % move_error_msg_part)
            continue
        move_msg = "ACTION: %s has a keyframe at %s that %s be moved to %s"
        if mock:
            print(move_msg % (node, keyframe, "should", fixed_time))
        else:
            print(move_msg % (node, keyframe, "will", fixed_time))
            try:
                num_curves = cmds.keyframe(time=(keyframe,keyframe), absolute=True,
                                           timeChange=fixed_time)
            except RuntimeError, e:
                print("ERROR: Failed to %s because: %s" % (move_error_msg_part, str(e).strip()))
            #else:
            #    print("(number of curves on which keys were modified = %s)" % num_curves)
        moved.append(keyframe)
    return moved


def process(maya_file, mock=True):
    # Make sure maya_file is writable in case we need to save it, eg. after updating any anim
    # clip names, and stash the last modified time of the file so we know if we had to save it.
    maya_file_stat = os.stat(maya_file)
    os.chmod(maya_file, maya_file_stat.st_mode | stat.S_IWUSR)
    orig_maya_file_mod_time = maya_file_stat.st_mtime

    # Open the maya file
    workspace_root_dir = os.path.dirname(os.getenv(TOOLS_DIR_ENV_VAR))
    cmds.workspace(workspace_root_dir, openWorkspace=True)
    cmds.file(maya_file, open=True, force=True)

    # Fix the keyframe times to be integers for the audio node and event ctrl node
    fixed = 0
    for node in NODES_TO_FIX:
        moved = move_keyframes_to_int_times(node, mock)
        fixed += len(moved)

    # Save the maya file if it was modified
    if not mock and fixed > 0:
        cmds.file(save=True, force=True, type="mayaAscii")

    # Return the .ma file that should be committed if it was modified
    if orig_maya_file_mod_time != os.stat(maya_file).st_mtime:
        return os.path.realpath(maya_file)


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
        files_to_commit.append(process(maya_file))
    while None in files_to_commit:
        files_to_commit.remove(None)
    if files_to_commit:
        print(os.linesep + ("-" * 80) + os.linesep)
        print("Commit the following files to SVN (in Cornerstone):%s%s%s"
              % (os.linesep, pprint.pformat(files_to_commit), os.linesep))


