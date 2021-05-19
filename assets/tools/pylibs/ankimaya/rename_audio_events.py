
# This script's main() should be executed by mayapy
# (/Applications/Autodesk/maya2016//Maya.app/Contents/bin/mayapy) NOT from within
# an interactive Maya session.

STRING_TO_REPLACE_FLAG = "-replace"

REPLACEMENT_STRING_FLAG = "-with"

EXPORT_FLAG = "-export"

TOOLS_DIR_ENV_VAR = "ANKI_TOOLS"

HELP_FLAGS = ["-h", "--h", "-help", "--help"]

USAGE_MSG = """
rename_maya_audio_events.sh %s <string_to_replace> %s <replacement_string> [%s] <maya_file> [<maya_file>] ...

If the optional %s flag is provided, then the animation data will
be exported after renaming IF any audio events were in fact renamed.
""" % (STRING_TO_REPLACE_FLAG, REPLACEMENT_STRING_FLAG, EXPORT_FLAG, EXPORT_FLAG)


import sys
import os
import glob
import stat
import pprint
import maya.standalone
from maya import cmds
from ankimaya import export_for_robot, audio_core
from ankiutils.anim_files import MAYA_FILE_EXT, OUTPUT_PACKAGE_EXT


def separate_input(args):
    string_to_replace = None
    replacement_string = None
    maya_files = []
    export = False
    if args is None:
        args = sys.argv
    idx = 0
    while idx < len(args):
        arg = args[idx]
        if arg in ["-c"]:
            idx += 1
        elif arg in HELP_FLAGS:
            print(USAGE_MSG)
            sys.exit(0)
        elif arg == EXPORT_FLAG:
            export = True
            idx += 1
        elif arg == STRING_TO_REPLACE_FLAG:
            try:
                string_to_replace = args[idx+1]
            except IndexError:
                string_to_replace = None
            idx += 2
        elif arg == REPLACEMENT_STRING_FLAG:
            try:
                replacement_string = args[idx+1]
            except IndexError:
                replacement_string = None
            idx += 2
        else:
            expanded_args = glob.glob(arg)
            for expanded_arg in expanded_args:
                if expanded_arg.endswith(MAYA_FILE_EXT):
                    maya_files.append(expanded_arg)
            idx += 1
    print("string to replace = %s" % string_to_replace)
    print("replacement string = %s" % replacement_string)
    print("maya files = %s" % maya_files)
    print("export = %s" % export)
    return (string_to_replace, replacement_string, maya_files, export)


def process(string_to_replace, replacement_string, maya_file, export=False):
    files_to_commit = []

    # Make sure maya_file is writable in case we need to save it (if any audio event names are updated).
    maya_file_stat = os.stat(maya_file)
    os.chmod(maya_file, maya_file_stat.st_mode | stat.S_IWUSR)

    # Open the maya file
    workspace_root_dir = os.path.dirname(os.getenv(TOOLS_DIR_ENV_VAR))
    cmds.workspace(workspace_root_dir, openWorkspace=True)
    cmds.file(maya_file, open=True, force=True)
    print("Opened maya file: %s" % maya_file)

    # Select the audio node and then call audio_core.setupEnumAttr() with the rename mapping.
    cmds.select(audio_core.AUDIO_NODE_NAME)
    eventNamesSorted, audioIds = audio_core.loadAudioAttrs()
    num_events_renamed = audio_core.setupEnumAttr(eventNamesSorted,
                                            renameMapping={string_to_replace : replacement_string})
    print("Renamed %s audio events in %s" % (num_events_renamed, maya_file))

    if num_events_renamed:
        # If any events were renamed, then we need to save the Maya file and
        # commit it. We may also want to export anim data and commit the
        # resulting tar files if any events were renamed.
        files_to_commit.append(os.path.realpath(maya_file))
        if export:
            files_to_commit.extend(export_anim())
        cmds.file(force=True, type='mayaAscii', save=True)

    return files_to_commit


def export_anim():
    # Redirect output stream to hide verbose output from the export
    sys_stdout = sys.stdout
    dev_null = open(os.devnull, 'w')
    sys.stdout = dev_null

    output_files = export_for_robot.export_robot_anim(all_clips=True, save_maya_file=False)

    # Restore output stream after export
    dev_null.close()
    sys.stdout = sys_stdout

    # Return the list of tar files that was generated by export
    tar_files = [str(output_file) for output_file in output_files if output_file.endswith(OUTPUT_PACKAGE_EXT)]
    return tar_files


def main(args=None):
    files_to_commit = []
    string_to_replace, replacement_string, maya_files, export = separate_input(args)
    if string_to_replace == replacement_string and string_to_replace is not None:
        print("The replacement string is identical to the string to replace")
        maya_files = []
    elif maya_files:
        maya.standalone.initialize()
    else:
        print("No maya file(s) specified for renaming audio events")
    for maya_file in maya_files:
        files_to_commit.extend(process(string_to_replace, replacement_string, maya_file, export))
    if files_to_commit:
        print(os.linesep + ("-" * 80) + os.linesep)
        print("Commit the following files to SVN (in Cornerstone):%s%s%s"
              % (os.linesep, pprint.pformat(files_to_commit), os.linesep))


