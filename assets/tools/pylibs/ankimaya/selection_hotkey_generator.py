# When user presses alt+number that stores selected objects into memory. when user presses
# cmd+number it takes those selected controllers out of memory.
# class needs to be initiated when maya starts

# daria.jerjomina@anki.com
# Oct 6, 2016: clearing selection on new scene and error check
# Oct 11, 2016: added generation of hotkeys that happens on init

import maya.cmds as mc
import maya.OpenMaya as OpenMaya
import maya.mel as mel


class SelectionHotkeyGenerator(object):
    def __init__(self):
        self.key_selectedObjects = {}  # "key_name":["ctr_name"]
        self.key_name_number = {"one": "1", "two": "2", "three": "3"}
        self.populate_keys()
        OpenMaya.MSceneMessage.addCallback(OpenMaya.MSceneMessage.kAfterNew, self.clear_selection)

    # ----------------------------------------------------------------------------------------------
    # Commands Executed by Hotkeys
    # ----------------------------------------------------------------------------------------------

    def store_selected_objects(self, key_name=""):
        selected_objects = mc.ls(sl=True)
        self.key_selectedObjects[key_name] = selected_objects
        print "stored %s objects as key %s" %(selected_objects, key_name)

    def select_stored_objects(self, key_name=""):
        if key_name in self.key_selectedObjects.keys():
            mc.select(self.key_selectedObjects[key_name])
        else:
            mc.warning("No object are stored under key %s" % key_name)

    def clear_selection(self, *args):
        self.key_selectedObjects = {}

    # ----------------------------------------------------------------------------------------------
    # Hotkey Generation
    # ----------------------------------------------------------------------------------------------

    def populate_keys(self):
        for key_name in self.key_name_number.keys():
            self.populate_storing_key(key_name)
            self.populate_selecting_key(key_name)

    def populate_storing_key(self, key_name):
        command_type = "StoreSelectedObjects%s" % key_name.capitalize()
        name_command = "%sNameCommand" % command_type

        mc.nameCommand(name_command, ann=command_type, c=name_command)
        mc.hotkey(keyShortcut=self.key_name_number[key_name], altModifier=True, name=name_command)
        mel.eval('if (!`runTimeCommand -exists %s`) '
                 '{runTimeCommand -annotation %s'
                 ' -command "shg_inst.store_selected_objects(key_name=\\"%s\\")"'
                 ' -commandLanguage "python" %s;}' % (name_command,command_type,key_name,
                                                      name_command))

    def populate_selecting_key(self, key_name):
        command_type = "SelectStoredObjects%s" % key_name.capitalize()
        name_command = "%sNameCommand" % command_type

        mc.nameCommand(name_command, ann=command_type, c=name_command)
        mc.hotkey(keyShortcut=self.key_name_number[key_name], commandModifier=True,
                  name=name_command)
        mel.eval('if (!`runTimeCommand -exists %s`) '
                 '{runTimeCommand -annotation %s'
                 ' -command "shg_inst.select_stored_objects(key_name=\\"%s\\")"'
                 ' -commandLanguage "python" %s;}' % (name_command, command_type, key_name,
                                                      name_command))