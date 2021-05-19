
WIN_TITLE = "Audio Settings"

SETTINGS_HEADER_UI_FILE = "audio_settings_header.ui"

KEYFRAME_DISPLAY_UI_FILE = "audio_keyframe_display.ui"

WINDOW_WIDTH = 600
WINDOW_HEIGHT = 500
HEADER_HEIGHT = 100
KEYFRAME_HEIGHT = 50
TEXT_EDIT_HEIGHT_PER_LINE = 17


import sys
import os
import string
from maya import cmds
from maya import OpenMayaUI
from maya import OpenMaya
from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *
from PySide2.QtUiTools import *
from shiboken2 import wrapInstance

from audio_core import loadAudioAttrs, loadAudioGroupsFromPy, setupAudioNode, audio_keyframe_updated
from audio_core import getEventKeyframeAtTime, getEventKeyframeTimes, setGlobalActiveKeyframes
from audio_core import changeTimelineTickColorAtTime, resetTimelineTickColorAtTime
from audio_core import getStimulationSetting, setStimulationSetting, STIM_PARAM_RANGE, STIM_TOOLTIP
from audio_core import EVENT_NAME_ATTR, PROB_ATTR, EVENT_NAME_DELIMITER, SELECTED_GROUP_ENV_VAR
import timeline_callbacks


mayaMainWindowPtr = OpenMayaUI.MQtUtil.mainWindow()
mayaMainWindow = wrapInstance(long(mayaMainWindowPtr), QWidget)


def updateWidgetText(widget, palette=None, text=None):
    if not palette:
        palette = QPalette()
    if text is None:
        text = widget.text()
    widget.clear()
    widget.setPalette(palette)
    widget.insert(str(text))


def showInvalidInput(widget, palette=None, color=Qt.red):
    if not palette:
        palette = QPalette()
    palette.setColor(QPalette.Text, color)
    updateWidgetText(widget, palette)


class GlobalAudioSettings(QWidget):
    def __init__(self, *args, **kwargs):
        super(GlobalAudioSettings,self).__init__(*args, **kwargs)
        self.setParent(mayaMainWindow)
        self.setWindowFlags(Qt.Window)
        self.headerWidget = None
        self.gridCount = 0
        self.scroll = None
        self.scrollWidget = None
        self.scrollLayout = None
        self.vbox = None
        self.widget = None
        self.keyframeWidgets = []
        self.initUI()
        setupAudioNode(None)
        self.rangeChangeCallbackId = timeline_callbacks.addRangeChangeCallback(self.refreshUI)
        self.sceneOpenedCallbackId = OpenMaya.MEventMessage.addEventCallback("SceneOpened", self.refreshSceneChanged)
        self.newSceneOpenedCallbackId = OpenMaya.MEventMessage.addEventCallback("NewSceneOpened", self.clearUI)
        audio_keyframe_updated.audio_keyframe_change.connect(self.refreshUI)

    def closeEvent(self, *args, **kwargs):
        self.headerWidget.doGroupChanged(0, resetAll=True)
        timeline_callbacks.removeRangeChangeCallback(self.rangeChangeCallbackId)
        OpenMaya.MMessage.removeCallback(self.sceneOpenedCallbackId)
        OpenMaya.MMessage.removeCallback(self.newSceneOpenedCallbackId)
        super(GlobalAudioSettings,self).closeEvent(*args, **kwargs)

    def refreshSceneChanged(self, arg=None):
        setupAudioNode(None)
        self.refreshUI()

    def _addWidgetToGrid(self, widget, column=0, lastInRow=True):
        self.grid.addWidget(widget, self.gridCount, column)
        if lastInRow:
            self.gridCount += 1

    def initUI(self):

        self.setGeometry(100, 100, WINDOW_WIDTH, WINDOW_HEIGHT)
        self.setWindowTitle(WIN_TITLE)

        # At the top layer, a grid layout is used to hold buttons and widgets
        self.grid = QGridLayout(self)

        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
        # TODO: Can we use the following instead of forcing the window to always stay on top?
        #self.setProperty("saveWindowPref", True)
        # Along with that setProperty() call, we may need to call setObjectName() to give it a name.

        self.show()
        self.setLayout(self.grid)
        self.addHeaderWidget()

        # The scroll area holds the list of all audio keyframes that are set
        self.initScrollArea()

    def refreshUI(self, arg=None):
        self.headerWidget.doGroupChanged(None)

    def initScrollArea(self):
        # The scroll area holds the list of all audio keyframes that are set
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

    def addHeaderWidget(self):
        self.headerWidget = AudioSettingsHeader(self.widget, self.changeGroup)
        self._addWidgetToGrid(self.headerWidget.ui)
        self.headerWidget.ui.setMinimumSize(WINDOW_WIDTH, HEADER_HEIGHT)
        self.headerWidget.ui.show()

    def displayAudioKeyframe(self, keyframeTime, audioNames, probabilities):
        keyframe = AudioKeyframeDisplay(self.scrollWidget, keyframeTime, audioNames, probabilities)
        self.keyframeWidgets.append(keyframe)
        self.scrollLayout.addWidget(keyframe.ui)
        keyframe.ui.show()

    def fillKeyframes(self, currentGroup=None):
        minTime = cmds.playbackOptions(query=True, minTime=True)
        maxTime = cmds.playbackOptions(query=True, maxTime=True)
        keyframeTimes = getEventKeyframeTimes()
        if not keyframeTimes:
            return
        keyframeTimes = [x for x in keyframeTimes if x >= minTime and x <= maxTime]
        if keyframeTimes:
            allAudioEvents, audioIds, groupedAudioNames = loadAudioAttrs()
            if currentGroup:
                currentGroup = EVENT_NAME_DELIMITER + currentGroup + EVENT_NAME_DELIMITER
            for keyframeTime in keyframeTimes:
                keyframe = getEventKeyframeAtTime(keyframeTime, allAudioEvents)
                if keyframe:
                    audioNames = keyframe[EVENT_NAME_ATTR]
                    if currentGroup and currentGroup not in audioNames[0]:
                        continue
                    try:
                        probabilities = keyframe[PROB_ATTR]
                    except KeyError:
                        probabilities = []
                    self.displayAudioKeyframe(keyframeTime, audioNames, probabilities)

    def clearUI(self, arg=None):
        for keyframe in self.keyframeWidgets:
            keyframe.included = False
            keyframe.ui.setParent(None)
            keyframe.setParent(None)
            keyframe.ui.hide()
            keyframe.hide()

    def changeGroup(self, currentGroup):
        if currentGroup in ['None']:
            currentGroup = None
        self.clearUI()
        self.fillKeyframes(currentGroup)


class AudioSettingsHeader(QWidget):
    def __init__(self, parent, groupChangedCallback, *args, **kwargs):
        super(AudioSettingsHeader,self).__init__(*args, **kwargs)
        self.setParent(parent)
        self.activeKeyframes = None
        self.groupChangedCallback = groupChangedCallback
        currentDir = os.path.dirname(__file__)
        self.headerUiFile = QFile(os.path.join(currentDir, SETTINGS_HEADER_UI_FILE))
        self.initUI()

    def initUI(self):
        # Load UI config from HEADER_UI_FILE
        loader = QUiLoader()
        self.headerUiFile.open(QFile.ReadOnly)
        self.ui = loader.load(self.headerUiFile, parentWidget=self.parent())
        self.headerUiFile.close()

        # Add groups to the pulldown menu in alphabetical order
        self.ui.groupComboBox.addItem("None")
        groups = loadAudioGroupsFromPy()
        groups.sort()
        for group in groups:
            self.ui.groupComboBox.addItem(group)
        self.ui.groupComboBox.activated.connect(self.doGroupChanged)
        self.doGroupChanged(0)

        # Setup buttons to jump between keyframes of the selected group
        self.ui.lastKey.clicked.connect(self.lastKey)
        self.ui.lastKey.setIcon(self.ui.lastKey.style().standardIcon(QStyle.SP_MediaSeekBackward))
        self.ui.nextKey.clicked.connect(self.nextKey)
        self.ui.nextKey.setIcon(self.ui.nextKey.style().standardIcon(QStyle.SP_MediaSeekForward))

        # Update the audio stimulation setting env var when the user updates stim parameter in UI
        if STIM_TOOLTIP:
            self.ui.stimSetting.setToolTip(STIM_TOOLTIP)
        self.ui.stimSetting.editingFinished.connect(self.doStimChanged)

    def _getActiveKeyframesInRange(self, allActiveKeyframes):
        minTime = cmds.playbackOptions(query=True, minTime=True)
        maxTime = cmds.playbackOptions(query=True, maxTime=True)
        activeCount = len(allActiveKeyframes)
        minIdx = 0
        maxIdx = activeCount - 1
        for idx in xrange(activeCount):
            if allActiveKeyframes[idx] >= minTime:
                minIdx = idx
                break
        for idx in xrange(maxIdx, -1, -1):
            if allActiveKeyframes[idx] <= maxTime:
                maxIdx = idx
                break
        return allActiveKeyframes[minIdx:maxIdx+1]

    def lastKey(self):
        activeInRange = self._getActiveKeyframesInRange(self.activeKeyframes)
        if not activeInRange:
            return
        current = cmds.currentTime(query=True)
        if current == activeInRange[0]:
            key = activeInRange[-1]
        else:
            for idx in range(len(activeInRange)):
                key = activeInRange[idx]
                if key < current and current <= activeInRange[idx+1]:
                    break
        if key != current:
            cmds.currentTime(key, edit=True)

    def nextKey(self):
        activeInRange = self._getActiveKeyframesInRange(self.activeKeyframes)
        if not activeInRange:
            return
        current = cmds.currentTime(query=True)
        if current == activeInRange[-1]:
            key = activeInRange[0]
        else:
            for idx in range(len(activeInRange)):
                key = activeInRange[idx]
                if key > current:
                    break
            else:
                key = activeInRange[0]
        if key != current:
            cmds.currentTime(key, edit=True)

    def doStimChanged(self, paramRange=STIM_PARAM_RANGE):
        currentStim = self.ui.stimSetting.text().strip()

        if not currentStim:
            # If no stim value was provided, try to use the previous value
            currentStim = getStimulationSetting()
            if currentStim is not None:
                updateWidgetText(self.ui.stimSetting, text=currentStim)
            return

        try:
            currentStim = float(currentStim)
        except (ValueError, TypeError):
            # This stim value is invalid (not float value), so change text to red and then abort
            showInvalidInput(self.ui.stimSetting)
            return

        if currentStim < paramRange[0] or currentStim > paramRange[1]:
            # This stim value is not in the valid range, so change text to red and then abort
            showInvalidInput(self.ui.stimSetting)
            return

        # This resets the text to normal if it was previously red but we now have valid input
        updateWidgetText(self.ui.stimSetting)

        paramName = str(self.ui.stimLabel.text())
        paramName = paramName.strip(string.punctuation)

        setStimulationSetting(currentStim, paramName)

    def doGroupChanged(self, itemIdx, groupEnvVar=SELECTED_GROUP_ENV_VAR, resetAll=False, verbose=False):
        keyframeTimes = getEventKeyframeTimes()
        if not keyframeTimes:
            return
        currentGroup = None
        if not resetAll:
            currentGroup = self.ui.groupComboBox.currentText().strip()
        if currentGroup in [None, "None"]:
            resetAll = True
            os.environ[groupEnvVar] = ''
        else:
            resetAll = False
            os.environ[groupEnvVar] = currentGroup
        if not resetAll:
            allAudioEvents, audioIds, groupedAudioNames = loadAudioAttrs()
        resetTimes = []
        changedTimes = []
        for keyframeTime in keyframeTimes:
            if resetAll:
                resetTimelineTickColorAtTime(keyframeTime)
                resetTimes.append(keyframeTime)
            else:
                thisKeyframe = getEventKeyframeAtTime(keyframeTime, allAudioEvents)
                if thisKeyframe:
                    audioEvent = thisKeyframe[EVENT_NAME_ATTR][0]
                    if EVENT_NAME_DELIMITER + currentGroup + EVENT_NAME_DELIMITER in audioEvent:
                        changeTimelineTickColorAtTime(keyframeTime)
                        changedTimes.append(keyframeTime)
                    else:
                        resetTimelineTickColorAtTime(keyframeTime)
                        resetTimes.append(keyframeTime)
        if resetAll:
            self.activeKeyframes = resetTimes
        else:
            self.activeKeyframes = changedTimes
        setGlobalActiveKeyframes(self.activeKeyframes)
        if self.groupChangedCallback:
            try:
                self.groupChangedCallback(currentGroup)
            except AttributeError:
                pass
        if verbose and resetTimes:
            print("Reset timeline ticks at frames %s" % resetTimes)
        if verbose and changedTimes:
            print("Changed timeline tickets for group '%s' at frames %s" % (currentGroup, changedTimes))
        return currentGroup


class AudioKeyframeDisplay(QWidget):
    def __init__(self, parent, keyframeTime, audioNames, probabilities, *args, **kwargs):
        super(AudioKeyframeDisplay,self).__init__(*args, **kwargs)
        #self.setParent(parent)
        currentDir = os.path.dirname(__file__)
        self.keyframe_display_ui_file = QFile(os.path.join(currentDir, KEYFRAME_DISPLAY_UI_FILE))
        self.keyframeTime = keyframeTime
        self.audioNames = audioNames
        self.probabilities = probabilities
        self.included = True
        self.initUI()

    def _increaseFontSize(self, widget, newSize=16):
        font = widget.font()
        font.setPointSize(newSize)
        widget.setFont(font)

    def _increaseWidgetHeight(self, widget, minHeight):
        currentHeight = widget.size().height()
        if minHeight > currentHeight:
            widget.setFixedHeight(minHeight)

    def initUI(self):
        # Load UI config from UI_FILE
        loader = QUiLoader()
        self.keyframe_display_ui_file.open(QFile.ReadOnly)
        self.ui = loader.load(self.keyframe_display_ui_file, parentWidget=self.parent())
        self.keyframe_display_ui_file.close()

        # Setup the button that shows the frame number
        keyframeTime = self.keyframeTime
        if keyframeTime == round(keyframeTime):
            keyframeTime = int(round(keyframeTime))
        self._increaseFontSize(self.ui.frame)
        self.ui.frame.setText(str(keyframeTime))
        self.ui.frame.clicked.connect(self.changeFrame)

        # Setup the box that shows event names
        events = []
        for idx in range(len(self.audioNames)):
            try:
                prob = self.probabilities[idx]
            except (KeyError, IndexError):
                prob = None
                events.append(self.audioNames[idx])
            else:
                displayStr = "%s  (%s)" % (self.audioNames[idx], prob)
                events.append(displayStr)
        fullDisplay = os.linesep.join(events)
        neededHeight = len(events) * TEXT_EDIT_HEIGHT_PER_LINE
        if len(events) > 0:
            self._increaseWidgetHeight(self.ui.events, neededHeight)
            if len(events) == 1 and (prob == 100 or prob is None):
                self._increaseFontSize(self.ui.events)
                if fullDisplay.endswith("(100)"):
                    fullDisplay = fullDisplay[:-5]
            # TODO: Why doesn't the following vertical alignment work?
            self.ui.events.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            fullDisplay = fullDisplay.strip()
            self.ui.events.setText(fullDisplay)
        self.ui.events.setReadOnly(True)

        # Increase frame number button size if needed
        self._increaseWidgetHeight(self.ui.frame, neededHeight)

        # Set minimum size for this widget
        if neededHeight > KEYFRAME_HEIGHT:
            self.ui.setMinimumSize(WINDOW_WIDTH, (neededHeight + 10))
        else:
            self.ui.setMinimumSize(WINDOW_WIDTH, KEYFRAME_HEIGHT)

    def changeFrame(self):
        cmds.currentTime(self.keyframeTime, edit=True)


def main():
    ui = GlobalAudioSettings()
    ui.show()
    ui.fillKeyframes()
    return ui


if __name__ == '__main__':
    main()


