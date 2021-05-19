

WIN_TITLE = "Should head angle variations be exported?"

UI_FILE = "head_angle_selector.ui"

EXPORT_HEAD_ANGLES_ATTR = "exportHeadAngles"
WHICH_KEYFRAMES_ATTR = "whichKeyframes"
ALL_ATTRS = [EXPORT_HEAD_ANGLES_ATTR, WHICH_KEYFRAMES_ATTR]

HEAD_ANGLE_STRUCT_NAME = "HeadAngleStruct"
HEAD_ANGLE_STREAM_NAME = "HeadAngleStream"
HEAD_ANGLE_MEMBER_NAME = "shouldExport"
HEAD_ANGLE_CHANNEL_NAME = "export"


import sys
import os
import copy
import pprint
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

from ankiutils import head_angle_config


def getHeadAngleVariationExportSettings(structName=HEAD_ANGLE_STRUCT_NAME):
    """
    Get the current settings for exported head angle variations.
    """
    numVariations = None
    whichKeyframes = None
    dataStructs = cmds.dataStructure(query=True)
    if structName in dataStructs:
        headAngleSetting = cmds.getMetadata(index=0, streamName=HEAD_ANGLE_STREAM_NAME,
                                            memberName=HEAD_ANGLE_MEMBER_NAME,
                                            channelName=HEAD_ANGLE_CHANNEL_NAME, scene=True)
        if isinstance(headAngleSetting, list):
            headAngleSetting = headAngleSetting[0]

        # We use a 2-digit number where the first digit is the number of head angle variations
        # to export and the second digit is the code that indicates which head angle keyframes
        # should be offset by the exact amount of the head angle variation.
        # (see the doApply() method for some related info)
        if headAngleSetting < 10:
            numVariations = headAngleSetting
            whichKeyframes = head_angle_config.DEFAULT_WHICH_KEYFRAME
        else:
            headAngleSettingString = str(headAngleSetting)
            numVariations = headAngleSettingString[0]
            whichKeyframes = headAngleSettingString[1]

        numVariations = int(numVariations)
        whichKeyframes = int(whichKeyframes)
    return (numVariations, whichKeyframes)


def setNumHeadAngleVariationsToExport(value, structName=HEAD_ANGLE_STRUCT_NAME):
    structDesc = "name=%s:int32=%s" % (structName, HEAD_ANGLE_MEMBER_NAME)
    dataStructs = cmds.dataStructure(query=True)
    if structName in dataStructs:
        existingStruct = cmds.dataStructure(name=structName, format="raw", query=True, asString=True)
        if structDesc != existingStruct:
            cmds.warning("Removing data structure for '%s' since the existing structure does not "
                         "match the expected format" % structName)
            cmds.dataStructure(remove=True, name=structName)
            dataStructs = cmds.dataStructure(query=True)
    if structName not in dataStructs:
        print("Creating data structure to store the number of head angle variations to use")
        cmds.dataStructure(format="raw", asString=structDesc)
        cmds.addMetadata(streamName=HEAD_ANGLE_STREAM_NAME, structure=structName,
                         channelName=HEAD_ANGLE_CHANNEL_NAME, scene=True)
    print("Setting number of head angle variations to be %s" % value)
    cmds.editMetadata(index=0, streamName=HEAD_ANGLE_STREAM_NAME, memberName=HEAD_ANGLE_MEMBER_NAME,
                      value=value, scene=True)


class HeadAngleSettings(QWidget):
    def __init__(self, mayaMainWindow, *args, **kwargs):
        super(HeadAngleSettings,self).__init__(*args, **kwargs)
        self.setParent(mayaMainWindow)
        self.setWindowFlags(Qt.Window)
        self.headAngleConfig = head_angle_config.HeadAngleConfig()
        self.headAngleWidget = None
        self.gridCount = 0
        self.vbox = None
        self.widget = None
        self.initUI()

    def _addWidgetToGrid(self, widget, column=0, lastInRow=True):
        self.grid.addWidget(widget, self.gridCount, column)
        if lastInRow:
            self.gridCount += 1

    def initUI(self):

        self.setGeometry(100, 100, 700, 70)
        self.setWindowTitle(WIN_TITLE)

        # At the top layer, a grid layout is used to hold buttons and widgets
        self.grid = QGridLayout(self)

        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
        # TODO: Can we use the following instead of forcing the window to always stay on top?
        #self.setProperty("saveWindowPref", True)
        # Along with that setProperty() call, we may need to call setObjectName() to give it a name.

        self.show()

        self.widget = QWidget()
        self.vbox = QVBoxLayout(self.widget)
        self._addWidgetToGrid(self.widget)
        self.setLayout(self.grid)

        self.addHeadAngleInput()
        self.addBottomButtons()

        self.loadExistingSettings()

    def addBottomButtons(self):
        self.bottomBtns = QGridLayout(self)

        # Add create button to the grid layout
        self.setBtn = QPushButton("Apply")
        self.setBtn.clicked.connect(self.doApply)
        self.bottomBtns.addWidget(self.setBtn, 0, 0)
        #self.setBtn.setLayout(self.bottomBtns)

        # Add cancel button to the grid layout
        self.cancelBtn = QPushButton("Cancel")
        self.cancelBtn.clicked.connect(self.doCancel)
        self.bottomBtns.addWidget(self.cancelBtn, 0, 1)

        self.bottomBtnsWidget = QWidget()
        self.bottomBtnsWidget.setLayout(self.bottomBtns)
        self._addWidgetToGrid(self.bottomBtnsWidget)

    def addHeadAngleInput(self):
        self.headAngleWidget = HeadAngleInput(self.widget, self.headAngleConfig)
        self._addWidgetToGrid(self.headAngleWidget.ui)
        self.headAngleWidget.ui.setMinimumSize(700, 70)
        self.headAngleWidget.ui.show()

    def getHeadAngleData(self, headAngleData):
        headAngleDataDict = {}
        for attr in ALL_ATTRS:
            uiAttr = eval("headAngleData.ui.%s" % attr)
            if hasattr(uiAttr, "checkState"):
                uiValue = uiAttr.checkState()
            elif hasattr(uiAttr, "currentText"):
                uiValue = uiAttr.currentText()
            elif hasattr(uiAttr, "text"):
                uiValue = uiAttr.text()
            headAngleDataDict[attr] = uiValue
        for key, value in headAngleDataDict.items():
            if value == Qt.CheckState.Unchecked:
                headAngleDataDict[key] = False
            elif value == Qt.CheckState.Checked:
                headAngleDataDict[key] = True
            elif not value:
                raise ValueError("No value provided for %s" % key)
        pprint.pprint(headAngleDataDict)
        return headAngleDataDict

    def doApply(self):
        try:
            headAngleData = self.getHeadAngleData(self.headAngleWidget)
        except ValueError:
            errorMsg = "Invalid head angle data provided"
            cmds.warning(errorMsg)
            QMessageBox.critical(self, "Alert", errorMsg)
            return None
        if headAngleData:
            numVariations = headAngleData[EXPORT_HEAD_ANGLES_ATTR]
            if isinstance(numVariations, basestring):
                numVariations = self.headAngleConfig.get_num_variations_from_display(numVariations)
            whichKeyframes = headAngleData[WHICH_KEYFRAMES_ATTR]
            whichKeyframes = self.headAngleConfig.get_which_keyframes_from_display(whichKeyframes)
            whichKeyframes = whichKeyframes[0]

            # We use a 2-digit number where the first digit is the number of head angle variations
            # to export and the second digit is the code that indicates which head angle keyframes
            # should be offset by the exact amount of the head angle variation.
            # (see the getHeadAngleVariationExportSettings() function for some related info)
            if numVariations > 0:
                setting = (numVariations * 10) + whichKeyframes
            else:
                setting = 0

            setNumHeadAngleVariationsToExport(setting)
            cmds.file(modified=True)
            self.close()

    def doCancel(self):
        self.close()

    def fillHeadAngleWidget(self, headAngleWidget, headAngleData):
        for attr, value in headAngleData.items():
            if attr in [EXPORT_HEAD_ANGLES_ATTR]:
                value = self.headAngleConfig.get_num_variations_display_string(value)
            elif attr in [WHICH_KEYFRAMES_ATTR]:
                value = self.headAngleConfig.get_which_keyframes_display_string(value)
            uiAttr = eval("headAngleWidget.ui.%s" % attr)
            if hasattr(uiAttr, "setChecked"):
                uiAttr.setChecked(value)
            elif hasattr(uiAttr, "setCurrentIndex"):
                idx = uiAttr.findText(str(value))
                if idx < 0:
                    idx = 0
                uiAttr.setCurrentIndex(idx)
            elif hasattr(uiAttr, "insert"):
                uiAttr.clear()
                uiAttr.insert(str(value))

    def loadExistingSettings(self):
        """
        Load the current setting(s) into the UI.
        """
        numVariations, whichKeyframes = getHeadAngleVariationExportSettings()
        headAngleData = {EXPORT_HEAD_ANGLES_ATTR : numVariations,
                         WHICH_KEYFRAMES_ATTR    : whichKeyframes}
        self.fillHeadAngleWidget(self.headAngleWidget, headAngleData)


class HeadAngleInput(QWidget):
    def __init__(self, parent, headAngleConfig, *args, **kwargs):
        super(HeadAngleInput,self).__init__(*args, **kwargs)
        self.setParent(parent)
        currentDir = os.path.dirname(__file__)
        self.headAngleConfig = headAngleConfig
        self.head_angle_ui_file = QFile(os.path.join(currentDir, UI_FILE))
        self.initUI()

    def initUI(self):
        # Load UI config from UI_FILE
        loader = QUiLoader()
        self.head_angle_ui_file.open(QFile.ReadOnly)
        self.ui = loader.load(self.head_angle_ui_file, parentWidget=self.parent())
        self.head_angle_ui_file.close()

        # Add head angle variation options to the pulldown menus
        options = self.headAngleConfig.get_num_variations_display_strings()
        for option in options:
            self.ui.exportHeadAngles.addItem(option)
        options = self.headAngleConfig.get_which_keyframes_display_strings()
        for option in options:
            self.ui.whichKeyframes.addItem(option)


def main():
    mayaMainWindowPtr = omui.MQtUtil.mainWindow()
    mayaMainWindow = wrapInstance(long(mayaMainWindowPtr), QWidget)
    ui = HeadAngleSettings(mayaMainWindow)
    ui.show()
    return ui


if __name__ == '__main__':
    main()


