

WIN_TITLE = "Exporter Configuration"

UI_FILE = "exporter_selector.ui"

EXPORTER_VERSION_ATTR = "exporterVersion"
ALL_ATTRS = [EXPORTER_VERSION_ATTR]


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

from ankimaya import exporter_config


class ExporterSettings(QWidget):
    def __init__(self, mayaMainWindow, *args, **kwargs):
        super(ExporterSettings,self).__init__(*args, **kwargs)
        self.setParent(mayaMainWindow)
        self.setWindowFlags(Qt.Window)
        self.exporterConfig = exporter_config.ExporterConfig()
        self.exporterWidget = None
        self.gridCount = 0
        self.vbox = None
        self.widget = None
        self.initUI()

    def _addWidgetToGrid(self, widget, column=0, lastInRow=True):
        self.grid.addWidget(widget, self.gridCount, column)
        if lastInRow:
            self.gridCount += 1

    def initUI(self):

        self.setGeometry(100, 100, 650, 50)
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

        self.addExporterInput()
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

    def addExporterInput(self):
        self.exporterWidget = ExporterInput(self.widget, self.exporterConfig)
        self._addWidgetToGrid(self.exporterWidget.ui)
        self.exporterWidget.ui.setMinimumSize(500, 50)
        self.exporterWidget.ui.show()

    def getExporterData(self, exporterData):
        exporterDataDict = {}
        for attr in ALL_ATTRS:
            uiAttr = eval("exporterData.ui.%s" % attr)
            if hasattr(uiAttr, "checkState"):
                uiValue = uiAttr.checkState()
            elif hasattr(uiAttr, "currentText"):
                uiValue = uiAttr.currentText()
            elif hasattr(uiAttr, "text"):
                uiValue = uiAttr.text()
            exporterDataDict[attr] = uiValue
        for key, value in exporterDataDict.items():
            if value == Qt.CheckState.Unchecked:
                exporterDataDict[key] = False
            elif value == Qt.CheckState.Checked:
                exporterDataDict[key] = True
            elif not value:
                raise ValueError("No value provided for %s" % key)
        pprint.pprint(exporterDataDict)
        return exporterDataDict

    def doApply(self):
        try:
            exporterData = self.getExporterData(self.exporterWidget)
        except ValueError:
            errorMsg = "Invalid data provided"
            cmds.warning(errorMsg)
            QMessageBox.critical(self, "Alert", errorMsg)
            return None
        if exporterData:
            exporterVersion = exporterData[EXPORTER_VERSION_ATTR]
            if isinstance(exporterVersion, basestring):
                exporterVersion = self.exporterConfig.get_version_num_from_display(exporterVersion)
            exporter_config.setExporterVersion(exporterVersion)
            cmds.file(modified=True)
            self.close()

    def doCancel(self):
        self.close()

    def fillExporterWidget(self, exporterWidget, exporterData):
        for attr, value in exporterData.items():
            uiAttr = eval("exporterWidget.ui.%s" % attr)
            value = self.exporterConfig.get_display_string(value)
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
        try:
            exporterVersion = exporter_config.getExporterVersion()
        except RuntimeError:
            exporterVersion = exporter_config.DEFAULT_VERSION
        exporterData = {EXPORTER_VERSION_ATTR : exporterVersion}
        self.fillExporterWidget(self.exporterWidget, exporterData)


class ExporterInput(QWidget):
    def __init__(self, parent, exporterConfig, *args, **kwargs):
        super(ExporterInput,self).__init__(*args, **kwargs)
        self.setParent(parent)
        currentDir = os.path.dirname(__file__)
        self.exporterConfig = exporterConfig
        self.exporter_ui_file = QFile(os.path.join(currentDir, UI_FILE))
        self.initUI()

    def initUI(self):
        # Load UI config from UI_FILE
        loader = QUiLoader()
        self.exporter_ui_file.open(QFile.ReadOnly)
        self.ui = loader.load(self.exporter_ui_file, parentWidget=self.parent())
        self.exporter_ui_file.close()

        # Add exporter version options to the pulldown menu
        options = self.exporterConfig.get_all_display_strings()
        for option in options:
            self.ui.exporterVersion.addItem(option)


def main():
    mayaMainWindowPtr = omui.MQtUtil.mainWindow()
    mayaMainWindow = wrapInstance(long(mayaMainWindowPtr), QWidget)
    ui = ExporterSettings(mayaMainWindow)
    ui.show()
    return ui


if __name__ == '__main__':
    main()


