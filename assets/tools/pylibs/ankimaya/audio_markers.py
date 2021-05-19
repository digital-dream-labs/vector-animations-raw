
WIN_TITLE = "Set audio event trigger"

HEADER_UI_FILE = "audio_header.ui"
EVENTS_UI_FILE = "audio_event.ui"
STATES_UI_FILE = "audio_state.ui"
SWITCH_UI_FILE = "audio_switch.ui"
PARAMETER_UI_FILE = "audio_parameter.ui"

AUDIO_EVENT_SEPARATOR = "__"
AUDIO_EVENT_ACTION_IDX = 0
AUDIO_EVENT_GROUP_IDX = 1
AUDIO_EVENT_EVENT_IDX = 2

ALL_GROUP = "(all)"


import sys
import os
import copy
import pprint
import math
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

from audio_core import CURVE_TYPES, STATE_ID_ATTR, STATE_GROUP_ID_ATTR, AUDIO_STATE_TYPES, \
    AUDIO_SWITCH_TYPES, AUDIO_PARAMETER_TYPES, EVENT_NAME_ATTR, PARAMETER_NAME_ATTR, CURVE_ATTR, \
    NUMERICAL_ATTRS, INT_ATTRS, FLOAT_ATTRS, ALL_ATTRS, PROB_ATTR, VOLUME_ATTR, SWITCH_ID_ATTR, \
    NUMERICAL_EVENT_ATTR_VALUES, VALUE_ATTR, TIME_MS_ATTR, AUDIO_ENUM_ATTR, SWITCH_GROUP_ID_ATTR, \
    AUDIO_NODE_NAME, ALT_SOUNDS_ATTR

from audio_core import audio_keyframe_updated, playAudioEvent, loadAudioAttrsFromPy, \
    setupAudioNode, setAudioEventKeyframe, setAudioParameterKeyframe, getEventKeyframe, \
    getAudioKeyframe, removeAudioKeys, refreshAttrAndVariants, syncWwisePlugin

import timeline_callbacks


GROUP_ATTRS = [STATE_GROUP_ID_ATTR]

EVENT_UI_ATTR_NAME_DICT = {EVENT_NAME_ATTR: AUDIO_ENUM_ATTR}

PARAMETER_UI_ATTR_NAME_DICT = {EVENT_NAME_ATTR: PARAMETER_NAME_ATTR}

SWITCH_UI_ATTR_NAME_DICT = {STATE_ID_ATTR: SWITCH_ID_ATTR,
                            STATE_GROUP_ID_ATTR: SWITCH_GROUP_ID_ATTR}

DISPLAYED_PARAMETER_ATTRS = {PARAMETER_NAME_ATTR: EVENT_NAME_ATTR,
                             VALUE_ATTR: VALUE_ATTR,
                             CURVE_ATTR: CURVE_ATTR,
                             TIME_MS_ATTR:TIME_MS_ATTR}

DISPLAYED_STATE_ATTRS = {STATE_GROUP_ID_ATTR: STATE_GROUP_ID_ATTR,
                         STATE_ID_ATTR: STATE_ID_ATTR}

DISPLAYED_SWITCH_ATTRS = {SWITCH_ID_ATTR: STATE_ID_ATTR,
                          SWITCH_GROUP_ID_ATTR: STATE_GROUP_ID_ATTR}

PARAMETER_UI_ATTRS = [EVENT_NAME_ATTR, CURVE_ATTR, VALUE_ATTR, TIME_MS_ATTR]

STATE_UI_ATTRS = [STATE_GROUP_ID_ATTR, STATE_ID_ATTR]


UI_COORDINATES = (100, 100, 1100, 500)
HEADER_MIN_SIZE = (500, 30)
EVENT_WIDGET_MIN_SIZE = (1000, 105)
PARAMETER_WIDGET_MIN_SIZE = (1000, 105)
STATE_WIDGET_MIN_SIZE = (1000, 52)


mayaMainWindowPtr = omui.MQtUtil.mainWindow()
mayaMainWindow = wrapInstance(long(mayaMainWindowPtr), QWidget)


def getInversedPalette():
    palette = QPalette()
    palette.setColor(QPalette.Base, Qt.gray)
    palette.setBrush(QPalette.Text, Qt.black)
    return palette


def updateWidgetPalette(widget, palette, text=None):
    if text is None:
        text = widget.text()
    widget.clear()
    widget.setPalette(palette)
    widget.insert(str(text))


def sortAudioEventsByGroup(allAudioEvents, specificGroups=None, allGroup=ALL_GROUP,
                           separator=AUDIO_EVENT_SEPARATOR, groupIdx=AUDIO_EVENT_GROUP_IDX,
                           eventIdx=AUDIO_EVENT_EVENT_IDX, actionIdx=AUDIO_EVENT_ACTION_IDX):
    audioEventsByGroup = {}
    for event in allAudioEvents:
        eventParts = event.split(separator)
        try:
            group = eventParts[groupIdx]
            event_short = eventParts[eventIdx]
            action = eventParts[actionIdx]
        except IndexError:
            group = ''
        if specificGroups is None or group in specificGroups:
            if group in audioEventsByGroup:
                audioEventsByGroup[group].append(event)
            else:
                audioEventsByGroup[group] = [event]
        if allGroup:
            if allGroup in audioEventsByGroup:
                audioEventsByGroup[allGroup].append(event)
            else:
                audioEventsByGroup[allGroup] = [event]
    return audioEventsByGroup


class SetAudioTrigger(QWidget):
    def __init__(self, *args, **kwargs):
        super(SetAudioTrigger,self).__init__(*args, **kwargs)
        self.setParent(mayaMainWindow)
        self.setWindowFlags(Qt.Window)
        self.headerWidget = None
        self.eventWidgets = []
        self.actionWidgets = []
        self.parameterWidgets = []
        self.stateWidgets = []
        self.switchWidgets = []
        self.gridCount = 0
        self.scroll = None
        self.scrollWidget = None
        self.scrollLayout = None
        self.vbox = None
        self.widget = None

        self.groupedParameterNames = {}
        self.goupedEventNames = {}

        self.allAudioEvents, self.audioIds, self.groupedAudioEvents = loadAudioAttrsFromPy()
        self.audioEventsByGroup = sortAudioEventsByGroup(self.allAudioEvents)
        for group in self.audioEventsByGroup.keys():
            self.audioEventsByGroup[group].sort()

        self.allAudioStates, self.audioStateIds, self.subAudioStateIds = \
            loadAudioAttrsFromPy(audioTypes=AUDIO_STATE_TYPES, audioGroups=[], recursive=True)

        self.allAudioSwitches, self.audioSwitchIds, self.subAudioSwitchIds = \
            loadAudioAttrsFromPy(audioTypes=AUDIO_SWITCH_TYPES, audioGroups=[], recursive=True)

        self.allAudioParameters, self.audioParameterIds, self.groupedParameterNames = \
            loadAudioAttrsFromPy(audioTypes=AUDIO_PARAMETER_TYPES)

        self.allSubAudioStateIds = copy.deepcopy(self.getAllSubIds(self.subAudioStateIds))
        self.allSubAudioSwitchIds = copy.deepcopy(self.getAllSubIds(self.subAudioSwitchIds))

        self.initUI()
        self.callbackId = timeline_callbacks.addTimeChangeCallback(self.refreshUI)

    def getAllSubIds(self, subIdsDict):
        allSubAudioIds = {}
        if subIdsDict:
            for subStateDict in subIdsDict.values():
                if self.isCorrectStateDict(subStateDict):
                    allSubAudioIds.update(subStateDict)
        return allSubAudioIds

    def __del__(self, *args, **kwargs):
        timeline_callbacks.removeTimeChangeCallback(self.callbackId)
        super(SetAudioTrigger,self).__del__(*args, **kwargs)

    def close(self, *args, **kwargs):
        timeline_callbacks.removeTimeChangeCallback(self.callbackId)
        super(SetAudioTrigger,self).close(*args, **kwargs)

    def closeEvent(self, *args, **kwargs):
        timeline_callbacks.removeTimeChangeCallback(self.callbackId)
        super(SetAudioTrigger,self).closeEvent(*args, **kwargs)

    def _addWidgetToGrid(self, widget, column=0, lastInRow=True):
        self.grid.addWidget(widget, self.gridCount, column)
        if lastInRow:
            self.gridCount += 1

    def initUI(self):
        self.setGeometry(UI_COORDINATES[0], UI_COORDINATES[1], UI_COORDINATES[2], UI_COORDINATES[3])
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

        # Add add-another-event button to the grid layout
        addEventBtn = QPushButton("Add event to audio keyframe")
        addEventBtn.clicked.connect(self.addEventToKeyframe)
        self._addWidgetToGrid(addEventBtn)

        addSwitchBtn = QPushButton("Add switch to audio keyframe")
        addSwitchBtn.clicked.connect(lambda: self.addStateToKeyframe(SWITCH_UI_FILE,
                                                                     self.audioSwitchIds,
                                                                     self.subAudioSwitchIds))
        self._addWidgetToGrid(addSwitchBtn)

        addParameterBtn = QPushButton("Add parameter to audio keyframe")
        addParameterBtn.clicked.connect(self.addParameterToKeyframe)
        self._addWidgetToGrid(addParameterBtn)

        addStateBtn = QPushButton("Add state to audio keyframe")
        addStateBtn.clicked.connect(lambda: self.addStateToKeyframe(STATES_UI_FILE,
                                                                    self.audioStateIds,
                                                                    self.subAudioStateIds))
        self._addWidgetToGrid(addStateBtn)

        # The scroll area holds the list of one or more audio events to use
        self.initScrollArea()

        self.addBottomButtons()

        setupAudioNode(self.allAudioEvents)

        sub_audio_states_list = [sub_states for sub_states in self.allSubAudioStateIds.keys()]
        sub_audio_states_list.sort()

        sub_audio_switch_list = [sub_switches for sub_switches in self.allSubAudioSwitchIds.keys()]
        sub_audio_switch_list.sort()

        self.refreshEnumAttrs(enum_attr=STATE_ID_ATTR,
                              ui_attr_name_dict=None,
                              actions_list=sub_audio_states_list)

        self.refreshEnumAttrs(enum_attr=STATE_GROUP_ID_ATTR,
                              ui_attr_name_dict=None,
                              actions_list=self.allAudioStates)

        self.refreshEnumAttrs(enum_attr=STATE_ID_ATTR,
                              ui_attr_name_dict=SWITCH_UI_ATTR_NAME_DICT,
                              actions_list=sub_audio_switch_list)

        self.refreshEnumAttrs(enum_attr=STATE_GROUP_ID_ATTR,
                              ui_attr_name_dict=SWITCH_UI_ATTR_NAME_DICT,
                              actions_list=self.allAudioSwitches)

        keyframeData = self.loadExistingKeyframe()

        if not keyframeData or keyframeData == ({}, {}, {}, {}):
            self.setBtn.setEnabled(False)
        else:
            self.setBtn.setEnabled(True)

    def refreshEnumAttrs(self, enum_attr=None, ui_attr_name_dict=None, actions_list=None):
        if ui_attr_name_dict is None or enum_attr not in ui_attr_name_dict:
            if cmds.attributeQuery(enum_attr, node=AUDIO_NODE_NAME,
                                   exists=True):
                refreshAttrAndVariants(actions_list, enum_attr)
        else:
            attr = ui_attr_name_dict[enum_attr]
            if cmds.attributeQuery(attr, node=AUDIO_NODE_NAME,
                                   exists=True):
                refreshAttrAndVariants(actions_list, attr)

    def initScrollArea(self):
        # The scroll area holds the list of one or more audio events to use
        self.scrollWidget = QWidget()
        self.scrollWidget.setParent(self)
        self.scrollLayout = QVBoxLayout(self.scrollWidget)
        self.scrollWidget.setLayout(self.scrollLayout)
        self.scroll = QScrollArea(self)
        self.scroll.setWidgetResizable(True)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setWidget(self.scrollWidget)
        self._addWidgetToGrid(self.scroll)

    def addBottomButtons(self):
        self.bottomBtns = QGridLayout(self)

        # Add create button to the grid layout
        self.setBtn = QPushButton("Set Keyframe")
        self.setBtn.clicked.connect(self.doSetKeyframe)
        self.bottomBtns.addWidget(self.setBtn, 0, 0)

        # Add cancel button to the grid layout
        self.cancelBtn = QPushButton("Done")
        self.cancelBtn.clicked.connect(self.doDone)
        self.bottomBtns.addWidget(self.cancelBtn, 0, 1)

        # Add delete button to the grid layout
        self.delBtn = QPushButton("Delete Keyframe")
        self.delBtn.clicked.connect(self.doDelete)
        self.bottomBtns.addWidget(self.delBtn, 0, 2)

        self.bottomBtnsWidget = QWidget()
        self.bottomBtnsWidget.setLayout(self.bottomBtns)
        self._addWidgetToGrid(self.bottomBtnsWidget)

    def addHeaderWidget(self):
        self.headerWidget = ToolHeader(self.widget)
        self._addWidgetToGrid(self.headerWidget.ui)
        self.headerWidget.ui.setMinimumSize(HEADER_MIN_SIZE[0], HEADER_MIN_SIZE[1])
        self.headerWidget.ui.show()

    def refreshUI(self, arg=None):
        playingBack = cmds.play(q=True, state=True)
        if not playingBack:
            eventGroupIdx, parameterGroupIdx = self.clearAllKeyframeEvents()
            self.loadExistingKeyframe()

    def clearAllKeyframeEvents(self):
        firstGroupIdx = None
        parameterGroupIdx = None
        for event in self.eventWidgets:
            if firstGroupIdx is None:
                firstGroupIdx = event.ui.groupComboBox.currentIndex()
            try:
                event.confirmRemoveAudioWidget(forceRemoval=True)
            except RuntimeError:
                pass
        for parameter in self.parameterWidgets:
            try:
                parameterGroupIdx = parameter.confirmRemoveAudioWidget(forceRemoval=True)
            except RuntimeError:
                pass
        for state in self.stateWidgets:
            try:
                state.confirmRemoveAudioWidget(forceRemoval=True)
            except RuntimeError:
                pass
        for switch in self.switchWidgets:
            try:
                switch.confirmRemoveAudioWidget(forceRemoval=True)
            except RuntimeError:
                pass
        self.eventWidgets = []
        self.parameterWidgets = []
        self.stateWidgets = []
        self.switchWidgets = []
        return firstGroupIdx, parameterGroupIdx

    def balanceEventProbs(self, removed=None):
        eventProbs = []
        for eventWidget in self.eventWidgets:
            if eventWidget.included and eventWidget.ui.probability.text():
                eventProbs.append(int(round(float(eventWidget.ui.probability.text()))))

        if not removed:
            # assume that an event was just added to the end of the list
            prevEventProbs = eventProbs[:-1]
        else:
            prevEventProbs = eventProbs[:]
        if not prevEventProbs:
            return

        totalPrevEventProbs = sum(prevEventProbs)
        maxTotalProb = NUMERICAL_EVENT_ATTR_VALUES[PROB_ATTR]["max"]
        if totalPrevEventProbs > maxTotalProb:
            # If the existing events have a total probability that exceeds 100, then
            # do nothing and let the user resolve all probabilities.
            newEventProb = None
        elif not removed and totalPrevEventProbs < (maxTotalProb-1):
            # If the existing events have a total probability less than 100, then the
            # new event should be given a probability to bring that total to 100.
            if removed:
                prevEventProbs.remove(removed)
                totalPrevEventProbs = sum(prevEventProbs)
            newEventProb = maxTotalProb - totalPrevEventProbs
            eventWidget = self.eventWidgets[-1]
            eventWidget.ui.probability.clear()
            eventWidget.ui.probability.insert(str(newEventProb))
        elif totalPrevEventProbs in [maxTotalProb, (maxTotalProb-1)]:
            # If the existing events have a total probability equal to 100, then:
            #     rebalance all the probabilities, including the new event,
            #     if all existing events have equal probability
            #         OR
            #     do nothing and let the user resolve all probabilities if
            #     all existing events do NOT have equal probability
            numEvents = len(eventProbs)
            if removed:
                numEvents -= 1
            if numEvents and prevEventProbs.count(prevEventProbs[0]) == len(prevEventProbs):
                # all existing events have equal probability
                newEventProb = int( float(maxTotalProb) / numEvents )
                for eventWidget in self.eventWidgets:
                    eventWidget.ui.probability.clear()
                    eventWidget.ui.probability.insert(str(newEventProb))

    def addEventToKeyframe(self, updateEventTotals=True, groupIdx=None):
        event = AudioEventWithProbability(self.scrollWidget, EVENTS_UI_FILE,
                                          self.audioEventsByGroup,
                                          self.removedAction, self.actionUpdated)
        if groupIdx is None and len(self.eventWidgets) > 0:
            groupIdx = self.eventWidgets[-1].ui.groupComboBox.currentIndex()
        if groupIdx is not None:
            event.ui.groupComboBox.setCurrentIndex(groupIdx)
            event.doGroupChanged()
        self.eventWidgets.append(event)
        self.actionWidgets.append(event)
        self.scrollLayout.addWidget(event.ui)
        if updateEventTotals:
            eventProbs = [ int(round(float(eventWidget.ui.probability.text()))) for eventWidget in self.eventWidgets if eventWidget.ui.probability.text() ]
            prevEventProbs = eventProbs[:-1]
            self.balanceEventProbs()
        event.ui.setMinimumSize(EVENT_WIDGET_MIN_SIZE[0], EVENT_WIDGET_MIN_SIZE[1])
        event.ui.show()
        if updateEventTotals:
            self._updateActionTotals()

    def addParameterToKeyframe(self, groupIdx=None):
        parameter = AudioParameter(self.scrollWidget, PARAMETER_UI_FILE, self.groupedParameterNames,
                                   self.removedAction, self.actionUpdated)
        if groupIdx is None and len(self.parameterWidgets) > 0:
            groupIdx = self.parameterWidgets[-1].ui.groupComboBox.currentIndex()
        if groupIdx is not None:
            parameter.ui.groupComboBox.setCurrentIndex(groupIdx)
            parameter.doGroupChanged()
        self.parameterWidgets.append(parameter)
        self.scrollLayout.addWidget(parameter.ui)
        parameter.ui.setMinimumSize(PARAMETER_WIDGET_MIN_SIZE[0], PARAMETER_WIDGET_MIN_SIZE[1])
        parameter.ui.show()
        self.actionWidgets.append(parameter)
        self._updateActionTotals()

    def addStateToKeyframe(self, uiFile, audioIds, subAudioIds):
        widgets = []
        state = AudioState(self.scrollWidget, uiFile, audioIds, subAudioIds,
                           self.removedAction, self.actionUpdated)
        self.scrollLayout.addWidget(state.ui)
        state.ui.setMinimumSize(STATE_WIDGET_MIN_SIZE[0], STATE_WIDGET_MIN_SIZE[1])
        state.ui.show()
        self.actionWidgets.append(state)
        if uiFile == STATES_UI_FILE:
            self.stateWidgets.append(state)
        elif uiFile == SWITCH_UI_FILE:
            self.switchWidgets.append(state)
        self._updateActionTotals()
        return state

    def _manageSetButton(self, actionCount, eventCount, totalProb):
        if actionCount > 0 and actionCount != eventCount:
            enabled = True
        elif actionCount == eventCount:
            maxTotalProb = NUMERICAL_EVENT_ATTR_VALUES[PROB_ATTR]["max"]
            if eventCount < 1 or totalProb == 0 or totalProb > maxTotalProb:
                enabled = False
            else:
                enabled = True
        self.setBtn.setEnabled(enabled)
        return enabled

    def _updateActionTotals(self):
        eventCount = 0
        totalProb = 0
        for eventWidget in self.eventWidgets:
            if eventWidget.included:
                eventCount += 1
                try:
                    totalProb += float(eventWidget.ui.probability.text())
                except ValueError:
                    totalProb = 0
                    break
        totalProb = int(math.ceil(totalProb))

        if self.getEventKeyframeData() == getEventKeyframe(self.allAudioEvents):
            # the current settings in the UI match the currently set keyframe
            inverseCountColors = False
        else:
            inverseCountColors = True
        self.headerWidget.updateEventTotals(eventCount, totalProb, inverseCountColors)

        actionCount = 0
        for widget in self.actionWidgets:
            if widget.included:
                actionCount += 1
        self.headerWidget.updateTotals(actionCount)
        self._manageSetButton(actionCount, eventCount, totalProb)

        return (actionCount, eventCount, totalProb)

    # [???] why not remove the passed event from the eventWidgets
    # on removedEvent? then won't need to check if included
    def removedAction(self, action):
        actionCount, eventCount, totalProb = self._updateActionTotals()

    def actionUpdated(self):
        actionCount, eventCount, totalProb = self._updateActionTotals()

    def getEventData(self, eventWidget):
        keyframeDataDict = {}
        for attr in ALL_ATTRS:
            try:
                uiAttr = eval("eventWidget.ui.%s" % attr)
            except AttributeError, e:
                # this attribute must come from a different widget
                continue
            if hasattr(uiAttr, "checkState"):
                uiValue = uiAttr.checkState()
            elif hasattr(uiAttr, "currentText"):
                uiValue = uiAttr.currentText()
            elif hasattr(uiAttr, "text"):
                uiValue = uiAttr.text()
            keyframeDataDict[attr] = uiValue
        for key, value in keyframeDataDict.items():
            if key in NUMERICAL_ATTRS and value:
                if key in INT_ATTRS:
                    keyframeDataDict[key] = int(round(float(value)))
                elif key in FLOAT_ATTRS:
                    keyframeDataDict[key] = float(value)
            elif value == Qt.CheckState.Unchecked:
                keyframeDataDict[key] = False
            elif value == Qt.CheckState.Checked:
                keyframeDataDict[key] = True
            elif isinstance(value, unicode):
                keyframeDataDict[key] = str(keyframeDataDict[key])
            elif not value:
                raise ValueError("No value provided for %s" % key)
        #pprint.pprint(keyframeDataDict)
        return keyframeDataDict

    def getEventKeyframeData(self):
        keyframeData = self.getEventData(self.headerWidget)
        for eventWidget in self.eventWidgets:
            if not eventWidget.included:
                continue
            eventData = self.getEventData(eventWidget)
            for key, val in eventData.items():
                if key not in keyframeData:
                    keyframeData[key] = []
                keyframeData[key].append(val)
        #pprint.pprint(keyframeData)
        return keyframeData

    def getParameterKeyframeData(self, widgets):
        keyframeData = {}
        for parameterWidget in widgets:
            if not parameterWidget.included:
                continue
            parameterData = self.getEventData(parameterWidget)
            for key, val in parameterData.items():
                if key not in keyframeData:
                    keyframeData[key] = []
                keyframeData[key].append(val)
        return keyframeData

    def doSetKeyframe(self):
        # self.headerWidget.ui.volume.editingFinished.emit()
        actionCount, eventCount, totalProb = self._updateActionTotals()
        if not self.setBtn.isEnabled():
            # The button is disabled if there are no events or total probability is too low/high
            return None

        eventKeyframeData = self.getEventKeyframeData()
        if eventKeyframeData:
            setAudioEventKeyframe(eventKeyframeData, self.allAudioEvents)
            normalPalette = QPalette()
            for eventWidget in self.eventWidgets:
                updateWidgetPalette(eventWidget.ui.probability, normalPalette)
                updateWidgetPalette(eventWidget.ui.volume, normalPalette)
            actionCount, eventCount, totalProb = self._updateActionTotals()
        else:
            removeAudioKeys(actionAttrs=[AUDIO_ENUM_ATTR, VOLUME_ATTR, PROB_ATTR])

        parameterKeyframeData = self.getParameterKeyframeData(self.parameterWidgets)
        if parameterKeyframeData:
            setAudioParameterKeyframe(parameterKeyframeData,
                                      {EVENT_NAME_ATTR:self.audioParameterIds, CURVE_ATTR:CURVE_TYPES},
                                      PARAMETER_UI_ATTR_NAME_DICT)
        else:
            removeAudioKeys(actionAttrs=[PARAMETER_NAME_ATTR, VALUE_ATTR, CURVE_ATTR, TIME_MS_ATTR])

        self.addStateKeyframe(widgets=self.stateWidgets,
                              subAudioStateIds=self.subAudioStateIds,
                              groupIds=self.audioStateIds)

        self.addStateKeyframe(widgets=self.switchWidgets,
                              subAudioStateIds=self.subAudioSwitchIds,
                              groupIds=self.audioSwitchIds,
                              actionAttrs=[SWITCH_ID_ATTR, SWITCH_GROUP_ID_ATTR],
                              displayedAttrNames=SWITCH_UI_ATTR_NAME_DICT)

        # Emit a signal to indicate that an audio keyframe has been updated
        audio_keyframe_updated.broadcast()

        # Run the MEL command that keeps Wwise plugin in sync with latest keyframes
        syncWwisePlugin()

    def addStateKeyframe(self, widgets, subAudioStateIds, groupIds,
                         actionAttrs=[STATE_ID_ATTR, STATE_GROUP_ID_ATTR], displayedAttrNames={}):
        stateKeyframeData = self.getParameterKeyframeData(widgets)
        allSubIds = {}
        if stateKeyframeData:
            for subStateDict in subAudioStateIds.values():
                if self.isCorrectStateDict(subStateDict):
                    allSubIds.update(subStateDict)
            setAudioParameterKeyframe(stateKeyframeData,
                                      {STATE_ID_ATTR:allSubIds, STATE_GROUP_ID_ATTR:groupIds},
                                      displayedAttrNames)
        else:
            removeAudioKeys(actionAttrs=actionAttrs)

    def isCorrectStateDict(self, subStateDict):
        for val in subStateDict.values():
            if not isinstance(val, int):
                return False
        return True

    def doDone(self):
        self.close()

    def doDelete(self):
        removeAudioKeys(actionAttrs=[AUDIO_ENUM_ATTR, VOLUME_ATTR, PROB_ATTR, ALT_SOUNDS_ATTR])
        removeAudioKeys(actionAttrs=[PARAMETER_NAME_ATTR, VALUE_ATTR, CURVE_ATTR, TIME_MS_ATTR])
        removeAudioKeys(actionAttrs=[STATE_ID_ATTR, STATE_GROUP_ID_ATTR])
        removeAudioKeys(actionAttrs=[SWITCH_ID_ATTR, SWITCH_GROUP_ID_ATTR])
        self.refreshUI()

        # Emit a signal to indicate that an audio keyframe has been updated
        audio_keyframe_updated.broadcast()

        # Run the MEL command that keeps Wwise plugin in sync with latest keyframes
        syncWwisePlugin()

    def _updateUiSettings(self, uiAttr, value):
        if hasattr(uiAttr, "setChecked"):
            uiAttr.setChecked(value)
        elif hasattr(uiAttr, "setCurrentIndex"):
            idx = uiAttr.findText(str(value))
            uiAttr.setCurrentIndex(idx)
        elif hasattr(uiAttr, "insert"):
            uiAttr.clear()
            uiAttr.insert(str(value))

    def fillEventWidgets(self, eventWidgets, keyframeData, eventNameAttr=PARAMETER_NAME_ATTR):
        filled = []
        for idx in range(len(eventWidgets)):
            eventWidget = eventWidgets[idx]
            for group, events in self.audioEventsByGroup.items():
                if keyframeData[eventNameAttr][idx] in events:
                    groupIdx = eventWidget.ui.groupComboBox.findText(group)
                    eventWidget.ui.groupComboBox.setCurrentIndex(groupIdx)
                    eventWidget.doGroupChanged()
                    break
            if PROB_ATTR not in keyframeData or VOLUME_ATTR not in keyframeData:
                # Shows the user that the existing keyframe is missing probability and/or volume settings
                inversedPalette = getInversedPalette()
                if PROB_ATTR not in keyframeData:
                    for eventWidget in eventWidgets:
                        updateWidgetPalette(eventWidget.ui.probability, inversedPalette)
                if VOLUME_ATTR not in keyframeData:
                    for eventWidget in eventWidgets:
                        updateWidgetPalette(eventWidget.ui.volume, inversedPalette)
            for attr, value in keyframeData.items():
                try:
                    uiAttr = eval("eventWidget.ui.%s" % attr)
                except AttributeError, e:
                    uiAttr = eval("self.headerWidget.ui.%s" % attr)
                if uiAttr in filled:
                    continue
                if isinstance(value, list):
                    try:
                        self._updateUiSettings(uiAttr, value[idx])
                    except IndexError:
                        # We previously used a single volume for all audio events in a keyframe.
                        # That has changed, but we need this for backwards compatibility.
                        self._updateUiSettings(uiAttr, value[0])
                else:
                    self._updateUiSettings(uiAttr, value)
                filled.append(uiAttr)
        self._updateActionTotals()

    def fillAudioWidgets(self, widgets, keyframeData, orderedAttrs):
        # orderedAttrs so that group gets populated before the action name
        for i in range(len(widgets)):
            widget = widgets[i]
            for attr in orderedAttrs:
                if attr not in keyframeData.keys():
                    # wrong orderedAttrs
                    return
                values = keyframeData[attr]
                if len(keyframeData[attr]) != len(widgets):
                    # wrong number of values and widgets
                    return
                try:
                    uiAttr = eval("widget.ui.%s" % attr)
                except StandardError:
                    # failed to eval the specified widget ui attr
                    continue
                self._updateUiSettings(uiAttr, values[i])
                if attr in GROUP_ATTRS:
                    widget.doGroupChanged()

    def loadExistingKeyframe(self, eventNameAttr=EVENT_NAME_ATTR):
        """
        If an audio event keyframe is already set on the current frame,
        we should load that data into the UI.
        """
        eventKeyframeData = getEventKeyframe(self.allAudioEvents)
        #pprint.pprint(eventKeyframeData)
        if eventKeyframeData:
            numEvents = len(eventKeyframeData[eventNameAttr])
            while len(self.eventWidgets) < numEvents:
                self.addEventToKeyframe(updateEventTotals=False)
            self.fillEventWidgets(self.eventWidgets, eventKeyframeData, eventNameAttr)

        parameterKeyframeData = getAudioKeyframe(displayedActionAttrs=DISPLAYED_PARAMETER_ATTRS)
        if parameterKeyframeData:
            for i in range(len(parameterKeyframeData.values()[0])):
                self.addParameterToKeyframe()
            self.fillAudioWidgets(self.parameterWidgets, parameterKeyframeData, PARAMETER_UI_ATTRS)

        stateKeyframeData = getAudioKeyframe(displayedActionAttrs=DISPLAYED_STATE_ATTRS)
        if stateKeyframeData:
            for i in range(len(stateKeyframeData.values()[0])):
                self.addStateToKeyframe(STATES_UI_FILE, self.audioStateIds, self.subAudioStateIds)
            self.fillAudioWidgets(self.stateWidgets, stateKeyframeData, STATE_UI_ATTRS)

        switchKeyframeData = getAudioKeyframe(displayedActionAttrs=DISPLAYED_SWITCH_ATTRS)
        if switchKeyframeData:
            for i in range(len(switchKeyframeData.values()[0])):
                self.addStateToKeyframe(SWITCH_UI_FILE, self.audioSwitchIds, self.subAudioSwitchIds)
            self.fillAudioWidgets(self.switchWidgets, switchKeyframeData, STATE_UI_ATTRS)

        return eventKeyframeData, parameterKeyframeData, stateKeyframeData, switchKeyframeData


class ToolHeader(QWidget):
    def __init__(self, parent, *args, **kwargs):
        super(ToolHeader,self).__init__(*args, **kwargs)
        self.setParent(parent)
        currentDir = os.path.dirname(__file__)
        self.headerUiFile = QFile(os.path.join(currentDir, HEADER_UI_FILE))
        self.initUI()

    def initUI(self):
        # Load UI config from HEADER_UI_FILE
        loader = QUiLoader()
        self.headerUiFile.open(QFile.ReadOnly)
        self.ui = loader.load(self.headerUiFile, parentWidget=self.parent())
        self.headerUiFile.close()

        # Users cannot update eventCount or total probability fields
        self.ui.eventCount.setReadOnly(True)
        self.ui.totalProb.setReadOnly(True)
        self.ui.actionCount.setReadOnly(True)

    def updateEventTotals(self, eventCount, prob, inverseCountColors=False):
        if inverseCountColors:
            countPalette = getInversedPalette()
        else:
            countPalette = QPalette()
        updateWidgetPalette(self.ui.eventCount, countPalette, eventCount)
        maxTotalProb = NUMERICAL_EVENT_ATTR_VALUES[PROB_ATTR]["max"]
        if prob == 0 or prob > maxTotalProb:
            color = Qt.red
        else:
            color = Qt.green
        probPalette = QPalette()
        probPalette.setColor(QPalette.Text, color)
        updateWidgetPalette(self.ui.totalProb, probPalette, prob)

    def updateTotals(self, actionCount=0):
        self.ui.actionCount.clear()
        self.ui.actionCount.insert(str(actionCount))


class AudioWidget(QWidget):
    def __init__(self, parent, uiFile, removeCallback, updateCallback, *args, **kwargs):
        super(AudioWidget,self).__init__(*args, **kwargs)
        self.setParent(parent)
        self.removeCallback = removeCallback
        self.updateCallback = updateCallback
        self.included = True
        currentDir = os.path.dirname(__file__)
        self.uiFile = QFile(os.path.join(currentDir, uiFile))
        self.initUI()

    def initUI(self):
        # Load UI config from ui file
        loader = QUiLoader()
        self.uiFile.open(QFile.ReadOnly)
        self.ui = loader.load(self.uiFile, parentWidget=self.parent())
        self.uiFile.close()

        # Add pair of checkboxes to allow removal of this event
        self.ui.removeAudioWidgetComboBox.stateChanged.connect(lambda: self.removeAudioWidget())
        self.removeAudioWidget()
        self.ui.confirmComboBox.stateChanged.connect(self.confirmRemoveAudioWidget)
        self.confirmRemoveAudioWidget()

    def removeAudioWidget(self):
        if self.ui.removeAudioWidgetComboBox.checkState():
            self.ui.confirmLabel.setEnabled(True)
            self.ui.confirmComboBox.setEnabled(True)
        else:
            self.ui.confirmLabel.setEnabled(False)
            self.ui.confirmComboBox.setEnabled(False)

    def confirmRemoveAudioWidget(self, forceRemoval=False):
        if self.ui.confirmComboBox.checkState() or forceRemoval:
            self.included = False
            self.removeCallback(self)
            self.ui.setParent(None)
            self.setParent(None)
            self.ui.hide()
            self.hide()


class AudioState(AudioWidget):
    """
    Used for both switches and states, since they have the same structure
    """
    def __init__(self, parent, uiFile, audioStates, subStateIds, removeCallback, updateCallback,
                 *args, **kwargs):
        self.audioStateGrps = copy.deepcopy(audioStates)
        self.allStateIds = copy.deepcopy(subStateIds)
        super(AudioState,self).__init__(parent, uiFile, removeCallback,
                                        updateCallback, *args, **kwargs)

        groups = self.audioStateGrps.keys()
        groups.sort()
        for group in groups:
            self.ui.stateGroupId.addItem(group)

        self.ui.stateGroupId.activated.connect(self.doGroupChanged)
        self.doGroupChanged()

    def doGroupChanged(self):
        # The group pulldown list is connected to the audio event pulldown
        # list so the latter only lists audio events in the selected group.
        self.ui.stateName.clear()
        group = self.ui.stateGroupId.currentText()
        if self.audioStateGrps and group in self.audioStateGrps.keys():
            for state in self.allStateIds[group]:
                self.ui.stateName.addItem(state)
        self.updateCallback()


class AudioWidgetWithGroupSearch(AudioWidget):
    """
    Keeps functionality for filtering the names and checking for the changed groups
    """
    def __init__(self, parent, uiFile, audioNamesByGroup, removeCallback,
                 updateCallback, *args, **kwargs):
        self.audioNamesByGroup = audioNamesByGroup
        super(AudioWidgetWithGroupSearch,self).__init__(parent, uiFile, removeCallback,
                                                        updateCallback, *args, **kwargs)

    def initUI(self):
        super(AudioWidgetWithGroupSearch,self).initUI()
        # Add groups and audio actions to the pulldown menus
        groups = self.audioNamesByGroup.keys()
        groups.sort()
        for group in groups:
            self.ui.groupComboBox.addItem(group)
        self.ui.groupComboBox.activated.connect(self.doGroupChanged)
        self.doGroupChanged()
        self.ui.audioName.activated.connect(self.doNameChanged)

        # The audio event list should be filtered by user input
        self.ui.audioSearch.textChanged.connect(self.filterNames)

    def filterNames(self):
        filter = self.ui.audioSearch.text()
        filter = filter.lower()
        group = self.ui.groupComboBox.currentText()
        self.ui.audioName.clear()
        for event in self.audioNamesByGroup[group]:
            if filter in event.lower():
                self.ui.audioName.addItem(event)

    def doGroupChanged(self):
        # The group pulldown list is connected to the audio event pulldown
        # list so the latter only lists audio events in the selected group.
        self.ui.audioSearch.clear()
        self.ui.audioName.clear()
        group = self.ui.groupComboBox.currentText()
        if self.audioNamesByGroup and group in self.audioNamesByGroup:
            for event in self.audioNamesByGroup[group]:
                self.ui.audioName.addItem(event)
        self.updateCallback()

    def doNameChanged(self):
        self.updateCallback()


class AudioWidgetWithGroupDoubleSearch(AudioWidgetWithGroupSearch):
    """
    This is the same as AudioWidgetWithGroupSearch but with two
    user input search fields to filter the audio event list.
    """
    def initUI(self):
        super(AudioWidgetWithGroupDoubleSearch,self).initUI()
        self.ui.audioSearchTwo.textChanged.connect(self.filterNames)

    def filterNames(self):
        filter = self.ui.audioSearch.text()
        filter = filter.lower()
        filterTwo = self.ui.audioSearchTwo.text()
        filterTwo = filterTwo.lower()
        group = self.ui.groupComboBox.currentText()
        self.ui.audioName.clear()
        for event in self.audioNamesByGroup[group]:
            lowercaseEvent = event.lower()
            if filter in lowercaseEvent and filterTwo in lowercaseEvent:
                self.ui.audioName.addItem(event)

    def doGroupChanged(self):
        self.ui.audioSearchTwo.clear()
        super(AudioWidgetWithGroupDoubleSearch,self).doGroupChanged()


class AudioEventWithProbability(AudioWidgetWithGroupDoubleSearch):
    def initUI(self):
        super(AudioEventWithProbability,self).initUI()

        # Display the audio event names and probability in bold
        boldFont = QFont()
        boldFont.setBold(True)
        self.ui.audioName.setFont(boldFont)
        self.ui.probability.setFont(boldFont)
        self.ui.volume.setFont(boldFont)

        # Set default value for probability
        self.ui.probability.insert(str(NUMERICAL_EVENT_ATTR_VALUES[PROB_ATTR]["default"]))

        # Set default value for volume
        self.ui.volume.insert(str(NUMERICAL_EVENT_ATTR_VALUES[VOLUME_ATTR]["default"]))

        # The valid range for volume values should be enforced by the UI
        self.ui.volume.editingFinished.connect(self.setVolume)

        # The valid range for probability values should be enforced by the UI
        self.ui.probability.editingFinished.connect(self.setProbVal)
        self.ui.probability.editingFinished.connect(self.updateCallback)

        self.ui.audioPlay.setIcon(self.ui.audioPlay.style().standardIcon(QStyle.SP_MediaPlay))
        self.ui.audioPlay.clicked.connect(self.playAudioEvent)

    def playAudioEvent(self):
        audioEvent = self.ui.audioName.currentText()
        #print("Trying to play '%s' audio event..." % audioEvent)
        playAudioEvent(audioEvent)

    def setProbVal(self, min=NUMERICAL_EVENT_ATTR_VALUES[PROB_ATTR]["min"],
                   max=NUMERICAL_EVENT_ATTR_VALUES[PROB_ATTR]["max"]):
        probVal = self.ui.probability.text()
        try:
            probVal = int(round(float(probVal)))
        except ValueError:
            return None
        if probVal < min:
            self.ui.probability.setText(str(min))
        elif probVal > max:
            self.ui.probability.setText(str(max))

    def setVolume(self, min=NUMERICAL_EVENT_ATTR_VALUES[VOLUME_ATTR]["min"],
                  max=NUMERICAL_EVENT_ATTR_VALUES[VOLUME_ATTR]["max"]):
        volume = self.ui.volume.text()
        try:
            volume = int(volume)
        except ValueError:
            return None
        if volume < min:
            self.ui.volume.setText(str(min))
        elif volume > max:
            self.ui.volume.setText(str(max))
        self.updateCallback()

    def doEventChanged(self):
        self.updateCallback()

    def confirmRemoveAudioWidget(self, forceRemoval=False):
        if self.ui.confirmComboBox.checkState() or forceRemoval:
            removedProb = self.ui.probability.text()
            if removedProb:
                removedProb = int(round(float(removedProb)))
            try:
                self.parent().parent().parent().parent().balanceEventProbs(removedProb)
            except AttributeError:
                pass
            self.ui.probability.clear()
        super(AudioEventWithProbability,self).confirmRemoveAudioWidget(forceRemoval)


class AudioParameter(AudioWidgetWithGroupSearch):
    """
    Similar to event, but has an option for value and interpolation
    """
    def __init__(self, parent, uiFile, audioParametersByGroup, removeCallback, updateCallback,
                 *args, **kwargs):
        self.audioParametersByGroup = audioParametersByGroup
        super(AudioParameter,self).__init__(parent, uiFile, audioParametersByGroup, removeCallback,
                                            updateCallback, *args, **kwargs)

    def initUI(self):
        super(AudioParameter,self).initUI()
        self.populateCurves()

    def populateCurves(self):
        for curve in CURVE_TYPES.keys():
            self.ui.curveType.addItem(curve)


def main():
    ui = SetAudioTrigger()
    ui.show()
    return ui


if __name__ == '__main__':
    main()


