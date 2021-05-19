"""
UI for easy rendering of the robot's face.

This rendering tool sets the start/end frames for the render to be
the same start/end frames of the timeline. This tool gives ability
to create selection sets, which, if they have selection correspond
to the render layers, can be viewed under
Windows -> Rendering Editors -> Render Setup.
"""

import os
import math
import maya.cmds as mc
from maya import OpenMayaUI as omui
import maya.app.renderSetup.model.renderSetup as renderSetup

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

from ankimaya import render_for_robot
from ankimaya.anim_clip_utils import is_there_intersecting_clip


DEFAULT_NAME = "face_render"

CAMERA_NAME = "x:png_cam"

RENDER_NODE_NAME = "render_data_storage"

SELECTION_SET_ENUM_ATTR = "empty_selection_sets"

WIN_TITLE = "Face Renderer"
WINDOW_WIDTH = 640
WINDOW_HEIGHT = 210
START_FRAME_LABEL = "Start frame"
END_FRAME_LABEL = "End frame"
ADD_SELECTION_BUTTON_LABEL = "Add selection as render set"
RENDER_BUTTON_LABEL = "Render"
FRAME_NUM_STR = "Frame number in rendered file names starts from zero"

MESH_STR = "mesh"


mayaMainWindowPtr = omui.MQtUtil.mainWindow()
mayaMainWindow = wrapInstance(long(mayaMainWindowPtr), QWidget)


def get_geo_selection():
    """
    Get only selected geometry out of all selected objects
    (this avoids problems like accidentally selected groups)
    """
    selected_geo = []
    all_selection = mc.ls(sl=True)
    all_shapes = mc.ls(type=MESH_STR)
    all_geo = mc.listRelatives(all_shapes, parent=True)
    for selection in all_selection:
        if selection in all_geo:
            selected_geo.append(selection)
    return selected_geo


def get_default_name(start_frame, end_frame):
    """
    Default name should be the name of the clip id it's set,
    Otherwise should be the name of the maya scene and if the
    scene doesn't have a name - a chosen default name
    """
    try:
        clip_name = is_there_intersecting_clip(float(start_frame), float(end_frame), True)
    except (ValueError, TypeError):
        clip_name = None
    if clip_name:
        return clip_name
    filepath = mc.file(q=True, sn=True)
    if filepath:
        filename = os.path.basename(filepath)
        return filename.split(".")[0]
    else:
        return DEFAULT_NAME


def _at_least_one_selection_set_active(selection_sets):
    for selection_set in selection_sets:
        if selection_set.included:
            return True
    return False


class MainWindow(QWidget):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setParent(mayaMainWindow)
        self.setWindowFlags(Qt.Window)
        self.selection_sets = []

    def init_ui(self):
        self.setWindowTitle(WIN_TITLE)
        self.show()
        # Can also set min size, but didn't look as nice self.setMinimumSize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.setFixedSize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.layout = QGridLayout()
        start_frame_label = QLabel(START_FRAME_LABEL)
        end_frame_label = QLabel(END_FRAME_LABEL)
        self.start_frame_num_from_zero = False
        self.frame_num_checkbox = QCheckBox(FRAME_NUM_STR)
        self.frame_num_checkbox.setChecked(False)
        self.frame_num_checkbox.stateChanged.connect(self.set_frame_num_naming)
        add_selection_button = QPushButton(ADD_SELECTION_BUTTON_LABEL)
        self.init_scroll_area()
        default_start_frame = str(int(math.floor(mc.playbackOptions(q=True, min=True))))
        default_end_frame = str(int(math.ceil(mc.playbackOptions(q=True, max=True))))
        self.start_frame = default_start_frame
        self.end_frame = default_end_frame
        start_frame_input = QLineEdit(default_start_frame)
        end_frame_input = QLineEdit(default_end_frame)
        start_frame_input.textChanged.connect(self.set_start_frame)
        end_frame_input.textChanged.connect(self.set_end_frame)
        render_button = QPushButton(RENDER_BUTTON_LABEL)
        render_button.clicked.connect(self.render)
        add_selection_button.clicked.connect(lambda: self.add_selection_set())

        # Adding widgets to the grid
        self.layout.addWidget(start_frame_label, 0, 0)
        self.layout.addWidget(start_frame_input, 0, 1)
        self.layout.addWidget(end_frame_label, 0, 2)
        self.layout.addWidget(end_frame_input, 0, 3)
        self.layout.addWidget(self.frame_num_checkbox, 1, 0, 1, 4)
        self.layout.addWidget(add_selection_button, 2, 0, 1, 4)
        self.layout.addWidget(self.scroll, 3, 0, 10, 4)
        self.layout.addWidget(render_button, 13, 0, 1, 4)

        self.layout.setAlignment(Qt.AlignTop)
        self.setLayout(self.layout)

        self.populate_selection_sets()

    def init_scroll_area(self):
        """
        The scroll area holds the list of one or more audio events to use
        """
        self.scroll_widget = QWidget()
        self.scroll_widget.setParent(self)
        self.scroll_layout = QVBoxLayout(self.scroll_widget)
        self.scroll_widget.setLayout(self.scroll_layout)
        self.scroll = QScrollArea(self)
        self.scroll.setWidgetResizable(True)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setWidget(self.scroll_widget)

    def add_selection_set(self, default_name=None, selection=None, overwrite_selection=True):
        """
        Add selection set widget to the scroll info and
        selection info to the list of selection sets.
        """
        if not selection:
            selection = get_geo_selection()
        if not default_name:
            default_name = get_default_name(self.start_frame, self.end_frame)
        selection_set = SelectionSet(selection, default_name)
        selection = filter(None, selection)
        # if user has objects selected, create corresponding render layer with those objects
        if selection:
            render_layer = render_for_robot.create_render_layer(selection, default_name,
                                                                overwrite_selection)
            selection_set.render_layer = render_layer
        self.selection_sets.append(selection_set)
        self.scroll_layout.addWidget(selection_set)

    def save_empty_names(self, enum_attr=SELECTION_SET_ENUM_ATTR,
                         render_data_node=RENDER_NODE_NAME, names_list=None):
        """
        Store the name of selection set that doesn't have a
        corresponding layer in a locator in the scene
        If render data node doesn't exist - create it
        """
        if not names_list:
            if mc.objExists(render_data_node):
                mc.delete(render_data_node)
            return
        elif not mc.objExists(render_data_node):
            render_data_node = mc.group(empty=True, name=render_data_node)
        if mc.objExists(render_data_node + "." + enum_attr):
            mc.deleteAttr(render_data_node, at=enum_attr)
        new_enum_str = ":".join(names_list)
        mc.addAttr(render_data_node, longName=enum_attr, attributeType="enum",
                   keyable=True, enumName=new_enum_str)

    def render(self):
        """
        Is called on pressing the render button.
        Renders based on created render layers and selection sets.
        """
        images_dir = None
        if self.selection_sets and _at_least_one_selection_set_active(self.selection_sets):
            for selection_set in self.selection_sets:
                render_layer = selection_set.render_layer
                if render_layer and selection_set.included:
                    # Render command accepts legacy render layers, so need to get that name
                    # The difference in the names is the "rs_" prefix in the beginning.
                    # We could get legacy render layer through "rs_"+selection_set.name
                    # Using _getLegacyNodeName() seems safer even though it's a private function
                    legacy_render_layer = render_layer._getLegacyNodeName()
                    render_layer_name = render_layer.name()
                    print("Rendering frames %s to %s for %s (using %s)"
                          % (self.start_frame, self.end_frame, render_layer_name, legacy_render_layer))
                    try:
                        image_files, images_dir = render_for_robot.render(CAMERA_NAME,
                                                      render_layer_name, self.start_frame,
                                                      self.end_frame, legacy_render_layer,
                                                      start_numbering_from_zero=self.start_frame_num_from_zero)
                    finally:
                        render_for_robot.show_default_render_layer()
                elif selection_set.included:
                    # If nothing is selected should render everything
                    print("Rendering frames %s to %s for %s"
                          % (self.start_frame, self.end_frame, selection_set.name))
                    image_files, images_dir = render_for_robot.render(CAMERA_NAME,
                                                  selection_set.name, self.start_frame, self.end_frame,
                                                  start_numbering_from_zero=self.start_frame_num_from_zero)
        else:
            default_name = get_default_name(self.start_frame, self.end_frame)
            print("Rendering frames %s to %s for %s"
                  % (self.start_frame, self.end_frame, default_name))
            image_files, images_dir = render_for_robot.render(CAMERA_NAME, default_name,
                                          self.start_frame, self.end_frame,
                                          start_numbering_from_zero=self.start_frame_num_from_zero)
        # Open the last render dir at the end (so that doesn't open multiple times)
        if images_dir:
            os.system("open %s" % images_dir)

    def set_start_frame(self, start_frame):
        self.start_frame = start_frame

    def set_end_frame(self, end_frame):
        self.end_frame = end_frame

    def set_frame_num_naming(self):
        self.start_frame_num_from_zero = self.frame_num_checkbox.isChecked()

    def populate_selection_sets(self, enum_attr=SELECTION_SET_ENUM_ATTR,
                                render_data_node=RENDER_NODE_NAME):
        """
        Called on tool's initialization.
        Populate selection sets from the render node (empty
        selections) and render layers (sets with selections).
        """
        # Populate selection sets that don't have render layers associated with them (no selections)
        if mc.objExists(render_data_node + "." + enum_attr):
            enums_as_str = mc.attributeQuery(enum_attr, node=render_data_node, listEnum=True)
            if enums_as_str:
                enums_as_str = enums_as_str[0]
                empty_selection_sets = enums_as_str.split(':')
                for selection_set in empty_selection_sets:
                    self.add_selection_set(default_name=selection_set)

        # Populate all the selection sets that have corresponding render layers
        render_layer_info = render_for_robot.get_render_layers_info()  # {layer_name:[selection]}
        for layer_name, selections in render_layer_info.iteritems():
            try:
                self.add_selection_set(layer_name, selections, False)
            except TypeError:
                continue

    def closeEvent(self, event):
        """
        On closing the tool
        Save un-named selection sets in a node in scene, so that on next time
        opening the tool, can re-populate them.
        """
        empty_sets = []
        for selection_set in self.selection_sets:
            if not selection_set.render_layer and selection_set.included:
                empty_sets.append(selection_set.name)
        self.save_empty_names(names_list=empty_sets)


class SelectionSet(QWidget):
    def __init__(self, selection, name):
        super(SelectionSet, self).__init__()
        layout = QHBoxLayout()
        name_input = QLineEdit(name)
        remove_button = QPushButton("-")
        layout.addWidget(name_input)
        layout.addWidget(remove_button)
        remove_button.clicked.connect(self.remove)
        name_input.textChanged.connect(self.set_name)
        self.setLayout(layout)
        self.included = True
        self.name = name
        self.selection = selection
        self.render_layer = None
        self.set_tool_tip()

    def remove(self):
        """
        Hides widget, removes render layer, makes not included
        """
        self.hide()
        self.included = False
        render_setup = renderSetup.instance()
        render_setup.detachRenderLayer(self.render_layer)
        self.render_layer = None

    def set_name(self, input_name):
        """
        Sets the name of the selection set, changes spaces to underscores
        """
        self.name = input_name.replace(" ", "_")
        if self.render_layer:
            self.render_layer.setName(self.name)

    def set_tool_tip(self):
        """
        Creates tool tip with the name of the selected objects
        """
        if self.selection:
            tool_tip = os.linesep.join(self.selection)
        else:
            tool_tip = "No selections are added to this set, will render everything."
        self.setToolTip(tool_tip)


def main():
    ui = MainWindow()
    ui.init_ui()


