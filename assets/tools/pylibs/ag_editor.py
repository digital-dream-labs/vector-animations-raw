
# This is used for the Animation Group editor that animators use in Maya.


ALLOWED_ASSET_TYPES = ["Animation", "Legacy Animation"]
DEFAULT_AG_DIRECTORY = "animationGroups"
ANIM_DIR_ENV_VAR = "ANKI_ANIM_DIR"
FILE_EXT = ".json"
FILE_BROWSER_FILTER = "animation group files (*%s)" % FILE_EXT
FILE_BROWSER_WIN_TITLE  = "Select an existing file OR specify new file "
FILE_BROWSER_WIN_TITLE += "directory/name for animation group..."
ANIM_GROUP_WIN_TITLE = "Animation Group (%s)"
UI_FILE = "ag_editor.ui"
CLIP_NAME_KEY = "clip_name"
ALL_CATEGORY_DISPLAY = "(all)"


import sys
import os
import copy
import json
import pprint
import re
from collections import OrderedDict
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

from anim_groups import JSON_TOP_KEY, NAME_ATTR, WEIGHT_ATTR, COOLDOWN_ATTR, MOOD_ATTR, MOODS
from anim_groups import USE_HEAD_ANGLE_ATTR, HEAD_ANGLE_MIN_ATTR, HEAD_ANGLE_MAX_ATTR
from anim_groups import HEAD_ANGLE_ATTRS_SORTED, ALL_ATTRS_SORTED, NUMERICAL_ATTRS
from anim_groups import DEFAULT_WEIGHT, DEFAULT_COOLDOWN_TIME
from ankimaya import game_exporter
from ankimaya.head_angle_selector import getHeadAngleVariationExportSettings
from ankiutils.head_angle_config import HeadAngleConfig


mayaMainWindowPtr = omui.MQtUtil.mainWindow()
mayaMainWindow = wrapInstance(long(mayaMainWindowPtr), QWidget)


def _getDefaultAnimGroupDir(dirName=DEFAULT_AG_DIRECTORY):
    animDir = os.getenv(ANIM_DIR_ENV_VAR)
    if not animDir:
        return None
    agDir = os.path.join(os.path.dirname(animDir), dirName)
    if os.path.isdir(agDir):
        return agDir
    else:
        return None


def get_sg_project_name(dir_path_env_var="ANKI_ANIM_DIR"):
    """
    This method uses the directory path that the "ANKI_ANIM_DIR" environment
    variable points at to determine which Shotgun project should be used.
    """
    from ankishotgun.anim_data import get_project_name_from_file
    dir_path = os.getenv(dir_path_env_var)
    if dir_path:
        return get_project_name_from_file(dir_path)
    else:
        warnMsg = "No valid setting for the '%s' environment variable" % dir_path_env_var
        cmds.warning(warnMsg)
        return None


def get_assets_by_category(allowed_asset_types=None):
    """
    This function will get all animation assets/clips from Shotgun,
    with their associated category/group. This function will return
    a dictionary where the keys are category/group names and the
    values are the list of animation assets/clips that are part of
    that category/group.
    """
    from ankishotgun.anim_data import ShotgunAssets, SG_PROJECTS
    if allowed_asset_types is None:
        allowed_asset_types = ALLOWED_ASSET_TYPES
    assets_by_category = {}
    assets_by_category[ALL_CATEGORY_DISPLAY] = []
    sg_proj = get_sg_project_name()
    if sg_proj is None:
        sg_proj = SG_PROJECTS[0]
        warnMsg = "Unable to determine which Shotgun project to use; using '%s' by default" % sg_proj
        cmds.warning(warnMsg)
    sg_assets = ShotgunAssets()
    all_assets = sg_assets.get_all_assets(SG_PROJECTS)
    try:
        all_assets = all_assets[sg_proj]
    except KeyError:
        warnMsg = "Invalid Shotgun project: %s" % sg_proj
        cmds.warning(warnMsg)
        assets_by_category[''] = []
        return assets_by_category
    for asset in all_assets:
        asset_type = asset[sg_assets.asset_type_attr]
        if asset_type and allowed_asset_types and asset_type not in allowed_asset_types:
            continue
        name = asset[sg_assets.asset_name_attr]
        category = asset[sg_assets.category_attr]
        if category is None:
            category = ''
        if category in assets_by_category:
            assets_by_category[category].append(name)
        else:
            assets_by_category[category] = [name]
        assets_by_category[ALL_CATEGORY_DISPLAY].append(name)
    return assets_by_category


class EditAnimGroupUI(QWidget):
    def __init__(self, *args, **kwargs):
        super(EditAnimGroupUI,self).__init__(*args, **kwargs)
        self.setParent(mayaMainWindow)
        self.setWindowFlags(Qt.Window)
        self.updateExisting = False
        self.animGroupName = None
        self.animGroupFile = None
        self.addAnimWidgets = []
        self.gridCount = 0
        self.scroll = None
        self.scrollWidget = None
        self.scrollLayout = None
        try:
            self.assets_by_category = get_assets_by_category()
        except BaseException, e:
            cmds.warning("Unable to query assets because: %s" % e)
            self.assets_by_category = {}
            self.assets_by_category[''] = []
        for category in self.assets_by_category.keys():
            self.assets_by_category[category].sort()
        self.initUI()

    def _checkAnimGroupFile(self):
        """
        Confirm that an animation group file was specified and then
        load that animation group if it already exists or confirm
        creation of a new animation group.
        """
        if self.animGroupFile is None:
            animGroupName = None
        else:
            if not self.animGroupFile.endswith(FILE_EXT):
                self.animGroupFile += FILE_EXT
            if os.path.isfile(self.animGroupFile):
                animGroupName = self.loadExistingFile(self.animGroupFile)
                self.updateExisting = True
            else:
                animGroupDir = os.path.dirname(self.animGroupFile)
                animGroupName = os.path.basename(self.animGroupFile)
                animGroupName = animGroupName.lower()
                self.animGroupFile = os.path.join(animGroupDir, animGroupName)
                animGroupName = os.path.splitext(animGroupName)[0]
                animGroupName = self.alertUserNewAnimGroup(animGroupName)
            self.setWindowTitle(ANIM_GROUP_WIN_TITLE % animGroupName)
        if animGroupName:
            print("Animation group name = [%s] and file = [%s]"
                  % (animGroupName, self.animGroupFile))
        return animGroupName

    def alertUserNewAnimGroup(self, animGroupName):
        """
        Use a message box to confirm creation of new animation group.
        """
        reply = QMessageBox.question(self, "Message",
            "Create new '%s' animation group?" % animGroupName,
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            return animGroupName
        else:
            return None

    def _addWidgetToGrid(self, widget, column=0, lastInRow=True):
        self.grid.addWidget(widget, self.gridCount, column)
        if lastInRow:
            self.gridCount += 1

    def initUI(self):

        self.setGeometry(300, 300, 1100, 500)
        self.setWindowTitle(FILE_BROWSER_WIN_TITLE)

        # At the top layer, a grid layout is used to hold buttons and widgets
        self.grid = QGridLayout(self)

        # Use file browser widget to have the user specify the animation group
        # name and file that is being created or edited. This method aborts if
        # both of those are not specified.
        fileBrowser = QFileDialog()
        fileBrowser.setOption(QFileDialog.DontUseNativeDialog)
        agDir = _getDefaultAnimGroupDir()
        if agDir:
            fileBrowser.setDirectory(agDir)
        fileBrowser.setFileMode(QFileDialog.AnyFile)
        fileBrowser.setNameFilter(FILE_BROWSER_FILTER)
        self._addWidgetToGrid(fileBrowser)

        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
        # TODO: Can we use the following instead of forcing the window to always stay on top?
        #self.setProperty("saveWindowPref", True)
        # Along with that setProperty() call, we may need to call setObjectName() to give it a name.

        self.show()
        if fileBrowser.exec_():
            self.animGroupFile = fileBrowser.selectedFiles()[0]

        # Add add-another-anim-clip button to the grid layout
        addAnimBtn = QPushButton("Include Another Animation in Group...")
        addAnimBtn.clicked.connect(self.addAnimToGroup)
        self._addWidgetToGrid(addAnimBtn)

        # Add copy-anim-clips-from-game-exporter button to the grid layout
        syncClipsBtn = QPushButton("Copy Animation Clips from Game Exporter")
        syncClipsBtn.clicked.connect(self.syncWithGameExporter)
        self._addWidgetToGrid(syncClipsBtn)

        # The scroll area holds the list of one or more anim clips for the anim group
        self.initScrollArea()

        self.setLayout(self.grid)

        # Load or create animation group
        self.animGroupName = self._checkAnimGroupFile()
        if self.animGroupName is None:
            self.close()
            return None

        # If this is a new animation group, add widget for first anim clip
        if not self.updateExisting:
            self.addAnimToGroup()

        self.addBottomButtons()

    def addBottomButtons(self):
        self.bottomBtns = QGridLayout(self)

        # Add create button to the grid layout
        self.createBtn = QPushButton("Create")
        self.createBtn.clicked.connect(self.doCreate)
        self.bottomBtns.addWidget(self.createBtn, 0, 0)

        # Add apply button to the grid layout
        self.applyBtn = QPushButton("Apply")
        self.applyBtn.clicked.connect(self.doApply)
        self.bottomBtns.addWidget(self.applyBtn, 0, 1)

        # Add close button to the grid layout
        self.closeBtn = QPushButton("Close")
        self.closeBtn.clicked.connect(self.doClose)
        self.bottomBtns.addWidget(self.closeBtn, 0, 2)

        self.bottomBtnsWidget = QWidget()
        self.bottomBtnsWidget.setLayout(self.bottomBtns)
        self._addWidgetToGrid(self.bottomBtnsWidget)

    def initScrollArea(self):
        # The scroll area holds the list of one or more anim clips for the anim group
        self.scrollWidget = QWidget()
        #self.scrollWidget.setParent(self)
        self.scrollLayout = QVBoxLayout(self.scrollWidget)
        self.scrollWidget.setLayout(self.scrollLayout)
        self.scroll = QScrollArea(self)
        self.scroll.setWidgetResizable(True)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setWidget(self.scrollWidget)
        self._addWidgetToGrid(self.scroll)

    def getPrevAnim(self, numAnimClips=None):
        if numAnimClips is None:
            numAnimClips = len(self.addAnimWidgets)
        prevAnimClip = self.addAnimWidgets[numAnimClips-1]
        if prevAnimClip and not prevAnimClip.included:
            prevAnimClip = self.getPrevAnim(numAnimClips-1)
        return prevAnimClip

    def addAnimToGroup(self):
        try:
            prevAnim = self.getPrevAnim()
        except IndexError:
            prevAnim = None
        anim = AddAnimWidget(self.scrollWidget, self.assets_by_category)
        self.addAnimWidgets.append(anim)
        self.scrollLayout.addWidget(anim.ui)
        anim.ui.setMinimumSize(1050, 220)
        if prevAnim:
            self.copyAnimWidget(anim, prevAnim)
        anim.ui.show()

    def syncWithGameExporter(self):

        # Clear any existing anim clips...
        for animWidget in self.addAnimWidgets:
            animWidget.ui.confirmComboBox.setChecked(True)
            animWidget.confirmRemoveAnimChanged()
        self.addAnimWidgets = []

        # Get anim clips from Game Exporter...
        gameExporterAnims = game_exporter.get_clip_info('', include_all=True)[2]
        gameExporterAnims = [str(x[CLIP_NAME_KEY]) for x in gameExporterAnims]
        print("Animation clips listed in Game Exporter = %s" % gameExporterAnims)

        if gameExporterAnims:
            # These anim clips will NOT be added to any specific category
            if '' not in self.assets_by_category:
                self.assets_by_category[''] = []

            # Get info for any head angle variations...
            numVariations, whichKeyframes = getHeadAngleVariationExportSettings()
            print("Number of head angle variations = %s" % numVariations)

        # Add all anim clips from Game Exporter...
        animClips = []
        headAngleConfig = HeadAngleConfig()
        for anim in gameExporterAnims:
            if numVariations:
                varMapping = headAngleConfig.get_anim_variation_to_range_mapping(anim, numVariations)
                sortedClips = varMapping.keys()
                sortedClips.sort()
                for clip in sortedClips:
                    angleRange = varMapping[clip]
                    if clip not in self.assets_by_category['']:
                        self.assets_by_category[''].append(clip)
                    animClip = {}
                    animClip[NAME_ATTR] = clip
                    animClip[USE_HEAD_ANGLE_ATTR] = True
                    animClip[HEAD_ANGLE_MIN_ATTR] = angleRange[0]
                    animClip[HEAD_ANGLE_MAX_ATTR] = angleRange[1]
                    animClips.append(animClip)
            else:
                if anim not in self.assets_by_category['']:
                    self.assets_by_category[''].append(anim)
                animClip = {}
                animClip[NAME_ATTR] = anim
                animClips.append(animClip)
        while len(self.addAnimWidgets) < len(animClips):
            self.addAnimToGroup()
        for idx in range(len(animClips)):
            self.fillAnimWidget(self.addAnimWidgets[idx], animClips[idx])

    def getAnimClipDict(self, animClip):
        animClipDict = {}
        for attr in ALL_ATTRS_SORTED:
            uiAttr = eval("animClip.ui.%s" % attr)
            if hasattr(uiAttr, "checkState"):
                uiValue = uiAttr.checkState()
            elif hasattr(uiAttr, "currentText"):
                uiValue = uiAttr.currentText()
            elif hasattr(uiAttr, "text"):
                uiValue = uiAttr.text()
            animClipDict[attr] = uiValue
        #clipName = animClipDict[NAME_ATTR]
        #print("anim clip = %s" % clipName)
        for key, value in animClipDict.items():
            if key in NUMERICAL_ATTRS and value:
                animClipDict[key] = float(value)
            elif value == Qt.CheckState.Unchecked:
                animClipDict[key] = False
            elif value == Qt.CheckState.Checked:
                animClipDict[key] = True
        if animClipDict[USE_HEAD_ANGLE_ATTR]:
            for headAngleAttr in HEAD_ANGLE_ATTRS_SORTED:
                if animClipDict[headAngleAttr] == '':
                    raise ValueError("Value must be provided for '%s'" % headAngleAttr)
        #pprint.pprint(animClipDict)
        return animClipDict

    def doApply(self, problems=None):
        if problems is None:
            problems = []
        numAnimClips = len(self.addAnimWidgets)
        animsUsed = []
        animClipDicts = []
        for idx in range(numAnimClips):
            thisAnimClip = self.addAnimWidgets[idx]
            if not thisAnimClip.included:
                continue
            try:
                animClip = self.getAnimClipDict(thisAnimClip)
            except ValueError:
                nameAttr = eval("thisAnimClip.ui.%s" % NAME_ATTR)
                clipName = nameAttr.currentText()
                errorMsg = "Invalid data provided for '%s' animation" % clipName
                cmds.warning(errorMsg)
                QMessageBox.critical(self, "Alert", errorMsg)
                problems.append(clipName)
                return None
            if animClip:
                try:
                    name = animClip[NAME_ATTR]
                except KeyError:
                    name = None
                if not name:
                    errorMsg = "Invalid name provided for at least one animation"
                    cmds.warning(errorMsg)
                    QMessageBox.critical(self, "Alert", errorMsg)
                    problems.append("clip-%s" % idx)
                    return None
                elif name in animsUsed:
                    errorMsg = "The '%s' animation appears to be included more than once" % name
                    cmds.warning(errorMsg)
                    QMessageBox.critical(self, "Alert", errorMsg)
                    problems.append("clip-%s" % idx)
                    return None
                animClipDicts.append(animClip)
                animsUsed.append(name)
        self.writeFile(animClipDicts, self.animGroupFile)

    def doCreate(self):
        problems = []
        self.doApply(problems)
        if not problems:
            self.close()

    def doClose(self):
        self.close()

    def copyAnimWidget(self, newAnimWidget, oldAnimWidget):
        oldCategory = oldAnimWidget.ui.categoryComboBox.currentText()
        oldName = oldAnimWidget.ui.Name.currentText()
        idx = newAnimWidget.ui.categoryComboBox.findText(oldCategory)
        newAnimWidget.ui.categoryComboBox.setCurrentIndex(idx)
        newAnimWidget.doCategoryChanged()
        idx = newAnimWidget.ui.Name.findText(oldName)
        newAnimWidget.ui.Name.setCurrentIndex(idx)

    def fillAnimWidget(self, animWidget, clipInfo):
        for category, anims in self.assets_by_category.items():
            if category == ALL_CATEGORY_DISPLAY:
                continue
            if clipInfo[NAME_ATTR] in anims:
                idx = animWidget.ui.categoryComboBox.findText(category)
                animWidget.ui.categoryComboBox.setCurrentIndex(idx)
                animWidget.doCategoryChanged()
                break
        else:
            if '' not in self.assets_by_category:
                self.assets_by_category[''] = []
            if clipInfo[NAME_ATTR] not in self.assets_by_category['']:
                self.assets_by_category[''].append(clipInfo[NAME_ATTR])
                idx = animWidget.ui.categoryComboBox.findText('')
                animWidget.ui.categoryComboBox.setCurrentIndex(idx)
                animWidget.doCategoryChanged()

        for attr, value in clipInfo.items():
            uiAttr = eval("animWidget.ui.%s" % attr)
            if hasattr(uiAttr, "setChecked"):
                uiAttr.setChecked(value)
            elif hasattr(uiAttr, "setCurrentIndex"):
                idx = uiAttr.findText(str(value))
                uiAttr.setCurrentIndex(idx)
            elif hasattr(uiAttr, "insert"):
                uiAttr.clear()
                uiAttr.insert(str(value))

    def loadExistingFile(self, jsonFile):
        errorMsg = "Failed to load %s" % jsonFile
        try:
            with open(jsonFile, 'r') as inFile:
                jsonData = inFile.read()
                jsonData = re.sub(r'//.*\n', os.linesep, jsonData) # remove C-style comments
                jsonData = re.sub(r'#.*\n', os.linesep, jsonData) # remove Python-style comments
                animGroup = json.loads(jsonData)
        except ValueError:
            cmds.warning(errorMsg)
            QMessageBox.critical(self, "Alert", errorMsg)
            return None
        try:
            animClips = animGroup[JSON_TOP_KEY]
        except KeyError:
            cmds.warning(errorMsg)
            QMessageBox.critical(self, "Alert", errorMsg)
            return None
        #pprint.pprint(animClips)
        while len(self.addAnimWidgets) < len(animClips):
            self.addAnimToGroup()
        for idx in range(len(animClips)):
            self.fillAnimWidget(self.addAnimWidgets[idx], animClips[idx])
        animGroupName = os.path.basename(jsonFile)
        animGroupName = animGroupName.lower()
        animGroupName = os.path.splitext(animGroupName)[0]
        return animGroupName

    def writeFile(self, animClips, jsonFile, sortOrder=ALL_ATTRS_SORTED):
        if not animClips:
            cmds.warning("No animation clips for animation group")
            return None
        for animClip in animClips:
            if not animClip[USE_HEAD_ANGLE_ATTR]:
                for headAngleAttr in HEAD_ANGLE_ATTRS_SORTED:
                    animClip.pop(headAngleAttr)
        ordered = [OrderedDict(sorted(item.iteritems(), key=lambda (k, v): sortOrder.index(k))) for item in animClips]
        animGroup = {JSON_TOP_KEY : ordered}
        try:
            with open(jsonFile, 'w') as outFile:
                json.dump(animGroup, outFile, indent=2, separators=(',', ': '))
        except (OSError, IOError), e:
            errorMsg = "Failed to write '%s' file because: %s" % (jsonFile, e)
            cmds.warning(errorMsg)
            QMessageBox.critical(self, "Alert", errorMsg)
        else:
            print("Animation group written to: %s" % jsonFile)


class AddAnimWidget(QWidget):
    def __init__(self, parent, assets_by_category, *args, **kwargs):
        super(AddAnimWidget,self).__init__(*args, **kwargs)
        #self.setParent(parent)
        self.assets_by_category = assets_by_category
        currentDir = os.path.dirname(__file__)
        self.add_anim_ui_file = QFile(os.path.join(currentDir, UI_FILE))
        self.included = True
        self.initUI()
        self.ui.Name.installEventFilter(self)
        self.ui.categoryComboBox.installEventFilter(self)

    def eventFilter(self, obj, event):
        """
        Event filter for rerouting wheel events away from combo boxes.
        """
        if event.type() == QEvent.Wheel and isinstance(obj, QComboBox):
            # Handle all wheel events for combo boxes
            event.ignore()
            return True
        else:
            return super(AddAnimWidget, self).eventFilter(obj, event)

    def closeEvent(self, e):
        """
        Remove the event filter
        """
        self.ui.Name.removeEventFilter(self)
        self.ui.categoryComboBox.removeEventFilter(self)
        return super(AddAnimWidget, self).closeEvent(e)

    def initUI(self):

        # Load UI config from UI_FILE
        loader = QUiLoader()
        self.add_anim_ui_file.open(QFile.ReadOnly)
        self.ui = loader.load(self.add_anim_ui_file, parentWidget=self.parent())
        self.add_anim_ui_file.close()

        # Setup the category/group setting, which will influence the animation clip setting.
        categories = self.assets_by_category.keys()
        categories.sort()
        for category in categories:
            self.ui.categoryComboBox.addItem(category)
        self.ui.categoryComboBox.activated.connect(self.doCategoryChanged)
        self.doCategoryChanged()

        # The anim list should be filtered by user input
        self.ui.animSearch.textChanged.connect(self.filterAnims)

        # Fill the Mood pulldown list
        for mood in MOODS:
            self.ui.Mood.addItem(mood)

        # Set defaults for Weight and Cooldown
        if DEFAULT_WEIGHT:
            self.ui.Weight.insert(DEFAULT_WEIGHT)
        if DEFAULT_COOLDOWN_TIME:
            self.ui.CooldownTime_Sec.insert(DEFAULT_COOLDOWN_TIME)

        # Setup head angle settings.
        self.ui.UseHeadAngle.stateChanged.connect(self.doHeadAngleUsageChanged)
        self.doHeadAngleUsageChanged()

        # Add pair of checkboxes to allow removal of this anim clip.
        self.ui.removeAnimComboBox.stateChanged.connect(self.removeAnimChanged)
        self.removeAnimChanged()
        self.ui.confirmComboBox.stateChanged.connect(self.confirmRemoveAnimChanged)
        self.confirmRemoveAnimChanged()

    def filterAnims(self):
        filter = self.ui.animSearch.text()
        filter = filter.lower()
        category = self.ui.categoryComboBox.currentText()
        self.ui.Name.clear()
        for anim in self.assets_by_category[category]:
            if filter in anim.lower():
                self.ui.Name.addItem(anim)

    def doCategoryChanged(self):
        # The Category/Group pulldown list is connected to the Anim Clip pulldown
        # list so the latter only lists anim clips in the selected Category/Group.
        self.ui.animSearch.clear()
        self.ui.Name.clear()
        category = self.ui.categoryComboBox.currentText()
        for anim in self.assets_by_category[category]:
            self.ui.Name.addItem(anim)

    def doHeadAngleUsageChanged(self):
        # When NOT using head angle ('self.ui.UseHeadAngle' checkbox
        # is NOT set) the min/max angle fields will be grayed out.
        if self.ui.UseHeadAngle.checkState():
            self.ui.headAngleMinLabel.setEnabled(True)
            self.ui.HeadAngleMin_Deg.setEnabled(True)
            self.ui.headAngleMaxLabel.setEnabled(True)
            self.ui.HeadAngleMax_Deg.setEnabled(True)
        else:
            self.ui.headAngleMinLabel.setEnabled(False)
            self.ui.HeadAngleMin_Deg.setEnabled(False)
            self.ui.headAngleMaxLabel.setEnabled(False)
            self.ui.HeadAngleMax_Deg.setEnabled(False)

    def removeAnimChanged(self):
        if self.ui.removeAnimComboBox.checkState():
            self.ui.confirmLabel.setEnabled(True)
            self.ui.confirmComboBox.setEnabled(True)
        else:
            self.ui.confirmLabel.setEnabled(False)
            self.ui.confirmComboBox.setEnabled(False)

    def confirmRemoveAnimChanged(self):
        if self.ui.confirmComboBox.checkState():
            self.included = False
            self.ui.setParent(None)
            self.setParent(None)
            self.ui.hide()
            self.hide()


def main():
    ui = EditAnimGroupUI()
    if ui.animGroupFile and ui.animGroupName:
        ui.show()
    return ui


if __name__ == '__main__':
    main()


