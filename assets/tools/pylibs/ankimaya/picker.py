
# TODO make multiple objects into 1 selection
# TODO move AAIW up so there is no blank space
# TODO grid layout for 2 rows

import os
import os.path
import json
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

from picker_add_selection import PickerAddWidget
from window_docker import Dock

# These modules are used in picker.json
import ankimaya.mirror_ctrs
import ankimaya.eyes_distance


_globalDockControl = None


WIN_TITLE = "Victor Picker"
FIXED_WIDTH = 360
MAIN_IMAGE_PARAMETERS = [350.0, 540.0]
DOCKING_WINDOW = ['MacBlast', 'ChannelBoxLayerEditor', 'AttributeEditor']
JSON_FILE = os.path.join(os.path.dirname(__file__), "picker.json")
TOOLS_DIR_ENV_VAR = "ANKI_TOOLS"
UI_ICONS_DIR = os.path.join(os.getenv(TOOLS_DIR_ENV_VAR), "icons", "PickerUI")
PICKER_BG_PNG = os.path.join(UI_ICONS_DIR, "picker_bg.png")
WINDOW_ICONS_DIR = os.path.join(os.getenv(TOOLS_DIR_ENV_VAR), "icons", "PreviewSelectorUI")

CLOSE_ICON = os.path.join(WINDOW_ICONS_DIR, "close.png")
WIN1_ICON = os.path.join(WINDOW_ICONS_DIR, "hide.png")
WIN2_ICON = os.path.join(WINDOW_ICONS_DIR, "dock.png")
WIN3_ICON = os.path.join(WINDOW_ICONS_DIR, "float.png")
PADDING_X = 0.0
PADDING_Y = 30.0

DEFAULT_ICON_STR = "default_icon"
ADDS_BUTTONS_STR = "adds_buttons"
BORDER_COLOR_HI_STR = "border_color_hi"
REMOVABLE_STR = "removable"
ON_ICON_STR = "on_icon"
ICON_SIZE_STR = "icon_size"
BTTN_COORDINATES_STR = "bttn_coordinates"
HIGHLIGHT_ICON_STR = "highlight_icon"
ON_HIGHLIGHT_ICON_STR = "on_highlight_icon"
FUNCTION_TO_CALL_STR = "function_to_call"
FUNCTION_ON_SHIFT_STR = "function_on_shift"
SELECTION_LIST_STR = "selection_list"
COLOR_STR = "color"

SELECTION_BTTNS_STR = "selection_bttns"

DEFAULT_BORDER_STYLE = "none"
DEFAULT_BORDER_STYLE_HIGHLIGHT = "solid"
DEFAULT_BORDER_WIDTH = 1
DEFAULT_BORDER_COLOR = "rgb(0,0,0,0)" # Changing color, not border-style, so that image remains the same size
DEFAULT_BORDER_COLOR_HIGHLIGHT = "rgb(206,206,206,255)"


mayaMainWindowPtr = omui.MQtUtil.mainWindow()
mayaMainWindow = wrapInstance(long(mayaMainWindowPtr), QWidget)


class SelectionButton(QPushButton):
    """
    Button with parameters from a json file (in a form of bttn_info)
    Has hover press and release functionality.
    Can be used as a button overlaying an image or an additional
    button below the image.
    """
    middle_clicked = Signal()
    left_clicked = Signal()

    def __init__(self, parent=None, bttn_info=None, bttn_idx=0, icon_dir=UI_ICONS_DIR):
        super(SelectionButton, self).__init__(parent)
        self.setParent(parent)
        self.bttn_info = bttn_info
        self.removable = False
        self.bttn_idx = bttn_idx
        self.icon_dir = icon_dir

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
                               % (bttn_info[COLOR_STR][0],bttn_info[COLOR_STR][1],
                                  bttn_info[COLOR_STR][2],bttn_info[COLOR_STR][3]))
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

        if SELECTION_LIST_STR in bttn_info:
            try:
                self.left_clicked.connect(lambda: self.select_ctrs(bttn_info[SELECTION_LIST_STR]))
            except AttributeError, ValueError:
                mc.warning("Unable to select %s" % bttn_info[SELECTION_LIST_STR])
                return

        if FUNCTION_TO_CALL_STR in bttn_info and FUNCTION_ON_SHIFT_STR in bttn_info:
            try:
                self.left_clicked.connect(
                    lambda: self.custom_function(function_to_call = str(bttn_info[FUNCTION_TO_CALL_STR]),
                                                 function_on_shift = str(bttn_info[FUNCTION_ON_SHIFT_STR])))
            except AttributeError:
                mc.warning("Unable to call %s" % bttn_info[FUNCTION_TO_CALL_STR])
                return

        elif FUNCTION_TO_CALL_STR in bttn_info:
            try:
                self.left_clicked.connect(lambda: eval(str(bttn_info[FUNCTION_TO_CALL_STR])))
            except AttributeError:
                mc.warning("Unable to call %s" % bttn_info[FUNCTION_TO_CALL_STR])
                return

    def custom_function(self, function_to_call, function_on_shift):
        modifiers = QApplication.keyboardModifiers()
        if modifiers == (Qt.ShiftModifier):
            eval(str(function_on_shift))
        else:
            eval(str(function_to_call))

    def select_ctrs(self, selection_list):
        modifiers = QApplication.keyboardModifiers()
        for ctr in selection_list:
            if not mc.objExists(ctr):
                print("%s does not exist and will not be selected" % ctr)
                selection_list.remove(ctr)
        if modifiers == (Qt.ShiftModifier):
            mc.select(selection_list, add=True)
        else:
            mc.select(selection_list, add=False)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.left_clicked.emit()
        if event.button() == Qt.MiddleButton:
            self.middle_clicked.emit()

    def enterEvent(self, event):
        self.set_hover_state()

    def leaveEvent(self, event):
        self.set_default_state()

    def set_hover_state(self):
        self.setStyleSheet("background-color:rgb(0,0,0,0); border-style:%s; border-width:%spx;"
                           "border-color: %s" % (DEFAULT_BORDER_STYLE_HIGHLIGHT,
                                                 DEFAULT_BORDER_WIDTH,
                                                 DEFAULT_BORDER_COLOR_HIGHLIGHT))

    def set_default_state(self):
        self.setStyleSheet("background-color:rgb(0,0,0,0); border-style:%s; border-width:%spx;"
                           "border-color: %s" % (DEFAULT_BORDER_STYLE,
                                                 DEFAULT_BORDER_WIDTH,
                                                 DEFAULT_BORDER_COLOR))


class Overlay(QWidget):
    """
    Buttons overlaying an image
    """
    def __init__(self, parent=None, json_file=JSON_FILE):
        super(Overlay, self).__init__(parent)
        self.setParent(parent)
        self.button_infos = []
        self.main_buttons = []
        try:
            self.populate_bttn_dicts(json_file)
        except BaseException:
            msg = "Invalid JSON file with button info: %s" % json_file
            mc.warning(msg)
        for bttn_info in self.button_infos:
            button = SelectionButton(self, bttn_info)
            self.main_buttons.append(button)

        self.setGeometry(0, 0,
                         MAIN_IMAGE_PARAMETERS[0]+PADDING_X, MAIN_IMAGE_PARAMETERS[1]+PADDING_Y)

    def change_state(self):
        if self.toggle_button.isChecked():
            for button in self.main_buttons:
                button.setChecked(True)
                button.set_add_multiply()
        else:
            for button in self.main_buttons:
                button.setChecked(False)
                button.set_add_multiply()

    def populate_bttn_dicts(self, json_file):
        with open(json_file, "r+") as data_file:
            data = json.load(data_file)
            for bttn_info_node in data[SELECTION_BTTNS_STR]:
                self.button_infos.append(bttn_info_node)


class Picker(QWidget):
    """
    Overall window, responsible for scrolling
    """
    def __init__(self, *args, **kwargs):
        super(Picker, self).__init__(*args, **kwargs)
        self.setParent(mayaMainWindow)
        self.setWindowFlags(Qt.Window)
        self.isDockedHidden = False
        self.isFloating = False
        self.initUI()

    def initUI(self):

        self.setFixedWidth(FIXED_WIDTH)
        self.layout = QGridLayout(self)
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
        self.initScrollArea()

        self.subWindow = SubWindow(self)
        self.scrollLayout.addWidget(self.subWindow)

        self.layout.addWidget(self.scroll)
        self.setWindowTitle(WIN_TITLE)

        hlo = QHBoxLayout()
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
        hlo = QHBoxLayout()
        hlo.setAlignment(Qt.AlignRight)
        qw.setLayout(hlo)

        hlo.addSpacing(120)
        hlo.addWidget(floatButton)
        hlo.addWidget(closeButton)

        self.layout.addWidget(qw)


        # Right click menu
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.openMenu)
        self.show()

    def openMenu(self, pos, *args, **kwargs):
        """
        Opens a right-click menu anywhere on the widget, its not really a 'context' menu
        For the picker, we only need the floating and docking helper menu items
        """
        menu = QMenu()

        floatAction = menu.addAction(self.tr("Toggle Float/Dock Widget"))
        hideAction = menu.addAction(self.tr("Hide and Dock Widget"))
        closeAction = menu.addAction(self.tr("Close Widget"))

        action = menu.exec_(QCursor.pos())

        if action == closeAction:
            self.close()

        if action == floatAction:
            self._toggleFloat()

        if action == hideAction:
            self._toggleDock()

    def close(self):
        try:
            mc.deleteUI(_globalDockControl)
        except:
            pass

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


class SubWindow(QWidget):
    """
    Separate from main window so that can have it work with scroll
    """
    def __init__(self, parent=None):
        super(SubWindow, self).__init__(parent)
        self.setParent(parent)
        self.initUI()

    def initUI(self):
        self.setWindowTitle(WIN_TITLE)
        self.layout = QVBoxLayout(self)
        pic = QLabel(self)
        pic.setPixmap(QPixmap(PICKER_BG_PNG))
        pic.setGeometry(0, 0, MAIN_IMAGE_PARAMETERS[0], MAIN_IMAGE_PARAMETERS[1])
        self.layout.addWidget(pic)

        # Need to add additional widget so that the image doesn't change position with scale
        # Later can replace it with a row of additional buttons
        emptyWidget = QLabel(self)
        self.layout.addWidget(emptyWidget, rowSpan=0)

        # First display the widget with an image, then one with the buttons overlaying the image
        self.show()
        self.overlay = Overlay(self)
        # this is the widget that allows the user to add/remove objects to picker
        self.picker_add_widget = PickerAddWidget()

        self.layout.addWidget(self.picker_add_widget)

        self.layout.addStretch(400)

    def _toggleFloat(self):
        pass

    # This deselects everything if the user clicks in a blank area
    def mousePressEvent(self, event):
        mc.select(cl=True)

    def closeEvent(self, *args, **kwargs):
        try:
            mc.deleteUI(WIN_TITLE)
        except:
            mc.warning("Failed to close picker")


def main():
    global _globalDockControl
    ui, dockWidget, _globalDockControl = Dock(Picker, winTitle=WIN_TITLE)
    return ui


