# UI for robot's movement related tools
#
# Consists of three parts:
#
# Main Window - An image with buttons overlaying it
#
# Additional buttons - a horizontal layout with buttons on the left side.
#  Those are buttons with tools that don't set the movement but are additional helping tools, such
#  as place missing keyframes and clamp speeds
#
# User shortcuts - the layout for those buttons is structured the same as for additional buttons.
#  Initially it only has one button, pressing that button adds a button that has information on
#  robot's movement in current segment.
#
#
# UI parameters get populated from movement_ui.json
# Tool calls functions from wheel_movemnt.py

# Sep 18 - initial commit
# Oct 02 - Adding and removing user buttons
# Oct 03 - Made scrollable
# Oct 06 - Creating local user's json file if there is none
# Oct 20 - New UI, multiply/divide functionality


import sys
import os
import os.path
import copy
import json
import functools

import maya.cmds as mc
from maya import OpenMayaUI as omui

# Maya 2016 uses PySide and Maya 2017+ uses PySide2, so try PySide2 first before resorting to PySide
try:
    from PySide2.QtCore import *
    from PySide2.QtGui import *
    from PySide2.QtWidgets import *
    from PySide2.QtUiTools import *
    from shiboken2 import wrapInstance
except ImportError:
    from PySide.QtCore import *
    from PySide.QtGui import *
    from PySide.QtUiTools import *
    from shiboken import wrapInstance

import ankimaya.wheel_movement as wm
from window_docker import Dock

WIN_TITLE = "Robot Movement"

MAIN_IMAGE_PARAMETERS = [437.0, 460.0]
ADDITIONAL_BTTN_ICON_SIZE = [33.0, 33.0]  # Default icon size unless json overwrites it
OFFSET_BUTTONS = -2.0  # After making window dockable, overlaying buttons and main image get disaligned, this hack fixes it

_maya_version = mc.about(version=True).split()[0]
USER_JSON_FILE = os.path.join(os.getenv("HOME"), ".anki", "maya", _maya_version, "movement_ui.json")
JSON_FILE = os.path.join(os.path.dirname(__file__), "movement_ui.json")

TOOLS_DIR_ENV_VAR = "ANKI_TOOLS"
MOVEMENT_UI_ICONS_DIR = os.path.join(os.getenv(TOOLS_DIR_ENV_VAR), "icons", "MovementUI")
MOVEMENT_UI_ALL_PNG = os.path.join(MOVEMENT_UI_ICONS_DIR, "coz_movement_ui_all.png")
ADD_ICON = os.path.join(MOVEMENT_UI_ICONS_DIR, "addition_switch.png")
ADD_ICON_HI = os.path.join(MOVEMENT_UI_ICONS_DIR, "addition_switch_hi.png")
MULTIPLY_ICON = os.path.join(MOVEMENT_UI_ICONS_DIR, "multiply_switch.png")
MULTIPLY_ICON_HI = os.path.join(MOVEMENT_UI_ICONS_DIR, "multiply_switch_hi.png")
ICON_WIDTH = 40
ICON_HEIGHT = 40
TOGGLE_NEXT_KEYS_ICON_ON = os.path.join(MOVEMENT_UI_ICONS_DIR, "move_next_keys_ON.png")
TOGGLE_NEXT_KEYS_ICON_OFF = os.path.join(MOVEMENT_UI_ICONS_DIR, "move_next_keys_OFF.png")

SWITCH_ICON_SIZE = [37.0, 37.0]
SWITCH_POSITION = [400.0, 26.0]

# Padding for the main image and overlaying buttons
PADDING_X = 40.0
PADDING_Y = 30.0

DEFAULT_ICON_STR = "default_icon"
ADDS_BUTTONS_STR = "adds_buttons"
BORDER_COLOR_HI_STR = "border_color_hi"
REMOVABLE_STR = "removable"
ON_ICON_STR = "on_icon"
ICON_SIZE_STR = "icon_size"
BTTN_COORDINATES_STR = "bttn_coordinates"
HIGHLIGHT_ICON_STR = "highlight_icon"
FORCE_RATIO_STR = "force_ratio"
ON_HIGHLIGHT_ICON_STR = "on_highlight_icon"
WHEEL_ROTATION_AMOUNT_STR = "wheel_rotation_amount"
FUNCTION_TO_CALL_STR = "function_to_call"
COLOR_STR = "color"
IS_ADDITIVE_STR = "is_additive"
FROM_WHEEL_MOVEMENT_CLASS_STR = "from_wheel_movement_class"
ADD_TO_ARC_TURN_STR = "add_to_arc_turn"
VALUE_STR = "value"
DIRECTION_STR = "direction"
ADDITIONAL_BTTNS_STR = "additional_bttns"
WHEEL_ROT_BTTNS_STR = "wheel_rot_bttns"

# Most buttons don't have a border (style = none), additional buttons have a border that becomes
# visible (alpha = 255) during hover and invisible (alpha = 0) when in the deafult state
DEFAULT_BORDER_STYLE = "none"
DEFAULT_BORDER_STYLE_HIGHLIGHT = "solid"
DEFAULT_BORDER_WIDTH = 1
DEFAULT_BORDER_COLOR = "rgb(0,0,0,0)"  # Changing color, not border-style, so that image remains the same size
DEFAULT_BORDER_HIGHLIGHT_COLOR = "rgb(206, 206, 206)"  # Changing color, not border-style, so that image remains the same size

WIN_TITLE = "Movement UI"
# This is the order of preference for the dock button:
DOCKING_WINDOW = [WIN_TITLE, 'ChannelBoxLayerEditor', 'AttributeEditor']
PREVIEW_SELECTOR_UI_ICONS_DIR = os.path.join(os.getenv(TOOLS_DIR_ENV_VAR), "icons", "PreviewSelectorUI")
CLOSE_ICON = os.path.join(PREVIEW_SELECTOR_UI_ICONS_DIR, "close.png")
WIN1_ICON = os.path.join(PREVIEW_SELECTOR_UI_ICONS_DIR, "hide.png")
WIN2_ICON = os.path.join(PREVIEW_SELECTOR_UI_ICONS_DIR, "dock.png")
WIN3_ICON = os.path.join(PREVIEW_SELECTOR_UI_ICONS_DIR, "float.png")

USER_JSON_CONTENTS = {
    "user_shortcuts": [
        {
            ADDS_BUTTONS_STR: True,
            BORDER_COLOR_HI_STR: wm.MOVEMENT_BUTTON_BORDER_COLOR_HI,
            DEFAULT_ICON_STR: "plus_blue.png",
            REMOVABLE_STR: False
        }
    ]
}

MAX_MESSAGE_LINES = 2

mayaMainWindowPtr = omui.MQtUtil.mainWindow()
mayaMainWindow = wrapInstance(long(mayaMainWindowPtr), QWidget)


class ToggleButton(QPushButton):
    """
    Button in the top right corner that changes the state of
    all addition buttons to multiplication when toggled.
    Under the hood, it's a checkbox with an image and
    highlighting functionality.
    On - multiply, Off - add
    """

    def __init__(self, parent=None, on_icon=MULTIPLY_ICON, off_icon=ADD_ICON,
                 highlight_on_icon=None, highlight_off_icon=None):
        super(ToggleButton, self).__init__(parent)
        self.setParent(parent)
        self.highlight_on_icon = highlight_on_icon
        self.highlight_off_icon = highlight_off_icon
        self.on_icon = on_icon
        self.off_icon = off_icon

        self.icon = QIcon()
        self.setCheckable(True)

        self.icon.addPixmap(QPixmap(on_icon), QIcon.Normal, QIcon.On)
        self.icon.addPixmap(QPixmap(off_icon), QIcon.Normal, QIcon.Off)

        self.setIcon(self.icon)
        self.setIconSize(QSize(SWITCH_ICON_SIZE[0], SWITCH_ICON_SIZE[1]))
        self.move(SWITCH_POSITION[0], SWITCH_POSITION[1])

        self.setStyleSheet("background-color:%s; border-style:%s"
                           % (DEFAULT_BORDER_COLOR, DEFAULT_BORDER_STYLE))

    def enterEvent(self, event):
        if self.highlight_on_icon and self.highlight_off_icon:
            if self.isChecked():
                self.setIcon(QIcon(self.highlight_on_icon))
            else:
                self.setIcon(QIcon(self.highlight_off_icon))
        else:
            self.setStyleSheet("background-color:rgb(0,0,0,0); border-style:%s; border-width:%spx;"
                               "border-color: %s" % (DEFAULT_BORDER_STYLE_HIGHLIGHT,
                                                     DEFAULT_BORDER_WIDTH,
                                                     DEFAULT_BORDER_HIGHLIGHT_COLOR))

    def leaveEvent(self, event):
        if self.highlight_on_icon and self.highlight_off_icon:
            if self.isChecked():
                self.setIcon(QIcon(self.on_icon))
            else:
                self.setIcon(QIcon(self.off_icon))
        else:
            self.setStyleSheet("background-color:rgb(0,0,0,0); border-style:%s; border-width:%spx;"
                               "border-color: %s" % (DEFAULT_BORDER_STYLE_HIGHLIGHT,
                                                     DEFAULT_BORDER_WIDTH,
                                                     DEFAULT_BORDER_COLOR))


class MovementButton(QPushButton):
    """
    Button with parameters from a json file (in a form of bttn_info)
    Has hover press and release functionality.
    Can be used as a button overlaying an image or an additional
    button below the image.
    """
    middle_clicked = Signal()
    left_clicked = Signal()

    def __init__(self, parent=None, bttn_info=None, bttn_idx=0,
                 icon_dir=MOVEMENT_UI_ICONS_DIR, bttn_info_label=None, modify_next_keys=False):
        super(MovementButton, self).__init__(parent)
        self.setParent(parent)
        self.bttn_info = bttn_info
        self.removable = False
        self.bttn_idx = bttn_idx
        self.icon_dir = icon_dir
        self.bttn_info_label = bttn_info_label
        self.modify_next_keys = modify_next_keys

        if DEFAULT_ICON_STR in bttn_info:
            icon_file = os.path.join(self.icon_dir, bttn_info[DEFAULT_ICON_STR])
            if os.path.exists(icon_file):
                icon = QIcon(icon_file)
                if ON_ICON_STR in bttn_info:
                    self.setCheckable(True)
                    on_icon_file = os.path.join(self.icon_dir, bttn_info[ON_ICON_STR])
                    icon.addPixmap(QPixmap(on_icon_file), QIcon.Normal, QIcon.On)
                    icon.addPixmap(QPixmap(icon_file), QIcon.Normal, QIcon.Off)
                self.setIcon(icon)
            else:
                mc.warning("%s file is missing from %s" % (bttn_info[DEFAULT_ICON_STR], self.icon_dir))

        if ICON_SIZE_STR in bttn_info:
            self.setIconSize(QSize(bttn_info[ICON_SIZE_STR][0], bttn_info[ICON_SIZE_STR][1]))

        if COLOR_STR in bttn_info:
            self.setStyleSheet("background-color:rgb(%f,%f,%f,%f); border-style:none"
                               % (bttn_info[COLOR_STR][0], bttn_info[COLOR_STR][1],
                                  bttn_info[COLOR_STR][2], bttn_info[COLOR_STR][3]))
        else:
            self.setStyleSheet("background-color:%s; border-style:%s"
                               % (DEFAULT_BORDER_COLOR, DEFAULT_BORDER_STYLE))

        border_style = DEFAULT_BORDER_STYLE

        # If there is a highlight option on a button border needs to be solid, but color change (so that button doesn't move)
        if BORDER_COLOR_HI_STR in bttn_info:
            border_style = DEFAULT_BORDER_STYLE_HIGHLIGHT

        self.setStyleSheet("background-color:rgb(0,0,0,0); border-style:%s; border-width:%spx;"
                           "border-color: %s" % (border_style, DEFAULT_BORDER_WIDTH,
                                                 DEFAULT_BORDER_COLOR))

        if BTTN_COORDINATES_STR in bttn_info:
            self.move(bttn_info[BTTN_COORDINATES_STR][0], bttn_info[BTTN_COORDINATES_STR][1])

        if REMOVABLE_STR in bttn_info:
            self.removable = bttn_info[REMOVABLE_STR]

        self.force_ratio = True
        if FORCE_RATIO_STR in bttn_info:
            self.force_ratio = bttn_info[FORCE_RATIO_STR]

        if WHEEL_ROTATION_AMOUNT_STR in bttn_info and IS_ADDITIVE_STR in bttn_info:
            self.left_clicked.connect(lambda: wm.rotate_wheels_by(bttn_info[WHEEL_ROTATION_AMOUNT_STR][0],
                                                                  bttn_info[WHEEL_ROTATION_AMOUNT_STR][1],
                                                                  bttn_info[IS_ADDITIVE_STR], False,
                                                                  self.force_ratio,
                                                                  modify_next_keys=self.modify_next_keys))
        elif WHEEL_ROTATION_AMOUNT_STR in bttn_info:
            self.left_clicked.connect(lambda: wm.rotate_wheels_by(bttn_info[WHEEL_ROTATION_AMOUNT_STR][0],
                                                                  bttn_info[WHEEL_ROTATION_AMOUNT_STR][1],
                                                                  modify_next_keys=self.modify_next_keys))
        elif FUNCTION_TO_CALL_STR in bttn_info:
            if FROM_WHEEL_MOVEMENT_CLASS_STR in bttn_info and bttn_info[FROM_WHEEL_MOVEMENT_CLASS_STR] == True:
                try:
                    wm_i = wm.WheelMovement()
                    function_to_call = getattr(wm_i, bttn_info[FUNCTION_TO_CALL_STR])
                except AttributeError:
                    mc.warning("Unable to call %s" % bttn_info[FUNCTION_TO_CALL_STR])
                    return
                self.left_clicked.connect(lambda: function_to_call())
            elif bttn_info[FUNCTION_TO_CALL_STR] == ADD_TO_ARC_TURN_STR:
                self.left_clicked.connect(lambda: wm.add_to_arc_turn(bttn_info[VALUE_STR],
                                                                     bttn_info[DIRECTION_STR]))
            else:
                try:
                    function_to_call = getattr(wm, bttn_info[FUNCTION_TO_CALL_STR])
                except AttributeError:
                    mc.warning("Unable to call %s" % bttn_info[FUNCTION_TO_CALL_STR])
                    return

                self.left_clicked.connect(lambda: function_to_call())

    def mousePressEvent(self, event):
        """
        Currently left and middle click are the only options.
        Middle click removes user shortcuts.
        """
        if event.button() == Qt.LeftButton:
            self.left_clicked.emit()
        if event.button() == Qt.MiddleButton:
            self.middle_clicked.emit()
            if self.removable:
                self.setParent(None)

    def enterEvent(self, event):
        self.set_hover_state()

    def leaveEvent(self, event):
        self.set_default_state()

    def set_wheel_message(self):
        l_rotation_amount = ""
        r_rotation_amount = ""
        wheel_rotation_string = ""

        if self.bttn_info_label:
            message_strings = []
            if WHEEL_ROTATION_AMOUNT_STR in self.bttn_info or (
                    "function_to_call" in self.bttn_info and self.bttn_info["function_to_call"] == "add_to_arc_turn"):
                if WHEEL_ROTATION_AMOUNT_STR in self.bttn_info:
                    # Separate wheel rotations
                    if IS_ADDITIVE_STR in self.bttn_info and self.bttn_info[IS_ADDITIVE_STR] == True:
                        wheel_rotation_string, l_rotation_amount, r_rotation_amount = \
                            self.set_aditive_wheel_msg(self.bttn_info[WHEEL_ROTATION_AMOUNT_STR][0],
                                                       self.bttn_info[WHEEL_ROTATION_AMOUNT_STR][1])

                    elif WHEEL_ROTATION_AMOUNT_STR in self.bttn_info:
                        wheel_rotation_string = "Separate wheel rotations in degrees: "
                        l_rotation_amount = self.bttn_info[WHEEL_ROTATION_AMOUNT_STR][0]
                        r_rotation_amount = self.bttn_info[WHEEL_ROTATION_AMOUNT_STR][1]

                        if "degrees" in self.bttn_info:
                            message_strings.append("Robot rotation %s degrees" % (self.bttn_info["degrees"]))
                        if "cm" in self.bttn_info:
                            message_strings.append(
                                "Robot movement %s cm" % (self.bttn_info["cm"]))

                    if l_rotation_amount != "":
                        wheel_rotation_string += "left %s, " % (l_rotation_amount)
                    if r_rotation_amount != "":
                        wheel_rotation_string += "right %s" % (r_rotation_amount)

                    message_strings.append(wheel_rotation_string)

                elif self.bttn_info["function_to_call"] == "add_to_arc_turn":
                    wheel_rotation_string, l_rotation_amount, r_rotation_amount = self.set_aditive_wheel_msg(
                        self.bttn_info[VALUE_STR], self.bttn_info[VALUE_STR])
                    # In case of arc turn there is only one rotation amount, the other wheels rotation depends on ratio
                    wheel_rotation_string += str(l_rotation_amount)

                    message_strings.append(wheel_rotation_string)

            elif "tool_tip" in self.bttn_info:
                message_strings.append(self.bttn_info["tool_tip"])

            if len(message_strings) < MAX_MESSAGE_LINES:
                for i in range(MAX_MESSAGE_LINES-len(message_strings)):
                    message_strings.append("")

            self.bttn_info_label.setText("\n".join(message_strings))

    def set_aditive_wheel_msg(self, l_rotation, r_rotation):
        wheel_rotation_string = "Add wheel rotations in degrees: "
        l_rotation_amount = ""
        r_rotation_amount = ""

        if l_rotation:
            if l_rotation == wm.DEFAULT_PLUS_STR:
                l_rotation_amount = wm.DEFAULT_WHEEL_ADD_VALUE
            if l_rotation == wm.DEFAULT_MINUS_STR:
                l_rotation_amount = wm.DEFAULT_WHEEL_MINUS_VALUE

        if r_rotation:
            if r_rotation == wm.DEFAULT_PLUS_STR:
                r_rotation_amount = wm.DEFAULT_WHEEL_ADD_VALUE
            if r_rotation == wm.DEFAULT_MINUS_STR:
                r_rotation_amount = wm.DEFAULT_WHEEL_MINUS_VALUE

        return wheel_rotation_string, l_rotation_amount, r_rotation_amount

    def set_hover_state(self):
        self.set_wheel_message()

        if HIGHLIGHT_ICON_STR in self.bttn_info:
            icon_file = os.path.join(self.icon_dir, self.bttn_info[HIGHLIGHT_ICON_STR])
            icon = QIcon(icon_file)
            icon.addPixmap(QPixmap(icon_file), QIcon.Normal, QIcon.Off)
            if ON_HIGHLIGHT_ICON_STR in self.bttn_info:
                on_icon_file = os.path.join(self.icon_dir, self.bttn_info[ON_HIGHLIGHT_ICON_STR])
                icon.addPixmap(QPixmap(on_icon_file), QIcon.Normal, QIcon.On)
            self.setIcon(icon)
        if BORDER_COLOR_HI_STR in self.bttn_info:
            self.setStyleSheet("background-color:rgb(0,0,0,0); border-style:%s; border-width:%spx;"
                               "border-color: %s" % (DEFAULT_BORDER_STYLE_HIGHLIGHT,
                                                     DEFAULT_BORDER_WIDTH,
                                                     self.bttn_info[BORDER_COLOR_HI_STR]))

    def set_default_state(self):
        if DEFAULT_ICON_STR in self.bttn_info:
            icon_file = os.path.join(self.icon_dir, self.bttn_info[DEFAULT_ICON_STR])
            if os.path.exists(icon_file):
                icon = QIcon(icon_file)
                if ON_ICON_STR in self.bttn_info:
                    on_icon_file = os.path.join(self.icon_dir, self.bttn_info[ON_ICON_STR])
                    icon.addPixmap(QPixmap(on_icon_file), QIcon.Normal, QIcon.On)
                    icon.addPixmap(QPixmap(icon_file), QIcon.Normal, QIcon.Off)
                self.setIcon(icon)
        if BORDER_COLOR_HI_STR in self.bttn_info:
            self.setStyleSheet("background-color:rgb(0,0,0,0); border-style:%s; border-width:%spx;"
                               "border-color: %s" % (DEFAULT_BORDER_STYLE_HIGHLIGHT,
                                                     DEFAULT_BORDER_WIDTH,
                                                     DEFAULT_BORDER_COLOR))

    def set_add_multiply(self):
        on_icon = ON_ICON_STR in self.bttn_info
        wheel_rotation_amount = WHEEL_ROTATION_AMOUNT_STR in self.bttn_info
        is_additive = IS_ADDITIVE_STR in self.bttn_info
        function_to_call = FUNCTION_TO_CALL_STR in self.bttn_info

        l_value, r_value, l_wheel_add, r_wheel_add, additive, multipliable = \
            None, None, None, None, None, None

        if on_icon and wheel_rotation_amount and is_additive and self.bttn_info[IS_ADDITIVE_STR] == True:
            # if don't disconnect will run all connected functions one after another
            self.left_clicked.disconnect()
            if not self.isChecked():
                self.left_clicked.connect(
                    lambda: wm.rotate_wheels_by(self.bttn_info[WHEEL_ROTATION_AMOUNT_STR][0],
                                                self.bttn_info[WHEEL_ROTATION_AMOUNT_STR][1],
                                                True, False, self.force_ratio,
                                                modify_next_keys=self.modify_next_keys))

            else:
                self.left_clicked.connect(
                    lambda: wm.rotate_wheels_by(self.bttn_info[WHEEL_ROTATION_AMOUNT_STR][0],
                                                self.bttn_info[WHEEL_ROTATION_AMOUNT_STR][1],
                                                False, True, self.force_ratio,
                                                modify_next_keys=self.modify_next_keys))

        if on_icon and function_to_call and self.bttn_info[FUNCTION_TO_CALL_STR] == ADD_TO_ARC_TURN_STR:
            # If don't disconnect will run all connected functions one after another
            self.left_clicked.disconnect()
            if not self.isChecked():
                self.left_clicked.connect(
                    lambda: wm.add_to_arc_turn(self.bttn_info[VALUE_STR], self.bttn_info[DIRECTION_STR],
                                               True, False))
            else:
                self.left_clicked.connect(
                    lambda: wm.add_to_arc_turn(self.bttn_info[VALUE_STR], self.bttn_info[DIRECTION_STR],
                                               False, True))

        return l_value, r_value, l_wheel_add, r_wheel_add, additive, multipliable

def _toggleFloat():
    print("TOGGLE FLOAT")

class AdditionalBttns(QWidget):
    def __init__(self, parent=None, populate_from=ADDITIONAL_BTTNS_STR, json_path=JSON_FILE, bttn_info_label=None):
        self.bttn_idx_dict = {}  # So that can update indexes after removing a button
        self.bttn_info_label = bttn_info_label
        if not os.path.isfile(json_path):
            mc.warning("%s file is missing" % json_path)
            return
        super(AdditionalBttns, self).__init__(parent)
        self.setParent(parent)
        self.populate_from = populate_from
        self.json_path = json_path

        self.additional_bttn_infos = []
        self.populate_bttn_dicts()
        self.initUI()


    def initUI(self):
        self.layout = QHBoxLayout(self)
        self.layout.setAlignment(Qt.AlignLeft)
        self.bttn_idx = 0

        for bttn_info in self.additional_bttn_infos:
            button = MovementButton(self, bttn_info, bttn_info_label=self.bttn_info_label)
            if ADDS_BUTTONS_STR in bttn_info:
                button.left_clicked.connect(self.add_user_button)
            if button.removable:
                self.bttn_idx_dict[self.bttn_idx] = self.bttn_idx
                # Using partial instead of lambda because need to pass specific index
                button.middle_clicked.connect(functools.partial(self.remove_bttn_from_json, self.bttn_idx))
            self.bttn_idx += 1
            self.layout.addWidget(button)



    def populate_bttn_dicts(self):
        with open(self.json_path, "r+") as data_file:
            data = json.load(data_file)
            for bttn_info_node in data[self.populate_from]:
                if ICON_SIZE_STR not in bttn_info_node:
                    bttn_info_node[ICON_SIZE_STR] = copy.copy(ADDITIONAL_BTTN_ICON_SIZE)
                self.additional_bttn_infos.append(bttn_info_node)

    def add_user_button(self):
        if not wm.are_wheels_keyed():
            mc.warning("Must have both wheels keyed at least once in the timeline")
            return
        bttn_info = wm.get_bttn_info_at_current_segment()
        if bttn_info is None:
            return
        bttn_info[ICON_SIZE_STR] = copy.copy(ADDITIONAL_BTTN_ICON_SIZE)  # So that size is consistent
        button = self.add_bttn(bttn_info)
        self.bttn_idx_dict[self.bttn_idx] = self.bttn_idx
        button.middle_clicked.connect(functools.partial(self.remove_bttn_from_json, self.bttn_idx))
        self.bttn_idx += 1
        self.add_bttn_to_json(bttn_info)

    def add_bttn_to_json(self, bttn_info):
        with open(self.json_path, "r+") as data_file:
            data = json.load(data_file)
            data[self.populate_from].append(bttn_info)
            data_file.seek(0)
            data_file.write(json.dumps(data, indent=4, sort_keys=True, separators=(',', ': ')))
            data_file.truncate()
            data_file.close()

    def add_bttn(self, bttn_info):
        button = MovementButton(self, bttn_info)
        self.layout.addWidget(button)
        return button

    def remove_bttn_from_json(self, bttn_idx):
        """
        This function is responsible only for removing button's node from the corresponding json file
        (Widget itself is being removed from the panel on that button's middle click function.)
        """
        with open(self.json_path, "r+") as data_file:
            data = json.load(data_file)
            del data[self.populate_from][self.bttn_idx_dict[bttn_idx]]
            data_file.seek(0)
            data_file.write(json.dumps(data, indent=4, sort_keys=True, separators=(',', ': ')))
            data_file.truncate()
            data_file.close()

        # Reassign indexes for buttons that go after the deleted one, so that remove the correct ones in the future
        for key, value in self.bttn_idx_dict.items():
            if value > self.bttn_idx_dict[bttn_idx]:
                self.bttn_idx_dict[key] = value - 1

        self.bttn_idx -= 1  # So that the new added button has correct idx


class Overlay(QWidget):
    """
    Buttons overlaying an image
    """

    def __init__(self, parent=None, bttn_info_label=None):
        super(Overlay, self).__init__(parent)
        self.setParent(parent)
        self.button_infos = []
        self.populate_bttn_dicts()
        self.main_buttons = []
        for bttn_info in self.button_infos:
            button = MovementButton(self, bttn_info, bttn_info_label=bttn_info_label)
            self.main_buttons.append(button)
        self.toggle_button = ToggleButton(parent=self, on_icon=MULTIPLY_ICON, off_icon=ADD_ICON,
                                          highlight_on_icon=MULTIPLY_ICON_HI, highlight_off_icon=ADD_ICON_HI)
        self.toggle_button.clicked.connect(self.change_state)

        self.setGeometry(OFFSET_BUTTONS, OFFSET_BUTTONS,
                         MAIN_IMAGE_PARAMETERS[0] + PADDING_X, MAIN_IMAGE_PARAMETERS[1] + PADDING_Y)

    def change_state(self):
        if self.toggle_button.isChecked():
            for button in self.main_buttons:
                button.setChecked(True)
                self.toggle_button.setIcon(QIcon(MULTIPLY_ICON_HI))
                button.set_add_multiply()
        else:
            for button in self.main_buttons:
                button.setChecked(False)
                self.toggle_button.setIcon(QIcon(ADD_ICON_HI))
                button.set_add_multiply()

    def set_change_next_keys(self, change_next_keys):
        for button in self.main_buttons:
            button.modify_next_keys = change_next_keys

    def populate_bttn_dicts(self, json_file=JSON_FILE):
        with open(json_file, "r+") as data_file:
            data = json.load(data_file)
            for bttn_info_node in data[WHEEL_ROT_BTTNS_STR]:
                self.button_infos.append(bttn_info_node)


class MovementUI(QWidget):
    """
    Overall wondow, responsible for scrolling
    """

    def __init__(self, *args, **kwargs):
        super(MovementUI, self).__init__(*args, **kwargs)
        self.setParent(mayaMainWindow)
        self.setWindowFlags(Qt.Window)
        self.isFloating = False
        self.initUI()

    def initUI(self):
        self.layout = QGridLayout(self)
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
        self.initScrollArea()
        bttn_info_label = QLabel("\n")

        self.subWindow = Subwindow(parent=self, bttn_info_label=bttn_info_label)
        self.scrollLayout.addWidget(self.subWindow)

        self.layout.addWidget(self.scroll)
        self.setWindowTitle(WIN_TITLE)

        bottom_horizontal_layout = QHBoxLayout()
        icon2 = QIcon()
        closeButton = QPushButton()
        icon2.addPixmap(QPixmap(CLOSE_ICON))
        closeButton.setIcon(icon2)
        closeButton.setIconSize(QSize(20, 20))
        closeButton.setFixedWidth(20 + 1)
        installToolTipMsg = "Close Movement UI"
        closeButton.setToolTip(installToolTipMsg)
        closeButton.clicked.connect(self.close)

        icon3 = QIcon()
        floatButton = QPushButton()
        icon3.addPixmap(QPixmap(WIN1_ICON))
        floatButton.setIcon(icon3)
        floatButton.setIconSize(QSize(20, 20))
        floatButton.setFixedWidth(20 + 1)
        installToolTipMsg = "Toggle Float"
        floatButton.setToolTip(installToolTipMsg)
        floatButton.clicked.connect(self._toggleFloat)

        qw = QWidget()
        qw.setFixedWidth(360)
        bottom_horizontal_layout = QHBoxLayout()

        bottom_horizontal_layout.setAlignment(Qt.AlignLeft)
        bottom_horizontal_layout.setSizeConstraint(QLayout.SetFixedSize)
        bttn_info_label.setFixedWidth(340)
        qw.setLayout(bottom_horizontal_layout)
        button_info_layout = QHBoxLayout()
        button_info_layout.setAlignment(Qt.AlignLeft)
        button_info_layout.addWidget(bttn_info_label)

        bottom_horizontal_layout.addLayout(button_info_layout)
        bottom_horizontal_layout.addSpacing(40)
        close_button_layout = QHBoxLayout()
        close_button_layout.setAlignment(Qt.AlignRight)
        close_button_layout.addWidget(floatButton)
        close_button_layout.addWidget(closeButton)
        bottom_horizontal_layout.addLayout(close_button_layout)
        #hlo.addWidget(floatButton)
        #hlo.addWidget(closeButton)
        bottom_horizontal_layout.geometry()
        self.layout.addWidget(qw)


        self.show()

    def initScrollArea(self):
        self.scrollWidget = QWidget()
        self.scrollLayout = QVBoxLayout(self.scrollWidget)
        self.scrollWidget.setLayout(self.scrollLayout)
        self.scroll = QScrollArea(self)
        self.scroll.setWidgetResizable(True)
        self.scroll.setMinimumWidth(MAIN_IMAGE_PARAMETERS[0] + PADDING_X)
        self.scroll.setMinimumHeight(MAIN_IMAGE_PARAMETERS[1])
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setWidget(self.scrollWidget)
        self.layout.addWidget(self.scroll)

    # def updateMovementInfo(self):

    def _toggleFloat(self):
        self.isFloating = not mc.workspaceControl(_globalDockControl, query=True, floating=True)
        mc.workspaceControl(_globalDockControl, edit=True, floating=self.isFloating)
        if self.isFloating:
            # self.toggleFloatButton.setText('Dock Widget')
            pass
        else:
            # self.toggleFloatButton.setText('Float Widget')
            # Searches for MacBlast, ChannelBox then Attr editor and finally the main window to dock to
            for dw in DOCKING_WINDOW:
                if mc.workspaceControl(dw, exists=True) and mc.workspaceControl(dw, q=True, visible=True):
                    mc.workspaceControl(_globalDockControl, edit=True, tabToControl=[dw, -1])
                    mc.workspaceControl(_globalDockControl, edit=True, restore=True)
                    break
            else:
                mc.workspaceControl(_globalDockControl, edit=True, dockToMainWindow=('right', 1))

    def _toggleDock(self):
        if self.isFloating:
            self._toggleFloat()
        if mc.workspaceControl(_globalDockControl, query=True, collapse=True):
            for dw in DOCKING_WINDOW:
                if mc.workspaceControl(dw, exists=True):
                    mc.workspaceControl(_globalDockControl, edit=True, tabToControl=[dw, -1])
                    break
            else:
                mc.workspaceControl(_globalDockControl, edit=True, dockToMainWindow=('right', 1))
        self.isDockedHidden = not mc.workspaceControl(_globalDockControl, query=True, collapse=True)
        mc.workspaceControl(_globalDockControl, edit=True, collapse=self.isDockedHidden)

    def close(self):
        global _globalDockControl, _globalPreviewUI
        mc.deleteUI(_globalDockControl)

    def closeEvent(self, *args, **kwargs):
        try:
            mc.deleteUI("MovementUI")
        except:
            print "didnt close movementWindow for some reason"


class Subwindow(QWidget):
    """
    Separate from main window so that can have it work with scroll
    """

    def __init__(self, parent=None, bttn_info_label=None):
        super(Subwindow, self).__init__(parent)
        self.setParent(parent)
        self.bttn_info_label = bttn_info_label
        self.initUI()

        self.modify_next_keys = False

    def initUI(self):
        self.layout = QGridLayout(self)
        self.layout.setHorizontalSpacing(0)
        pic = QLabel(self)
        pic.setPixmap(QPixmap(MOVEMENT_UI_ALL_PNG))
        pic.setGeometry(0, 0, MAIN_IMAGE_PARAMETERS[0], MAIN_IMAGE_PARAMETERS[1])
        self.layout.addWidget(pic)
        additional_bttns = AdditionalBttns(parent=self, populate_from=ADDITIONAL_BTTNS_STR,
                                           bttn_info_label=self.bttn_info_label)
        user_bttns = AdditionalBttns(parent=self, populate_from="user_shortcuts",
                                     json_path=USER_JSON_FILE,
                                     bttn_info_label=self.bttn_info_label)

        # Add following frames toggle to aditional buttons
        self.toggle_next_keys_button = ToggleButton(parent=self, on_icon=TOGGLE_NEXT_KEYS_ICON_ON,
                                                    off_icon=TOGGLE_NEXT_KEYS_ICON_OFF)
        additional_bttns.layout.addWidget(self.toggle_next_keys_button)
        self.toggle_next_keys_button.clicked.connect(self.change_modify_next_keys)

        self.layout.addWidget(additional_bttns, rowSpan=0)
        self.layout.addWidget(user_bttns, rowSpan=0)
        self.closeButton = QPushButton("")


        # First display the widget with an image, then one with the buttons overlaying the image

        self.show()
        self.overlay = Overlay(self, bttn_info_label=self.bttn_info_label)

    def closeMe(self):
        #try:
        global _globalDockControl, _globalPreviewUI
        mc.deleteUI(WIN_TITLE)
        mc.deleteUI(_globalDockControl)
        mc.deleteUI(_globalPreviewUI)
        mc.delete("MovementUI")
        #except:
            #pass

    def change_modify_next_keys(self):
        if self.modify_next_keys:
            self.modify_next_keys = False
        else:
            self.modify_next_keys = True
        self.overlay.set_change_next_keys(self.modify_next_keys)


def add_user_json_file(user_json_file, file_contents=USER_JSON_CONTENTS):
    user_json_dir = os.path.dirname(user_json_file)
    if not os.path.exists(user_json_dir):
        os.makedirs(user_json_dir)
    with open(user_json_file, "w") as data_file:
        data_file.write(json.dumps(file_contents, indent=4,
                                   sort_keys=True, separators=(',', ': ')))


def check(json_file, user_json_file):
    if not mc.objExists(wm.L_WHEEL_CTR) or not mc.objExists(wm.R_WHEEL_CTR):
        msg = "Movement UI works only when robot rig with separate wheel controllers is in the scene."
        msg += os.linesep + "Please make sure you have the correct rig referenced."
        mc.warning(msg)
        return False
    if not os.path.isfile(json_file):
        msg = "%s file is missing, so make sure you have correct file checked out" % json_file
        mc.warning(msg)
        return False
    if not os.path.isfile(user_json_file):
        msg = "%s file is missing, so it will be created now" % user_json_file
        mc.warning(msg)
        add_user_json_file(user_json_file)
    return True

_globalPreviewUI = None
_globalDockControl = None

def main(json_file=JSON_FILE, user_json_file=USER_JSON_FILE):
    if not check(json_file, user_json_file):
        return
    global _globalPreviewUI, _globalDockControl
    ui, dockWidget, _globalDockControl= Dock(MovementUI, winTitle=WIN_TITLE)
    return ui