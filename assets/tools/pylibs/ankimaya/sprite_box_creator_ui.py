import os
import maya.cmds as mc
from maya import OpenMayaUI as omui
from ankiutils import image_files

# UI for creating a sprite box or setting keyframe of a a selected keyframe.
# User can:
#   Chose a name of the asset from the png and tar files in the sprites directory
#   Set a render method
#   Set a loop configuration
#   Set x and y position of the sprite box
#   Set width and height of the sprite box
#   Set an alpha value of the image

# Conversion from inputted attributes and maya's cm units is happening in sprite_box_creator

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

import sprite_box_creator as sbc
import timeline_callbacks

reload(timeline_callbacks)
import re

WIN_TITLE = "Sprite Box Creator"
WINDOW_WIDTH = 640
WINDOW_HEIGHT = 380

ASSET_NAME_STR = "Asset name:"
FRAME_COUNT_STR = "Frame count:"
LAYER_STR = "Layer:"

# Once Sam changes the layering, can change the message to the commented out one.
# LAYER_EXAPLANATION_STR = "(Eyes are in-between layers 5 and 6.\n" \
#                          "Layer 5 and below - behind eyes. Layer 6 and above - in front of the
#                           eyes)"
LAYER_EXAPLANATION_STR = "(Eyes are in-between layers 5 and 6.\n" \
                         "Currently layer 4 and below - behind eyes. Layer 5 and above - in front" \
                         " of the eyes)"
RENDER_METHOD_STR = "Render Method:"
RGBA_STR = "RGBA"
EYE_COLOR_STR = "Eye Color"
RENDER_MEHTODS = [RGBA_STR, EYE_COLOR_STR]
LOOP_CONFIGURATION_STR = "Loop Configuration:"
CLEAR_STR = "Clear"
LOOP_STR = "Loop"
HOLD_STR = "Hold"
LOOP_CONFIGURATIONS = [CLEAR_STR, LOOP_STR, HOLD_STR]
X_POS_STR = "xPos (px):"
Y_POS_STR = "yPos (px):"
WIDTH_STR = "Width (px):"
HEIGHT_STR = "Height (px):"
ALPHA_STR = "Alpha (0-100):"
CREATE_SPRITE_BOX_STR = "Create Sprite Box"
SET_SPRITE_BOX_KEYFRAME_STR = "Set Sprite Box Keyframe"
DEFAULT_ASSET_NAME = "clear_sprite_box"
DEFAULT_FRAME_COUNT = "0"
EXPLANATION_COLOR = "orange"
WINDOW_TITLE = "Sprite Box Creator"

LAYER_NUM = 10
SPRITE_DEFAULT_WIDTH = 184
SPRITE_DEFAULT_HEIGHT = 96
DEFAULT_ALPHA = 100

REGEX_0_TO_100 = "([0-9]|[1-8][0-9]|9[0-9]|100)"
REGEX_0_TO_96 = "([0-9]|[1-8][0-9]|9[0-6])"
REGEX_0_TO_184 = "([0-9]|[1-8][0-9]|9[0-9]|1[0-7][0-9]|18[0-4])"
REGEX_MIN_96_TO_96 = "-?%s" % REGEX_0_TO_96
REGEX_MIN_184_TO_184 = "-?%s" % REGEX_0_TO_184

ANKI_ANIM_DIR = os.environ["ANKI_ANIM_DIR"]
SPRITES_PATH = os.path.abspath(os.path.join(ANKI_ANIM_DIR, "..", 'sprites'))

mayaMainWindowPtr = omui.MQtUtil.mainWindow()
MAYA_MAIN_WINDOW = wrapInstance(long(mayaMainWindowPtr), QWidget)


class MainWindow(QWidget):
    def __init__(self, sets_keyframe, x_pos=0, y_pos=0,
                 width=SPRITE_DEFAULT_WIDTH, height=SPRITE_DEFAULT_HEIGHT,
                 asset_name=DEFAULT_ASSET_NAME, render_method=RGBA_STR,
                 loop_configuration=CLEAR_STR, alpha=DEFAULT_ALPHA, layer_num=LAYER_NUM,
                 sprite_box=None):
        super(MainWindow, self).__init__()
        self.setParent(MAYA_MAIN_WINDOW)
        self.setWindowFlags(Qt.Window)

        # Check if this tool is already opened and close it if that's the case
        for widget in MAYA_MAIN_WINDOW.findChildren(QWidget):
            if widget is not self:
                if widget.windowTitle() == WINDOW_TITLE:
                    widget.close()

        self.sets_keyframe = sets_keyframe  # if true, sets keyframe, otherwise creates sprite box
        self.asset_names = [DEFAULT_ASSET_NAME]
        self.asset_names_and_paths = {DEFAULT_ASSET_NAME: None}

        # Init vars that can be changed depending on the selected sprite box

        self.set_values(render_method=render_method, loop_config=loop_configuration,
                        asset_name=asset_name,
                        layer_num=layer_num, width=width, height=height,
                        pos_x=x_pos, pos_y=y_pos, alpha=DEFAULT_ALPHA, sprite_box=sprite_box)

        self.width_input_widget = None
        self.height_input_widget = None

    def init_ui(self):
        self.setWindowTitle(WIN_TITLE)
        self.show()
        self.setFixedSize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.layout = QGridLayout()

        # Position, scale and alpha related fields
        position_attrs = PositionAttributes(default_x=self.x_pos, default_y=self.y_pos,
                                            default_width=self.width, default_height=self.height,
                                            default_alpha=self.alpha)

        self.x_pos_input_widget = position_attrs.x_pos_input_field
        self.y_pos_input_widget = position_attrs.y_pos_input_field
        self.width_input_widget = position_attrs.width_input_field
        self.height_input_widget = position_attrs.height_input_field
        self.alpha_input_widget = position_attrs.alpha_input_field

        self.x_pos_input_widget.textChanged.connect(self.set_x_pos)
        self.y_pos_input_widget.textChanged.connect(self.set_y_pos)
        self.width_input_widget.textChanged.connect(self.set_width)
        self.height_input_widget.textChanged.connect(self.set_height)
        self.alpha_input_widget.textChanged.connect(self.set_alpha)

        # Assets section. Has a a way to chose assets, filter their names and display the frame count.
        asset_name_label = QLabel(ASSET_NAME_STR)
        asset_filter_line = QLineEdit()
        self.assets_combo_box = QComboBox()
        frame_str_label = QLabel(FRAME_COUNT_STR)
        self.frame_count_label = QLabel(DEFAULT_FRAME_COUNT)
        asset_filter_line.textChanged.connect(self.filter_asset_names)
        self.populate_assets()
        self.assets_combo_box.activated.connect(self.set_asset_name)

        # Layers can be chosen from 1 to 10
        layer_label = QLabel(LAYER_STR)
        self.layer_combo_box = QComboBox()
        self.populate_layers(self.layer_combo_box, self.layer)
        self.layer_combo_box.activated.connect(self.set_layer)

        # Explanation of what layers mean. Set to different color, so that are separated from the
        # rest of the labels
        layer_explanation_label = QLabel(LAYER_EXAPLANATION_STR)
        layer_explanation_label.setStyleSheet("color: %s" % (EXPLANATION_COLOR))

        # Radial buttons - render method and loop configuration.
        render_method_label = QLabel(RENDER_METHOD_STR)
        render_method_radio_bttns_line = RadioButtonsLine(RENDER_MEHTODS, self.render_method)
        self.render_method_bttns_dict = render_method_radio_bttns_line.radio_buttons

        # Looping through a dict didn't work so
        # for render_method, render_button in self.render_method_bttns_dict.iteritems():
        #     render_button.toggled.connect(lambda: self.set_render_method(render_button))
        self.render_method_bttns_dict["RGBA"].toggled.connect(
            lambda: self.set_render_method(self.render_method_bttns_dict["RGBA"]))
        self.render_method_bttns_dict["Eye Color"].toggled.connect(
            lambda: self.set_render_method(self.render_method_bttns_dict["Eye Color"]))

        loop_configuration_label = QLabel(LOOP_CONFIGURATION_STR)
        loop_configuration_bttns_line = RadioButtonsLine(LOOP_CONFIGURATIONS,
                                                         self.loop_configuration)
        self.loop_configuration_bttns_dict = loop_configuration_bttns_line.radio_buttons

        # for loop_config, button in self.loop_configuration_bttns_dict.iteritems():
        #     button.toggled.connect(lambda: self.set_loop_configuration(loop_config))
        self.loop_configuration_bttns_dict["Clear"].toggled.connect(
            lambda: self.set_loop_configuration(self.loop_configuration_bttns_dict["Clear"]))
        self.loop_configuration_bttns_dict["Hold"].toggled.connect(
            lambda: self.set_loop_configuration(self.loop_configuration_bttns_dict["Hold"]))
        self.loop_configuration_bttns_dict["Loop"].toggled.connect(
            lambda: self.set_loop_configuration(self.loop_configuration_bttns_dict["Loop"]))

        self.update_radial_bttns()

        # Buttons for creating sprites and setting a sprite keyframe.
        if self.sets_keyframe:
            self.sprite_box_bttn = QPushButton(SET_SPRITE_BOX_KEYFRAME_STR)
        else:
            self.sprite_box_bttn = QPushButton(CREATE_SPRITE_BOX_STR)

        self.toggle_sprite_creation_bttn(self.sets_keyframe)

        # Adding widgets to the grid
        self.layout.addWidget(asset_name_label, 0, 0)
        self.layout.addWidget(self.assets_combo_box, 0, 1)
        self.layout.addWidget(asset_filter_line, 0, 2)
        self.layout.addWidget(frame_str_label, 1, 0)
        self.layout.addWidget(self.frame_count_label, 1, 1)
        self.layout.addWidget(layer_label, 2, 0)
        self.layout.addWidget(self.layer_combo_box, 2, 1)
        self.layout.addWidget(layer_explanation_label, 3, 0, 1, 2)
        self.layout.addWidget(render_method_label, 5, 0)
        self.layout.addWidget(render_method_radio_bttns_line, 6, 0, 1, 2)
        self.layout.addWidget(loop_configuration_label, 7, 0)
        self.layout.addWidget(loop_configuration_bttns_line, 8, 0, 1, 2)
        self.layout.addWidget(position_attrs, 9, 0, 1, 3)
        self.layout.addWidget(self.sprite_box_bttn, 12, 0, 1, 3)

        self.layout.setAlignment(Qt.AlignTop)
        self.setLayout(self.layout)

        self.time_change_callback_id = timeline_callbacks.addTimeChangeCallback(self.refresh_ui)
        self.selection_change_callback_id = timeline_callbacks.addSelctionChangeCallback(
            self.refresh_ui)

    def toggle_sprite_creation_bttn(self, sets_keyframe):
        try:
            self.sprite_box_bttn.clicked.disconnect()
        except RuntimeError:
            print "Can't disconnect sprite box key button"
        if not sets_keyframe:
            self.sprite_box_bttn.clicked.connect(
                lambda: sbc.create_sprite_box_polygon(layer_num=self.layer,
                                                      pos_x=self.x_pos,
                                                      pos_y=self.y_pos, width=self.width,
                                                      height=self.height,
                                                      render_method=self.render_method,
                                                      loop_config=self.loop_configuration,
                                                      asset_name=self.asset_name,
                                                      asset_enum_list=self.asset_names,
                                                      alpha_value=self.alpha))
            self.sprite_box_bttn.setText(CREATE_SPRITE_BOX_STR)

        elif self.sprite_box:
            self.sprite_box_bttn.clicked.connect(
                lambda: sbc.set_sprite_box_keyframe(sprite_box=self.sprite_box,
                                                    render_method=self.render_method,
                                                    loop_config=self.loop_configuration,
                                                    asset_name=self.asset_name,
                                                    layer=self.layer, width=self.width,
                                                    height=self.height, pos_x=self.x_pos,
                                                    pos_y=self.y_pos, alpha_value=self.alpha))
            self.sprite_box_bttn.setText(SET_SPRITE_BOX_KEYFRAME_STR)

        else:
            # Should never reach this
            mc.error("Need to specify sprite box to set keyframe")

    def refresh_ui(self, arg=None):
        selected_objs = mc.ls(sl=True)
        if selected_objs and len(selected_objs) == 1 and "SpriteBox" in selected_objs[0]:
            pos_x, pos_y, width, height, asset_name, render_method, loop_config, alpha, layer = \
                sbc.get_sprite_box_attrs(selected_objs[0])
            self.set_ui_attrs(render_method=render_method, loop_config=loop_config,
                              asset_name=asset_name,
                              layer_num=layer, width=width, height=height, pos_x=pos_x, pos_y=pos_y,
                              alpha=alpha, sprite_box=selected_objs[0])
            self.toggle_sprite_creation_bttn(True)
        else:
            # If the sprite box is not selected need to go into creation mode and set
            # parameters to default
            self.toggle_sprite_creation_bttn(False)

    # Setters

    def set_frame_count(self, frame_count):
        """
        Set frame number depending on the chosen asset - each has a different frame count
        """
        self.frame_count_label.setText(str(frame_count))

    def set_x_pos(self, x_pos):
        self.x_pos = x_pos

    def set_y_pos(self, y_pos):
        self.y_pos = y_pos

    def set_layer(self):
        layer_name = self.layer_combo_box.currentText()
        self.layer = layer_name

    def set_width(self, width):
        self.width = width
        self.width_input_widget.setText(str(width))

    def set_height(self, height):
        self.height = height
        self.height_input_widget.setText(str(height))

    def set_alpha(self, alpha):
        self.alpha = alpha

    def set_loop_configuration(self, radio_button):
        if radio_button.isChecked():
            self.loop_configuration = radio_button.text()

    def set_render_method(self, radio_button):
        if radio_button.isChecked():
            self.render_method = radio_button.text()

    def set_asset_name(self):
        """
        Set asset name and change frame count number
        """
        self.asset_name = self.assets_combo_box.currentText()
        if self.asset_name in self.asset_names_and_paths:
            file_path = self.asset_names_and_paths[self.asset_name]
            if (file_path) and os.path.isfile(file_path):
                frame_count = image_files.get_image_file_count(file_path)
                self.set_width(image_files.get_pixel_width(file_path))
                self.set_height(image_files.get_pixel_height(file_path))
                self.set_frame_count(frame_count)
            else:
                # This becomes important if we switch from asset with non-default params to clear
                self.set_width(SPRITE_DEFAULT_WIDTH)
                self.set_height(SPRITE_DEFAULT_HEIGHT)
                self.set_frame_count(0)

    def set_values(self, render_method=RGBA_STR, loop_config=CLEAR_STR,
                   asset_name=DEFAULT_ASSET_NAME,
                   layer_num=LAYER_NUM, width=SPRITE_DEFAULT_WIDTH, height=SPRITE_DEFAULT_HEIGHT,
                   pos_x=0.0, pos_y=0.0, alpha=DEFAULT_ALPHA, sprite_box=None):
        """
        Set values of member vars so that they can be used to populate the ui.
        """
        self.asset_name = asset_name
        self.render_method = camel_case_2_spaces(render_method)
        self.loop_configuration = camel_case_2_spaces(loop_config)
        self.x_pos = str(pos_x)
        self.y_pos = str(pos_y)
        self.width = str(width)
        self.height = str(height)
        self.alpha = str(alpha)
        self.layer = layer_num
        if sprite_box:
            self.sprite_box = sprite_box

    def set_ui_attrs(self, render_method=RGBA_STR, loop_config=CLEAR_STR,
                     asset_name=DEFAULT_ASSET_NAME,
                     layer_num=LAYER_NUM, width=SPRITE_DEFAULT_WIDTH, height=SPRITE_DEFAULT_HEIGHT,
                     pos_x=0.0, pos_y=0.0, alpha=DEFAULT_ALPHA, sprite_box=None):
        """
        Set values of ui elements.
        """
        self.set_values(render_method=render_method, loop_config=loop_config,
                        asset_name=asset_name,
                        layer_num=layer_num, width=width, height=height, pos_x=pos_x, pos_y=pos_y,
                        alpha=alpha, sprite_box=sprite_box)
        self.x_pos_input_widget.setText(str(self.x_pos))
        self.y_pos_input_widget.setText(str(self.y_pos))
        self.width_input_widget.setText(str(self.width))
        self.height_input_widget.setText(str(self.height))
        self.alpha_input_widget.setText(str(self.alpha))
        set_enum_by_str(self.assets_combo_box, self.asset_name)
        self.set_asset_name()
        set_enum_by_str(self.layer_combo_box, self.layer)
        self.update_radial_bttns()

    def update_radial_bttns(self):
        """
        Turn on buttons that correspond to current render method and loop config
        """
        if self.render_method in self.render_method_bttns_dict:
            self.render_method_bttns_dict[self.render_method].setChecked(True)

        if self.loop_configuration in self.loop_configuration_bttns_dict:
            self.loop_configuration_bttns_dict[self.loop_configuration].setChecked(True)

    def filter_asset_names(self, filter_text):
        """
        Used to filter the name of the assets in the combo box by typing in their names.
        """
        filter_text = filter_text.lower()
        self.assets_combo_box.clear()
        for asset in self.asset_names:
            if filter_text in asset.lower():
                self.assets_combo_box.addItem(asset)
        # Since the current text of the asset can change when filtering, need to update it
        self.set_asset_name()

    def populate_layers(self, layer_combo_box, layer_num=LAYER_NUM):
        """
        Add 10 layers to the combo box (from 1 to 10)
        """
        for i in range(1, int(LAYER_NUM) + 1):
            layer_combo_box.addItem(str(i))

        set_enum_by_str(layer_combo_box, str(layer_num))

    def populate_assets(self):
        populate_assets_and_path_dict(self.asset_names_and_paths)
        self.asset_names = self.asset_names_and_paths.keys()
        for asset in self.asset_names:
            self.assets_combo_box.addItem(asset)
        set_enum_by_str(self.assets_combo_box, self.asset_name)
        self.set_asset_name()

    def closeEvent(self, *args, **kwargs):
        timeline_callbacks.removeTimeChangeCallback(self.time_change_callback_id)
        timeline_callbacks.removeSelctionChangeCallback(self.selection_change_callback_id)


class RadioButtonsLine(QWidget):
    def __init__(self, radio_button_names=[], active_bttn_name=""):
        super(RadioButtonsLine, self).__init__()
        self.layout = QHBoxLayout()
        self.radio_buttons = {}  # name:radio_button, so that to find the object from it's name

        for radio_bttn_name in radio_button_names:
            radio_bttn = QRadioButton(radio_bttn_name)
            self.layout.addWidget(radio_bttn)
            radio_bttn.setAutoExclusive(True)
            if radio_bttn_name == active_bttn_name:
                radio_bttn.setChecked(True)
            self.radio_buttons[radio_bttn_name] = radio_bttn
        self.setLayout(self.layout)


class PositionAttributes(QWidget):
    """
    Making this a separate widget to align better with the rest of
    the main widget
    """

    def __init__(self, default_x="0", default_y="0",
                 default_width=SPRITE_DEFAULT_WIDTH, default_height=SPRITE_DEFAULT_HEIGHT,
                 default_alpha=DEFAULT_ALPHA):
        super(PositionAttributes, self).__init__()
        self.layout = QGridLayout()
        # X and Y positions with limits between -184 and 184 and -96 and 96
        x_pos_label = QLabel(X_POS_STR)
        self.x_pos_input_field = self.add_input_field_with_regex(default_x,
                                                                 REGEX_MIN_184_TO_184)
        y_pos_label = QLabel(Y_POS_STR)
        self.y_pos_input_field = self.add_input_field_with_regex(default_y,
                                                                 REGEX_MIN_96_TO_96)

        # Width and height with limits between 0 and 184 and 0 and 96
        width_label = QLabel(WIDTH_STR)
        self.width_input_field = self.add_input_field_with_regex(str(default_width),
                                                                 REGEX_0_TO_184)
        height_label = QLabel(HEIGHT_STR)
        self.height_input_field = self.add_input_field_with_regex(str(default_height),
                                                                  REGEX_0_TO_96)
        alpha_label = QLabel(ALPHA_STR)
        self.alpha_input_field = self.add_input_field_with_regex(str(default_alpha),
                                                                 REGEX_0_TO_100)

        self.layout.addWidget(x_pos_label, 0, 0, 1, 1, Qt.AlignRight)
        self.layout.addWidget(self.x_pos_input_field, 0, 1, 1, 2)
        self.layout.addWidget(y_pos_label, 0, 3, 1, 1, Qt.AlignRight)
        self.layout.addWidget(self.y_pos_input_field, 0, 4, 1, 2)
        self.layout.addWidget(width_label, 1, 0, 1, 1, Qt.AlignRight)
        self.layout.addWidget(self.width_input_field, 1, 1, 1, 2)
        self.layout.addWidget(height_label, 1, 3, 1, 1, Qt.AlignRight)
        self.layout.addWidget(self.height_input_field, 1, 4, 1, 2)
        self.layout.addWidget(alpha_label, 2, 0, 1, 1, Qt.AlignRight)
        self.layout.addWidget(self.alpha_input_field, 2, 1, 1, 2)

        self.setLayout(self.layout)

    def add_input_field_with_regex(self, default_str, regex):
        input_field = QLineEdit(default_str)
        rx = QRegExp(regex)
        validator = QRegExpValidator(rx, self)
        input_field.setValidator(validator)
        return input_field


def camel_case_2_spaces(camel_case_string):
    return re.sub("([a-z])([A-Z])", "\g<1> \g<2>", camel_case_string)


def set_enum_by_str(combo_box, enum_str):
    enum_idx = combo_box.findText(enum_str, Qt.MatchFixedString)
    if enum_idx >= 0:
        combo_box.setCurrentIndex(enum_idx)


def populate_assets_and_path_dict(asset_names_and_paths):
    assets = {}
    # Go through the dir recursively and add all the png and tar files names to the list
    for root, dirs, files in os.walk(SPRITES_PATH):
        for name in files:
            if "." in name and name.split(".")[-1] == "png" or name.split(".")[-1] == "tar":
                no_extension_name = name.split(".")[0]
                asset_names_and_paths[no_extension_name] = (os.path.join(root, name))


def main():
    selected_objs = mc.ls(sl=True)
    if selected_objs and len(selected_objs) == 1 and "SpriteBox" in selected_objs[0]:
        pos_x, pos_y, width, height, asset_name, render_method, loop_config, alpha, layer = \
            sbc.get_sprite_box_attrs(selected_objs[0])
        ui = MainWindow(True, pos_x, pos_y, width, height, asset_name,
                        render_method, loop_config, alpha, layer, selected_objs[0])
    else:
        ui = MainWindow(sets_keyframe=False)
    ui.init_ui()
