
import os
import subprocess
import maya.cmds as cmds


EXPORT_PATH_ENV_VAR = "ANKI_ANIM_EXPORT_PATH"


def getExportDir(exportPathEnvVar=EXPORT_PATH_ENV_VAR):
    exportDir = os.getenv(exportPathEnvVar)
    if not exportDir:
        msg = "Unable to determine export directory from %s setting" % exportPathEnvVar
        cmds.warning(msg)
    elif not os.path.isdir(exportDir):
        msg = "%s animation export directory does not exist (yet)" % exportDir
        cmds.warning(msg)
    return exportDir


def openAnimExportDir(exportDir=None):
    if not exportDir:
        exportDir = getExportDir()
    if not exportDir:
        msg = "Animation export directory is unknown"
        cmds.warning(msg)
    elif not os.path.isdir(exportDir):
        msg = "%s animation export directory does not exist (yet)" % exportDir
        cmds.warning(msg)
    else:
        openDirectory(exportDir)


def openDirectory(dirToOpen, reveal=False):
    openDirCmd = ["open", dirToOpen]
    if reveal:
        openDirCmd.append("-R")
    try:
        subprocess.call(openDirCmd)
    except StandardError, e:
        msg = "Unable to open %s folder because: %s" % (dirToOpen, e)
        cmds.warning(msg)


