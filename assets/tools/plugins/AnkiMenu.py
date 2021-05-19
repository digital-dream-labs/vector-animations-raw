
import sys
import os
import maya.OpenMaya as OpenMaya
import maya.OpenMayaMPx as OpenMayaMPx
import maya.cmds as cmds
import maya.mel as mel
from functools import partial
import ankimaya.json_exporter as je
from ankimaya.audio_core import setupAudioNode
from ankimaya.game_exporter import open_json
from ankimaya.export_for_robot import exportRobotAnim, verify_export_path, set_export_path


# To setup script follow instructions in SVN: https://svn.ankicore.com/svn/cozmo-animation/trunk/tools/other/readme.txt
# In Maya, click Windows -> Setting/Preferences -> Plug-In Manager and click "Loaded" and "Auto load"
# for the "AnkiMenu.py" plugin. An "Anki" menu will appear in the main Maya menu bar.


kPluginCmdName = "AnkiAnimExport"
kOpenJsonShortFlagName = "oj"
kOpenJsonLongFlagName = "open_json"
kAudioShortFlagName = "a"
kAudioLongFlagName = "audio"

g_PrevMenuName = ""
g_ClipWindow = None
g_SBLabelElement = None


def SBDirChanged(btn_id, *args):
    # Set working directory to be what you clicked on...
    mel.eval("putenv \"ANKI_SB_WORKING\" `getenv " + btn_id + "`; ")
    environment_path = mel.eval("getenv ANKI_SB_WORKING")
    cmds.text(g_SBLabelElement, edit=True, label=("Updated: " + environment_path), align='center')
    je.load_audio_to_globals()
    try:
        # Call C++ command to regenerate SoundBanks...
        mel.eval("AnkiMayaWWisePlugIn_ReloadSoundBanks")
    except:
        cmds.warning("Something bad happened when parsing audio - AnkiMayaWWisePlugIn_ReloadSoundBanks")


def ShowSoundBankUI(item):
    global g_ClipWindow
    global g_SBLabelElement

    g_ClipWindow = cmds.window(title="Sound Bank Working Directory")
    cmds.frameLayout(label="Sound Bank Working Directory")
    cmds.rowLayout(numberOfColumns=3)
    cmds.radioCollection()
    environment_path = mel.eval("getenv ANKI_SB_WORKING")
    local_environment_path = mel.eval("getenv ANKI_SB_WORKING")
    shared_environment_path = mel.eval("getenv ANKI_SB_SHARED")
    built_environment_path = mel.eval("getenv ANKI_SB_BUILT")
    cmds.radioButton(label="Local", onCommand=partial(SBDirChanged, "ANKI_SB_LOCAL"),
                     select=(environment_path == local_environment_path))
    cmds.radioButton(label="Shared", onCommand=partial(SBDirChanged, "ANKI_SB_SHARED"),
                     select=(environment_path == shared_environment_path))
    cmds.radioButton(label="Built", onCommand=partial(SBDirChanged, "ANKI_SB_BUILT"),
                     select=(environment_path == built_environment_path))
    cmds.setParent('..')
    cmds.separator()
    g_SBLabelElement = cmds.text(label="Current: " + environment_path, align='center')
    cmds.showWindow(g_ClipWindow)


def openJsonWrapper():
    export_path = verify_export_path()
    open_json(export_path)


# Setup the "AnkiAnimExport" MEL command...
class scriptedCommand(OpenMayaMPx.MPxCommand):
    def __init__(self):
        OpenMayaMPx.MPxCommand.__init__(self)

    # Invoked when the command is run. ( Command so can be integrated with other scripts. )
    def doIt(self, argList):
        print("Anki plugin called!")
        argData = OpenMaya.MArgParser(self.syntax(), argList)

        # TODO: this is an abuse of flags as they all do radically different things with the same data.
        # probably want to split this into different plugins
        if argData.isFlagSet(kOpenJsonShortFlagName):
            # Run with "AnkiAnimExport -open_json"
            openJsonWrapper()
        elif argData.isFlagSet(kAudioShortFlagName):
            # Run with "AnkiAnimExport -audio"
            setupAudioNode(je.g_AudioNamesSorted)
        else:
            exportRobotAnim()


# Creator
def cmdCreator():
    return OpenMayaMPx.asMPxPtr(scriptedCommand())


def syntaxCreator():
    ''' Flag opens json, select audio'''
    syntax = OpenMaya.MSyntax()
    syntax.addFlag(kOpenJsonShortFlagName, kOpenJsonLongFlagName, OpenMaya.MSyntax.kNoArg)
    syntax.addFlag(kAudioShortFlagName, kAudioLongFlagName, OpenMaya.MSyntax.kNoArg)
    return syntax


# Initialize the script plug-in
def initializePlugin(mobject):
    global g_PrevMenuName

    mplugin = OpenMayaMPx.MFnPlugin(mobject)
    print("Initializing Anki plugin")
    cmds.cycleCheck(e=False)
    try:
        mplugin.registerCommand(kPluginCmdName, cmdCreator, syntaxCreator)
        je.load_audio_to_globals()
        # Create the menu on the main menu bar...
        g_PrevMenuName = cmds.menu(label='Anki', parent='MayaWindow')
        cmds.menuItem(label='Export Anim', command=exportRobotAnim)
        cmds.menuItem(label='Set Export Path', command=set_export_path)
        cmds.menuItem(label='Select Audio Node', command=setupAudioNode)
        cmds.menuItem(label='SoundBank Dir', command=ShowSoundBankUI)
    except:
        sys.stderr.write("Failed to register command: %s" % kPluginCmdName + os.linesep)
        raise


# Uninitialize the script plug-in
def uninitializePlugin(mobject):
    mplugin = OpenMayaMPx.MFnPlugin(mobject)
    print("Uninitialize Anki plugin")
    # clean up our previous menu
    try:
        mplugin.deregisterCommand(kPluginCmdName)
        cmds.deleteUI(g_PrevMenuName, menu=True)
    except:
        sys.stderr.write("Failed to unregister command: %s" % kPluginCmdName + os.linesep)


