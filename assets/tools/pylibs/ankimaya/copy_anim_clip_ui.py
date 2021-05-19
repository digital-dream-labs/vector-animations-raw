
import os
from maya import cmds
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

from ankimaya import copy_anim_clip


WIN_TITLE = "Copy Animation Clip"
ANIM_UI_FILE = "copy_anim.ui"
USER_SELECT_ATTR = "animClips"
USER_TYPE_ATTR = "animClip"
FRAME_ATTR = "frameNum"
ALL_ATTRS = [USER_SELECT_ATTR, USER_TYPE_ATTR, FRAME_ATTR]

WINDOW_WIDTH = 640
WINDOW_HEIGHT = 93


mayaMainWindowPtr = omui.MQtUtil.mainWindow()
mayaMainWindow = wrapInstance(long(mayaMainWindowPtr), QWidget)


class CopyAnimSettings(QWidget):
    def __init__(self, *args, **kwargs):
        super(CopyAnimSettings,self).__init__(*args, **kwargs)
        self.setParent(mayaMainWindow)
        self.setWindowFlags(Qt.Window)
        self.gridCount = 0
        self.add_maya_file = False
        self.initUI()

    def _addWidgetToGrid(self, widget, column=0, lastInRow=True):
        self.grid.addWidget(widget, self.gridCount, column)
        if lastInRow:
            self.gridCount += 1

    def initUI(self):
        self.setWindowTitle(WIN_TITLE)
        self.grid = QGridLayout(self)
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)

        self.show()
        self.setLayout(self.grid)

        self.add_main_section()
        self.add_bottom_buttons()

    def add_bottom_buttons(self):
        self.bottomBtns = QGridLayout(self)

        self.setBtn = QPushButton("Copy")
        self.setBtn.clicked.connect(self.do_copy)
        self.bottomBtns.addWidget(self.setBtn, 0, 0)

        self.cancelBtn = QPushButton("Cancel")
        self.cancelBtn.clicked.connect(self.do_cancel)
        self.bottomBtns.addWidget(self.cancelBtn, 0, 1)

        self.bottomBtnsWidget = QWidget()
        self.bottomBtnsWidget.setLayout(self.bottomBtns)
        self._addWidgetToGrid(self.bottomBtnsWidget)

    def add_main_section(self):
        self.anim = AnimToCopy(self)
        self._addWidgetToGrid(self.anim.ui)

        self.new_file_checkbox = QCheckBox("Create new maya file")
        self.new_file_checkbox.setChecked(False)
        self.new_file_checkbox.stateChanged.connect(lambda: self.add_file_name_field())
        self._addWidgetToGrid(self.new_file_checkbox)

        self.anim.ui.setMinimumSize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.anim.ui.show()

    def add_file_name_field(self):
        if self.new_file_checkbox.isChecked() == True:
            self.grid.removeWidget(self.bottomBtnsWidget)
            self.gridCount -= 1

            self.maya_file_name_w = MayaFileName(parent = self)
            self._addWidgetToGrid(self.maya_file_name_w)
            self._addWidgetToGrid(self.bottomBtnsWidget)
            self.add_maya_file = True

        else:
            self.grid.removeWidget(self.maya_file_name_w)
            self.maya_file_name_w.deleteLater()
            self.maya_file_name_w = None
            self.gridCount -= 1
            self.add_maya_file = False

    def getAnimClipData(self, uiData):
        animClipDataDict = {}
        for attr in ALL_ATTRS:
            uiAttr = eval("uiData.ui.%s" % attr)
            if hasattr(uiAttr, "checkState"):
                uiValue = uiAttr.checkState()
            elif hasattr(uiAttr, "currentText"):
                uiValue = uiAttr.currentText()
            elif hasattr(uiAttr, "text"):
                uiValue = uiAttr.text()
            animClipDataDict[attr] = uiValue
        for key, value in animClipDataDict.items():
            if value == Qt.CheckState.Unchecked:
                animClipDataDict[key] = False
            elif value == Qt.CheckState.Checked:
                animClipDataDict[key] = True
        return animClipDataDict

    def get_anim_clip_info(self, animWidget):
        animClipData = self.getAnimClipData(animWidget)
        try:
            frameNum = int(animClipData[FRAME_ATTR])
        except (TypeError, ValueError):
            # If doesn't find the frame will set it to the frame after the end
            frameNum = None

        copy_clip_name = animClipData[USER_TYPE_ATTR].strip()
        anim_clip = animClipData[USER_SELECT_ATTR].strip()

        return (anim_clip, copy_clip_name, frameNum)

    def do_copy(self):
        clip_duplicator = copy_anim_clip.ClipDuplicator()
        anim_clip, copy_clip_name, frameNum = self.get_anim_clip_info(self.anim)
        if self.add_maya_file:
            success = clip_duplicator.copy_to_new_file(self.maya_file_name_w.file_name, anim_clip, copy_clip_name)
        else:
            success = clip_duplicator.add_anim_clip(anim_clip, copy_clip_name, frameNum)

        if success:
            self.close()

    def do_cancel(self):
        self.close()


class MayaFileName(QWidget):
    def __init__(self, parent = None, *args, **kwargs):
        super(MayaFileName, self).__init__(*args, **kwargs)
        self.file_name = None
        self.initUI()

    def initUI(self):
        self.setWindowTitle(WIN_TITLE)
        self.layout = QHBoxLayout(self)
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)

        self.show()
        self.setLayout(self.layout)

        self.copy_to_file_label = QLabel()
        self.copy_to_file_label.setText("Name of the new Maya file:")
        self.layout.addWidget(self.copy_to_file_label,0,0)

        self.copy_to_file_line_edit = QLineEdit()
        self.copy_to_file_line_edit.textChanged.connect(self.file_name_input)
        self.layout.addWidget(self.copy_to_file_line_edit, 0, 0)

    def file_name_input(self, text):
        self.file_name = text;


class AnimToCopy(QWidget):
    def __init__(self, parent, *args, **kwargs):
        super(AnimToCopy,self).__init__(*args, **kwargs)
        self.setParent(parent)
        currentDir = os.path.dirname(__file__)
        self.preview_ui_file = QFile(os.path.join(currentDir, ANIM_UI_FILE))
        self.initUI()

    def initUI(self):
        # Load UI config from ANIM_UI_FILE
        loader = QUiLoader()
        self.preview_ui_file.open(QFile.ReadOnly)
        self.ui = loader.load(self.preview_ui_file, parentWidget=self.parent())
        self.preview_ui_file.close()

        # Add current anim clips to the pulldown menu
        try:
            animClips = copy_anim_clip.get_anim_clips()
        except BaseException, e:
            cmds.warning("Failed to get the list of animation clips from the Game Exporter")
            animClips = []
        animClips.sort()
        for anim_clip in animClips:
            self.ui.animClips.addItem(anim_clip)


def main():
    ui = CopyAnimSettings()
    ui.show()
    return ui


if __name__ == '__main__':
    main()


