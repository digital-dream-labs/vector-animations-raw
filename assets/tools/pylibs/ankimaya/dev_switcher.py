import os
import sys
import glob

TOOLS_DIR_ENV_VAR = "ANKI_TOOLS"
TOOLS_DIR = os.path.join(os.getenv(TOOLS_DIR_ENV_VAR), 'pylibs', 'ankimaya')

import importlib
from ankiutils import svn_tools
from maya import cmds
from maya import OpenMayaUI as omui
from window_docker import Dock
import time
import datetime

GET_SVN_REV = True

'''
                    this pyqt and maya script will scan a directory (currently tools/pylibs/ankimaya)
                    for files that have _DEV in the name.  when it finds one, a UI widget is
                    created to allow the user to be able to switch between the two.
                    when the user switches, the old module is unloaded and the new module is re-loaded
                    so recent changes to the file will be live, and the main function is called, so that 
                    is a requirement in the module to switch between.
                    
                    chris rogers (c) anki, inc. 8/2018

'''

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

mayaMainWindowPtr = omui.MQtUtil.mainWindow()
mayaMainWindow = wrapInstance(long(mayaMainWindowPtr), QWidget)


class DevLabel(QWidget):
    def __init__(self, *args, **kwargs):
        super(DevLabel, self).__init__()
        self.setParent(mayaMainWindow)
        self.setWindowFlags(Qt.Window)
        self.devname = kwargs.get('devname', None)
        self.proname = kwargs.get('proname', None)
        self.devrev = kwargs.get('devrev', None)
        self.prorev = kwargs.get('prorev', None)
        self.path = kwargs.get('path', None)
        self.useDev = False
        self.initUI()

    def initUI(self):
        self.setFixedHeight(40)
        self.lo = QHBoxLayout()
        self.setLayout(self.lo)

        self.cb_pro = QCheckBox()
        self.cb_pro.setFixedWidth(32)
        self.cb_pro.setChecked(True)
        self.lo.addWidget(self.cb_pro)

        self.prolabel = QLabel('#' + str(self.prorev) + ':' + self.proname)
        self.prolabel.setFixedWidth(160)
        self.lo.addWidget(self.prolabel)

        self.devrevLabel = QLabel('#' + str(self.devrev))

        self.devlabel = QLabel('#' + str(self.devrev) + ':' + self.devname)
        self.devlabel.setFixedWidth(160)
        self.lo.addWidget(self.devlabel)

        self.cb_dev = QCheckBox()
        self.cb_dev.setFixedWidth(32)
        self.lo.setAlignment(Qt.AlignRight)
        self.lo.addWidget(self.cb_dev)

        self.cb_dev.clicked.connect(self.switch_module)
        self.cb_pro.clicked.connect(self.switch_module)

        self.show()

    def switch_module(self):
        self.useDev = not self.useDev
        oldmodule = self.proname
        newmodule = self.devname
        if self.useDev:
            self.cb_pro.setChecked(False)
            self.cb_dev.setChecked(True)
        if not self.useDev:
            self.cb_dev.setChecked(False)
            self.cb_pro.setChecked(True)
            newmodule = self.proname
            oldmodule = self.devname

        newmodule = newmodule.replace('.py', '')
        oldmodule = oldmodule.replace('.py', '')

        if 'ankimaya.' + oldmodule in sys.modules:
            del sys.modules['ankimaya.' + oldmodule]

        if 'ankimaya.' + newmodule in sys.modules:
            del sys.modules['ankimaya.' + newmodule]

        # Here is where it reloads the DEV module with the production name
        newModuleName = importlib.import_module('ankimaya.' + newmodule, package=self.proname.replace('.py', ''))

        # Here is where it calls the new module entry function.  So far, they have been windowed apps with main function
        if 'main' in dir(newModuleName):
            newModuleName.main()

        path = os.path.join(TOOLS_DIR, newmodule + '.py')
        mtime = time.strftime("%d %b %H:%M:%S", time.localtime(os.path.getmtime(path)))
        msg = ("switched to {0}({2}) at {1}.".format(newmodule, time.strftime("%d %b %H:%M:%S", time.gmtime()), mtime))
        self.parent().te.append(msg + '\n')


class DevWidget(QWidget):
    def __init__(self, *args, **kwargs):
        super(DevWidget, self).__init__(*args, **kwargs)
        print "__file__=", __file__
        self.rev = svn_tools.get_svn_file_rev(__file__.replace('.pyc', '.py'))
        self.setParent(mayaMainWindow)
        self.setWindowFlags(Qt.Window)
        self.initUI()
        self.get_dev_files()
        self.lo.addWidget(self.closeButton)
        self.te = QTextEdit()
        self.lo.addWidget(self.te)

    def initUI(self):
        self.lo = QVBoxLayout()
        self.lo.setAlignment(Qt.AlignTop)
        self.setLayout(self.lo)
        self.title = QLabel("DEV Switcher #" + str(self.rev))
        self.lo.addWidget(self.title)

        self.closeButton = QPushButton('close')
        self.closeButton.clicked.connect(self.close)

        self.show()

    def get_dev_files(self):
        dev_files = glob.glob(os.path.join(TOOLS_DIR, '*_DEV.py'))
        for dev in dev_files:
            proname = dev.replace('_DEV', '')
            rev = '0'
            prorev = '0'
            if GET_SVN_REV: rev = svn_tools.get_svn_file_rev(dev)
            if GET_SVN_REV: prorev = svn_tools.get_svn_file_rev(proname)
            l = DevLabel(devrev=rev, devname=os.path.basename(dev), prorev=prorev, proname=os.path.basename(proname),
                         path=TOOLS_DIR)
            self.lo.addWidget(l)

    def close(self):
        cmds.deleteUI(dockControl)
        try:
            cmds.deleteUI("DevSwitcher")
        except:
            pass


def getGlobalPreviewUI():
    # This will allow us to assign a hotkey to the "Preview" button
    return _globalPreviewUI


global _globalPreviewUI, dockControl, dockWidget, ui


def main():
    try:
        cmds.deleteUI('DevSwitcher')
    except:
        pass
    global _globalPreviewUI, dockControl, dockWidget, ui
    ui, dockWidget, dockControl = Dock(DevWidget, width=320, winTitle='DevSwitcher')
    ui.setObjectName('DevSwitcher')
    _globalPreviewUI = ui
    return ui


if __name__ == '__main__':
    main()
