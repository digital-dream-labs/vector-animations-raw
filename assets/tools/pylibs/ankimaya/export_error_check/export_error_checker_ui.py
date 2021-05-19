"""
The UI part of the error export tool.

Needs export_error_checker.json in the same directory as this file,
and also a user specific json file in anki/maya. If the latter
doesn't exist it gets copied to that directory from the original
export_error_checker.json.
That allows to preserve the information on the most recent checks
even in case of closing/crashing of maya or reloading the tool.

StepsContainer is the central part of the tool which consists of a
tree of error groups as well as information on whether the checks
for the listed errors have passed or not

DisplaySettings is the part on the top of the UI where user can
chose to change the visibility of different errors depending on
their type. Under the hood it re-creates the tree ommiting the
checks that have a status we don't need

TopButtons includes three buttons for user to force a check of post
or pre export checks or reset the check - which copies the original
json file to the one in anki/maya.

BottomButtons contains of three buttons that run fixes on the
selected steps or export animation clips ignoring the error checks.

ExporterCheckWidget is the main widget that calls all the other ones.
"""

WINDOW_TITLE = "Exporter Error Check"

STEP_CHECKBOX_TOOL_TIP = "Select elements to preform a fix on"
STEP_WIDTH = 90
STEP_LABEL_WIDTH = 28
EXPAND_TO_DEPTH = 1
MESSAGE_COLUMN_WIDTH = 500

STATUS_COLOR_DICT = {"error": "red", "warning": "orange", "pass": "green"}
DEFAULT_DISPLAY_TYPES = STATUS_COLOR_DICT.keys()
DEFAULT_MESSAGE_COLOR = "yellow"
DEFAULT_STATUS_COLOR = "white"

MESSAGE_STR = "message"
STATUS_STR = "status"
NAME_STR = "name"
TOOL_TIP_STR = "tool_tip"
FIX_FUNCTION_STR = "fix_function"


import os
import json
import maya.cmds as mc

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

from ankimaya.export_error_check.export_error_checker import run_pre_export_checks
from ankimaya.export_error_check.export_error_checker import run_post_export_checks
from ankimaya.export_error_check.error_checker_utils import add_user_json_file, update_anim_jsons
from ankimaya.export_error_check.error_checker_utils import JSON_FILE, USER_JSON_FILE, optimize_json
from ankimaya.export_error_check import export_error_fixes as fixes
from ankimaya.window_docker import Dock


# Global variable
_dockControl = None


class ExporterCheckWidget(QWidget):
    """
    Main widget that references all the other ones and is responsible
    for their functionality.

    When creating an instance of this class, you must pass in an
    'exporter_func' keyword argument to indicate the function
    that should be used for exporting and that is typically the
    export_for_robot.export_robot_anim() function.
    """
    def __init__(self, *args, **kwargs):
        if 'exporter_func' in kwargs:
            self.exporter_func = kwargs.pop('exporter_func')
        else:
            raise ValueError("The 'exporter_func' keyword argument should be passed in and that is "
                             "typically set to the export_for_robot.export_robot_anim() function")
        super(ExporterCheckWidget, self).__init__(*args, **kwargs)
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        display_settings = DisplaySettings()
        self.current_display_types = DEFAULT_DISPLAY_TYPES

        error_checkbox = display_settings.error_checkbox
        warning_checkbox = display_settings.warnings_checkbox
        log_checkbox = display_settings.logs_checkbox

        error_checkbox.stateChanged.connect(
            lambda: self.on_changed_display_settings("error", error_checkbox.isChecked()))
        warning_checkbox.stateChanged.connect(
            lambda: self.on_changed_display_settings("warning", warning_checkbox.isChecked()))
        log_checkbox.stateChanged.connect(
            lambda: self.on_changed_display_settings("pass", log_checkbox.isChecked()))

        top_buttons = TopButtons()
        self.steps_container = StepsContainer()

        bottom_buttons = BottomButtons()

        layout.addWidget(display_settings)
        layout.addWidget(top_buttons)
        layout.addWidget(bottom_buttons)
        layout.addWidget(self.steps_container)

        top_buttons.reset_check_button.clicked.connect(
            lambda: self.steps_container.reset_steps(None))
        top_buttons.pre_export_button.clicked.connect(lambda: self.on_pre_export())
        top_buttons.export_button.clicked.connect(lambda: export_with_error_check(self.exporter_func))

        bottom_buttons.export_anyway_bttn.clicked.connect(self.exporter_func)
        bottom_buttons.fix_selected_bttn.clicked.connect(self.run_fixes)

        self.steps_container.draw_tree()

    def on_pre_export(self):
        run_pre_export_checks()
        self.steps_container.draw_tree()

    def on_changed_display_settings(self, display_type, is_checked):
        if is_checked and display_type not in self.current_display_types:
            self.current_display_types.append(display_type)
        elif not is_checked and display_type in self.current_display_types:
            self.current_display_types.remove(display_type)
        self.steps_container.draw_tree(display_types=self.current_display_types)

    def run_fixes(self):
        selected_step_names = self.steps_container.get_checked()
        name2node_dict = self.steps_container.name2node_dict
        fixes.run_fixes(selected_step_names, name2node_dict)

    def close(self):
        mc.deleteUI(_dockControl)


class StepsContainer(QWidget):
    """
    Central part of the UI
    Steps are displayed in form a tree widget. Their names and statuses
    are displayed by default. Change EXPAND_TO_DEPTH to display their
    messages when the tool opens.
    """
    def __init__(self, display_types=DEFAULT_DISPLAY_TYPES, json_path=JSON_FILE,
                 user_json_path=USER_JSON_FILE, *args, **kwargs):
        super(StepsContainer, self).__init__(*args, **kwargs)
        self.steps_dict = {}
        self.json_path = json_path
        self.user_json_path = user_json_path
        # If user doesn't have a json file with steps info copy clean one from the repo,
        # if they do, open with the previously populated steps
        if not os.path.exists(user_json_path):
            add_user_json_file(json_path=self.json_path, user_json_path=self.user_json_path)
        if self.user_json_path is None:
            return
        self.populate_steps()
        self.display_types = display_types
        self.step_widgets = []
        self.selected_step_widgets = []
        self.error_steps = []
        self.warning_steps = []
        self.log_steps = []
        self.name2node_dict = {} # To get fix function from the name of the node
        self.title_widgets = []
        self.initUI()

    def initUI(self):
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.tree = None
        self.draw_tree()
        self.show()

    def draw_tree(self, display_types=None):
        if self.tree:
            self.layout.removeWidget(self.tree)
        self.populate_steps()
        self.tree = QTreeWidget()
        if not display_types:
            self.display_types = DEFAULT_DISPLAY_TYPES
        else:
            self.display_types = display_types
        self.tree.setColumnCount(2)
        self.tree.setHeaderLabels(["Step name", STATUS_STR.capitalize()])
        self.tree.setColumnWidth(0, MESSAGE_COLUMN_WIDTH)
        self.add_element_to_tree(self.steps_dict, self.tree)
        self.tree.expandToDepth(EXPAND_TO_DEPTH)
        self.layout.addWidget(self.tree)

    def populate_steps(self):
        """
        Populates steps displayed in a tree from a json file
        (part of drawing a tree of messages)
        """
        with open(self.user_json_path, "r+") as data_file:
            self.steps_dict = json.load(data_file)
        optimize_json(self.steps_dict)

    def reset_steps(self, display_types=None):
        """
        Copies default message info from the public json file
        (in the same dir as code)
        """
        add_user_json_file(json_path=self.json_path, user_json_path=self.user_json_path)
        self.draw_tree(display_types=display_types)

    def add_element_to_tree(self, element, parent_element):
        """
        Recursive function. Adds a node to the tree of messages
        """
        if isinstance(element, dict):
            if NAME_STR in element.keys():
                # leaf
                self.add_leaf_node(element, parent_element)
            else:
                for key, value in element.iteritems():
                    # branch
                    if value:
                        new_node = self.add_parent_node(key, parent_element)
                        self.add_element_to_tree(value, new_node)
        elif isinstance(element, list):
            for item in element:
                self.add_element_to_tree(item, parent_element)
        else:
            print("add_element_to_tree: %s element not accepted" % element)

    def add_parent_node(self, node_name, parent_node):
        """
        Add a parent node when populating the tree of messages
        """
        tree_node = QTreeWidgetItem(parent_node)
        tree_node.setText(0, node_name)
        node_font = QFont()
        node_font.setBold(True)
        # Only make the first nodes large
        size = QSize(15, 15)
        if type(parent_node) == QTreeWidget:
            size = QSize(25, 25)
            node_font.setPointSize(14)
        tree_node.setSizeHint(0, size)
        tree_node.setFont(0, node_font)
        return tree_node

    def add_leaf_node(self, node_dict, parent_node):
        """
        Add a leaf node when poopulating message dictionary.
        It needs to have a name key.
        """
        if NAME_STR in node_dict.keys() and node_dict[STATUS_STR] in self.display_types:
            leaf_node = QTreeWidgetItem(parent_node)
            leaf_node.setText(0, node_dict[NAME_STR])

            self.set_status(node_dict[STATUS_STR], leaf_node)
            node_font = QFont()
            # Making bold to separate between messages and node titles
            node_font.setBold(True)
            leaf_node.setFont(0, node_font)
            if FIX_FUNCTION_STR in node_dict and node_dict[FIX_FUNCTION_STR] != "":
                leaf_node.setFlags(leaf_node.flags() | Qt.ItemIsUserCheckable)
                leaf_node.setCheckState(0, Qt.Unchecked)
            self.name2node_dict[node_dict[NAME_STR]] = node_dict
            self.title_widgets.append(leaf_node)

            if MESSAGE_STR in node_dict and node_dict[MESSAGE_STR] != "":
                if TOOL_TIP_STR in node_dict:
                    message_widget = self.create_message_widget(node_dict[STATUS_STR],
                                                                node_dict[MESSAGE_STR],
                                                                node_dict[TOOL_TIP_STR])
                else:
                    message_widget = self.create_message_widget(node_dict[STATUS_STR],
                                                                node_dict[MESSAGE_STR])
                message_widget.setWordWrap(True)
                sub_leaf_node = QTreeWidgetItem(leaf_node)
                self.tree.setItemWidget(sub_leaf_node, 0, message_widget)
                leaf_node.addChild(sub_leaf_node)

    def create_message_widget(self, status, message="", tool_tip=""):
        """
        For some reason this makes maya crash, if not placed in a separate function
        """
        try:
            color = STATUS_COLOR_DICT[status]
        except KeyError:
            color = DEFAULT_MESSAGE_COLOR
        if isinstance(message, list):
            message = os.linesep.join(message)
        elif not (isinstance(message, str) or isinstance(message, unicode)):
            message = "Wrong message type %s%s%s" % (type(message), os.linesep, str(message))
        message_widget = QLabel(message)
        message_widget.setStyleSheet("color: %s" % (color))
        if tool_tip != "":
            message_widget.setToolTip(tool_tip)
        self.step_widgets.append(message_widget)
        return message_widget

    def set_status(self, status, leaf_node):
        leaf_node.setText(1, status)
        status_font = QFont()
        status_font.setBold(True)
        leaf_node.setFont(1, status_font)
        brush = QBrush()
        try:
            brush.setColor(STATUS_COLOR_DICT[status])
        except KeyError:
            brush.setColor(DEFAULT_STATUS_COLOR)
        leaf_node.setForeground(1, brush)

        # Uncomment the following to set the color of the title (right now setting color
        # of the message, but might be better to change title as well or instead)
        # leaf_node.setForeground(0, brush)

    def get_checked(self):
        checked = []
        for title_widget in self.title_widgets:
            if title_widget.checkState(0) == Qt.Checked:
                checked.append(title_widget.text(0))
        return checked


class DisplaySettings(QWidget):
    def __init__(self, *args, **kwargs):
        super(DisplaySettings, self).__init__(*args, **kwargs)
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout()
        layout.setAlignment(Qt.AlignLeft)
        label = QLabel("Display: ")
        errors_section = DisplaySection("Errors: ")
        warnings_section = DisplaySection("Warnings: ")
        log_section = DisplaySection("Log: ")

        self.error_checkbox = errors_section.checkBox
        self.warnings_checkbox = warnings_section.checkBox
        self.logs_checkbox = log_section.checkBox

        layout.addWidget(label)
        layout.addWidget(errors_section)
        layout.addWidget(warnings_section)
        layout.addWidget(log_section)

        self.setLayout(layout)


class DisplaySection(QWidget):
    def __init__(self, text="", *args, **kwargs):
        super(DisplaySection, self).__init__(*args, **kwargs)
        layout = QHBoxLayout()
        layout.setAlignment(Qt.AlignLeft)
        label = QLabel(text)
        self.checkBox = QCheckBox()
        # By default display all the messages
        self.checkBox.setChecked(True)

        layout.addWidget(label)
        layout.addWidget(self.checkBox)
        self.setLayout(layout)


class BottomButtons(QWidget):
    """
    Three buttons at the bottom of the tool.
    """
    def __init__(self, steps=None, *args, **kwargs):
        super(BottomButtons, self).__init__(*args, **kwargs)
        self.layout = QHBoxLayout()
        self.layout.setAlignment(Qt.AlignCenter)
        self.fix_selected_bttn = self.add_button("Fix Selected")
        self.export_anyway_bttn = self.add_button("Export Anyway")
        self.setLayout(self.layout)

    def add_button(self, name=""):
        new_button = QPushButton(name)
        self.layout.addWidget(new_button)
        return new_button


class TopButtons(QWidget):
    """
    Three buttons on the top of the tool.
    """
    def __init__(self, *args, **kwargs):
        super(TopButtons, self).__init__(*args, **kwargs)
        self.layout = QHBoxLayout()
        self.layout.setAlignment(Qt.AlignCenter)
        self.pre_export_button = self.add_button("Pre-Export Check")
        self.export_button = self.add_button("Export")
        self.reset_check_button = self.add_button("Reset check")
        self.setLayout(self.layout)

    def add_button(self, name=""):
        new_button = QPushButton(name)
        self.layout.addWidget(new_button)
        return new_button


def export_with_error_check(exporter_func):
    """
    When calling this function, pass in the function that
    should be used for exporting, which is typically
    export_for_robot.export_robot_anim()
    """
    global _dockControl
    add_user_json_file()
    run_pre_export_checks()
    output_files = exporter_func()
    if output_files:
        run_post_export_checks(output_files)
    try:
        mc.deleteUI(WINDOW_TITLE)
    except:
        pass
    ui, dockWidget, _dockControl = Dock(ExporterCheckWidget, width=350, winTitle=WINDOW_TITLE,
                                        exporter_func=exporter_func)
    ui.setObjectName(WINDOW_TITLE)
    return ui


