"""
This is a setup file for Maya that will be invoked whenever Maya is launched.
"""

PLUGINS_TO_AUTOLOAD = ["AnkiMenu.py"]

TOOLS_ENV_VAR = "ANKI_TOOLS"


import sys
import os
from maya import cmds
from ankimaya.scene_file_mgmt import openSceneFile
from ankimaya.scene_callbacks import addSceneOpenedScriptJob


def runShelfOptions():
    """
    This optionVar sets Shelf Editor->Options->Save Only on Request
    """
    cmds.optionVar(iv=("isShelfSave", 0))


def loadPlugins(plugins=PLUGINS_TO_AUTOLOAD):
    for plugin in plugins:
        cmds.evalDeferred("cmds.loadPlugin('%s')" % plugin)


def setProjectWorkspace():
    workspaceDir = os.path.dirname(os.getenv(TOOLS_ENV_VAR))
    cmds.workspace(workspaceDir, o=True)


def main():
    runShelfOptions()
    loadPlugins()
    setProjectWorkspace()
    addSceneOpenedScriptJob(openSceneFile)


main()


