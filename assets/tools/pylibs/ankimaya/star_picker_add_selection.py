"""
This widget appears on the picker panel and
it allows a user to add new items and a
button to select them to the picker.

It can also work as a standalone widget

When the user presses the add button, a new selectionSet is created with the selected objs.
A button is added to the UI to be able to select.

When the picker loads, it scans the scene for nodes with a certain  prefix PICKER_SET_PREFIX = 'pickerSet_'
and creates the button for those

7/2018 chris rogers
(c) anki, inc
"""

import os
import json
from pprint import pprint
import maya.cmds as cmds

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

from window_docker import Dock
PICKER_JSON_DIR = os.path.join( os.environ['HOME'], '.anki','maya','2018','vectorStarSelectionSets')
PICKER_SET_PREFIX = 'vectorStarPickerSet_'
TOOLS_DIR_ENV_VAR = "ANKI_TOOLS"
COMMON_ICONS = os.path.join(os.getenv(TOOLS_DIR_ENV_VAR), "icons")
ICONS_DIR = os.path.join(os.getenv(TOOLS_DIR_ENV_VAR), "icons", "PickerUI")
#PLUS_ICON = os.path.join(COMMON_ICONS, 'plus_blue.png')
#UP_ICON = os.path.join(COMMON_ICONS, 'stright_fwd.png')
PLUS_ICON = os.path.join(COMMON_ICONS, 'MovementUI','plus_blue.png')
UP_ICON = os.path.join(COMMON_ICONS, 'MovementUI','straight_fwd.png')
SAVE_EVERY_CHANGE = False
ICON_SIZE = 70
MAX_COLUMNS = 4.0



class SelectItemButton(QPushButton):
    """Left of right button selects the object this button points to
    middle button deletes this button.
    ive hijacked the button to put a lineedit on there so the user can name the button
    """

    def __init__(self, parent=None, *args, **kwargs):
        super(SelectItemButton, self).__init__(parent)
        self.gridPos = kwargs.get("gridPos", "0x0")
        self.selectionList = kwargs.get('selectionList', None)
        self.label = kwargs.get('label', 'label')
        self.clicked.connect(self.selectThis)
        self.setStyleSheet('background-color:black; color: white')
        lo = QVBoxLayout()
        lo.setAlignment(Qt.AlignBottom)
        self.setLayout(lo)
        lo.addSpacing(80)
        lo.addWidget(self)
        self.lineEdit = QLineEdit(self.label)
        self.lineEdit.setText(self.label)
        self.lineEdit.setFixedWidth(52)
        self.lineEdit.setFixedHeight(22)
        self.setMaximumWidth(ICON_SIZE)
        self.setMinimumWidth(40)
        self.setFixedHeight(ICON_SIZE)
        self.lineEdit.setStyleSheet('background-color:green; color: white')
        self.lineEdit.returnPressed.connect(self._updateLabel)
        self.setFixedHeight(38)
        lo.addWidget(self.lineEdit)
        self.parent = parent

    def _updateLabel(self):
        self.label=self.lineEdit.text()
        cmds.setAttr(self.selectionList+'.label',self.label,type='string')
        print("updated label to "+self.label)


    def selectThis(self):
        modifiers = QApplication.keyboardModifiers()
        print(self.selectionList, len(self.selectionList))
        if modifiers == (Qt.ShiftModifier):
            cmds.select(self.selectionList, add=True)
        else:
            cmds.select(self.selectionList)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.selectThis()
        elif event.button() == Qt.RightButton:
            self.selectThis()
        elif event.button() == Qt.MidButton:
            self.parent.buttonList.remove(self)
            # DELETE
            # need to get rid of the selectionSet but not contents
            #_removeButton(self.selectionList)
            cmds.delete(self.selectionList)
            self.close()
            if self.gridPos in self.parent.occupiedGridSlot:
                self.parent.occupiedGridSlot.remove(self.gridPos)



class PickerAddWidget(QWidget):
    def __init__(self, parent=None):
        super(PickerAddWidget, self).__init__()
        self.buttonList = []
        self.occupiedGridSlot = []
        self.buttonCount = 0
        self.setParent(parent)
        self.initUI()
        self._scanSceneForSets()

    def _scanSceneForSets(self):
        '''Scan the scene for objects with this prefix and call loadItem on the set and label'''
        selSets = cmds.ls(PICKER_SET_PREFIX + '*')
        for s in selSets:
            cmds.select(s)
            label = cmds.getAttr(s+'.label')
            self.loadItem(s,label=label)

    def _findVacantGridSlot(self):
        for y in range(20):
            for x in range(int(MAX_COLUMNS)):
                val = "{0}x{1}".format(x, y)
                #if val == "0x0": continue  # this is the slot for the + button
                if val not in self.occupiedGridSlot:
                    self.occupiedGridSlot.append(val)
                    ret = val.split("x")
                    return int(ret[0]), int(ret[1])

    def initUI(self):
        self.setAttribute(Qt.WA_StyledBackground)
        self.setFixedWidth(300)

        topLayout  = QVBoxLayout()
        topLayout.setAlignment(Qt.AlignTop)
        self.setLayout(topLayout)
        topLoadSaveLayout = QHBoxLayout()
        topLayout.addLayout(topLoadSaveLayout)


        self.loadButton = QPushButton("Load")
        topLoadSaveLayout.addWidget(self.loadButton)
        self.loadButton.clicked.connect(self.loadJsonFiles)

        self.saveButton = QPushButton("Save")
        topLoadSaveLayout.addWidget(self.saveButton)
        self.saveButton.clicked.connect(self.saveJsonFiles)

        self.addButton = QPushButton()
        self.icon = QIcon()
        self.icon.addPixmap(QPixmap(PLUS_ICON))

        self.addButton.setIcon(self.icon)
        self.addButton.setIconSize(QSize(30, ICON_SIZE))
        self.addButton.setFixedWidth(30)
        self.setStyleSheet("background-color:black; color:white;")
        self.addButton.setMinimumWidth(18)
        self.addButton.setFixedHeight(20)
        self.loadButton.setFixedHeight(20)
        self.saveButton.setFixedHeight(20)
        topLoadSaveLayout.addWidget(self.addButton)




        self.layout = QGridLayout()
        self.layout.setAlignment(Qt.AlignLeft)

        topLayout.addLayout(self.layout)




        self.addButton.clicked.connect(self.checkNewItem)
        self.addButton.setToolTip(
            'this creates a selector button for the selected object.\nhover over button to see selection list\nmiddle click to delete.')

        self.show()


    def saveJsonFiles(self):
        filepath = PICKER_JSON_DIR
        try:
            os.makedirs(filepath)
        except:
            pass
        for b in self.buttonList:
            print b, b.selectionList, b.label
            filename = str(b.label).replace(':','')+".json"
            jsonfile = os.path.join(filepath, filename)
            print b.selectionList
            objs = cmds.sets(b.selectionList,q=1)
            print "OBJS=",objs
            data = {"label" :  str(b.label), "set_name":str(b.selectionList), "objects":objs}

            print jsonfile
            print data
            with open(jsonfile, 'w') as outfile:
                json.dump(data, outfile)

    def loadJsonFiles(self):
        filepath = PICKER_JSON_DIR
        fname = QFileDialog.getOpenFileNames(self, 'Open file',
                                            filepath, "Json files (*.json)")

        fnames = fname[0]
        data = None
        for f in fnames:
            f = str(f)
            print str(f)
            with open(f, 'r') as outfile:
                data = json.load(outfile)
            label = data["label"]
            set_name = data["set_name"]
            objs = data["objects"]
            if cmds.objExists(set_name):
                print "skipping set {0} it already exists".format(set_name)
                continue
            cmds.select(cl=True)
            for o in objs:
                if cmds.objExists(str(o)):
                    cmds.select(str(o), add=True)
            #cmds.select(objs)
            cmds.sets(name=set_name)
            cmds.addAttr(set_name,ln='label',dt='string')
            cmds.setAttr(set_name+'.label',str(label), type='string')
            self.loadItem(selSet=set_name, label=label)
        cmds.select(cl=1)

    def checkNewItem(self):
        self.addNewItem()


    def addNewItem(self):
        '''This creates a new set when the button is pressed
        The objects are already selected'''
        objs = cmds.ls(sl=True, type='transform')
        if len(objs) == 0 or objs is None:
            return
        # first guess at a label
        label = objs[0].replace(':','_')

        # Create the set
        set_name =  (PICKER_SET_PREFIX + objs[0]).replace(':','_')
        thisSet = cmds.sets(name=set_name)
        print("MADE THISSET:", set_name)

        # add an attr called label that will be the text displayed in the picker
        cmds.addAttr(thisSet, ln='label', dt='string')
        cmds.setAttr(thisSet + '.label', objs[0], type='string')
        self.loadItem(thisSet,label=label)

    def loadItem(self, selSet, label=None ):
        '''This creates a new button from an existing selectionSet'''
        (x, y) = self._findVacantGridSlot()
        val = "{0}x{1}".format(x, y)
        # Actually create the button
        b = SelectItemButton(selectionList=selSet, parent=self, gridPos=val,
                             label=label)

        #b.lineEdit.setText(label)
        self.layout.addWidget(b, y, x)
        # self.layout.addWidget(b)

        icon = QIcon()
        icon.addPixmap(UP_ICON)
        b.setIcon(icon)
        b.setIconSize(QSize(40, ICON_SIZE))
        b.setFixedWidth(ICON_SIZE)
        b.setToolTip(selSet)
        # b.clicked.connect(lambda: b.selectThis(objs))
        b.setStyleSheet('background-color:black; color: white')
        self.buttonList.append(b)

    def selectThis(self, o):
        cmds.select(str(o), replace=True)


ui = None


# this can be run as a standalone widget
def main():
    global ui
    ui = Dock(PickerAddWidget, winTitle='add item widget')
    return ui
