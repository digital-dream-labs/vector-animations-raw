import sys
import os
import subprocess
import time
import ast

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

WIN_TITLE = "Eye Intersection"

mayaMainWindowPtr = omui.MQtUtil.mainWindow()
mayaMainWindow = wrapInstance(long(mayaMainWindowPtr), QWidget)

class MainWindow(QDockWidget):
    """
    Overall wondow, responsible for scrolling
    """
    def __init__(self, *args, **kwargs):
        super(MainWindow,self).__init__(*args, **kwargs)
        self.setParent(mayaMainWindow)
        self.setWindowFlags(Qt.Window)

    def initUI(self):
        self.layout = QGridLayout(self)
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
        self.initScrollArea()

        self.subWindow = Subwindow(parent = self)
        self.scrollLayout.addWidget(self.subWindow)

        self.setWidget(self.scroll)
        self.setWindowTitle(WIN_TITLE)
        self.show()

    def initScrollArea(self):
        self.scrollWidget = QWidget()
        self.scrollLayout = QVBoxLayout(self.scrollWidget)
        self.scrollWidget.setLayout(self.scrollLayout)
        self.scroll = QScrollArea(self)
        self.scroll.setWidgetResizable(True)

        #self.scroll.setMinimumWidth(480)
        #self.scroll.setMinimumHeight(300)

        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setWidget(self.scrollWidget)
        self.layout.addWidget(self.scroll)

class Subwindow(QWidget):
    """
    Separate from main window so that can have it work with scroll
    """
    def __init__(self, parent = None):
        super(Subwindow, self).__init__(parent)
        self.setParent(parent)
        self.initUI()

    def initUI(self):
        self.layout = QVBoxLayout(self)
        #self.layout.setHorizontalSpacing(0)
        self.check_intersection_bttn = QPushButton("Check Intersections")

        self.layout.addWidget(self.check_intersection_bttn, row=0)
        #self.b1.clicked.connect(eye_screen_intersection.check_intersection())

        self.frame_info_widget = FrameInfoWidget(parent=self)
        self.addWidget(self.frame_info_widget)

        self.show()

    def add_frame_info_widget(self):
        pass

class FrameInfoWidget(QWidget):
    def __init__(self, parent=None):
        super(FrameInfoWidget, self).__init__(parent)
        self.setParent(parent)
        self.frame_num = 0.0
        self.initUI()

    def initUI(self):
        self.layout = QVBoxLayout(self)
        self.frame_num_label = QLabel()
        self.frame_num_label.setText("Frame: %s" % (self.frame_num))

        self.layout.addWidget(self.frame_num_label, row=0)
        # self.b1.clicked.connect(eye_screen_intersection.check_intersection())

        self.show()

def main():
    global _globalPreviewUI
    ui = MainWindow()
    ui.initUI()
    _globalPreviewUI = ui
    return ui
