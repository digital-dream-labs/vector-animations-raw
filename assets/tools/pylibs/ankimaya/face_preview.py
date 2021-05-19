

# The following time to sleep between each displayed image is a rough
# estimate to help achieve close to 30 frames-per-second.
# TODO: Measure times to get more precise values for these times.
SLEEP_TIME_BETWEEN_DISPLAY_SEC = 0.03

INVALID_FRAME_RANGE_MSG = "Invalid frame range provided"

TOOLS_DIR_ENV_VAR = "ANKI_TOOLS"

PYTHON3_INTERPRETER = "/usr/local/bin/python3"

WIN_TITLE = "Face Preview"

SETTINGS_UI_FILE = "face_preview_settings.ui"
DISPLAY_UI_FILE = "face_preview_display.ui"
SAVE_UI_FILE = "face_preview_save.ui"

CLIP_NAME_KEY = "clip_name"
CLIP_START_KEY = "clip_start"
CLIP_END_KEY = "clip_end"

TRIGGER_TIME_KEY = "triggerTime_ms"


# This will allow us to assign hotkeys to buttons.
_globalPreviewUI = None


import sys
import os
import copy
import subprocess
import time
import tempfile
import glob
import math
from operator import itemgetter

from maya import cmds
from maya import OpenMayaUI as omui
from maya import OpenMayaAnim as oma

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

from ankimaya.constants import DATA_NODE_NAME
from ankimaya.export_for_robot import FLOAT_EQUALITY_TOLERANCE
from ankimaya import game_exporter, anim_data_manager, robot_data
from ankibasestation import face_images
from ankimaya.interpolation_manager import find_value_for_frame


mayaMainWindowPtr = omui.MQtUtil.mainWindow()
mayaMainWindow = wrapInstance(long(mayaMainWindowPtr), QWidget)


def get_tools_dir():
    tools_dir = os.getenv(TOOLS_DIR_ENV_VAR)
    if not tools_dir:
        err_msg = "Failed to query the '%s' environment variable" % TOOLS_DIR_ENV_VAR
        cmds.warning(err_msg)
    return tools_dir


def run_command_core(cmd, stdout_pipe, stderr_pipe, shell):
    #print("Running: %s" % cmd)
    try:
        p = subprocess.Popen(cmd.split(), stdout=stdout_pipe, stderr=stderr_pipe, shell=shell)
    except OSError as err:
        cmds.warning("Failed to execute '%s' because: %s" % (cmd, err))
        return (None, None, None)
    (stdout, stderr) = p.communicate()
    status = p.poll()
    return (status, stdout, stderr)


def run_command_wrapper(cmd, tools_dir=None, shell=False):
    display_msg = ""
    if not tools_dir:
        tools_dir = get_tools_dir()
    if tools_dir and not cmd.startswith(os.sep):
        cmd = os.path.join(tools_dir, cmd)
    status, stdout, stderr = run_command(cmd, run_with_py3=True, shell=shell)
    if status != 0:
        if stderr:
            display_msg = stderr.split(os.linesep)[-1]
        else:
            display_msg = "Failed to execute: %s" % cmd
        cmds.warning(display_msg)
    elif stdout:
        display_msg = stdout.split(os.linesep)[-1]
        print display_msg,
    return (status, stdout, stderr, display_msg)


def run_command(cmd, num_retries=0, display_output=False,
                run_with_py3=False, py3_interpreter=PYTHON3_INTERPRETER,
                shell=False):
    """
    Given a command to run, this function will execute that
    in a subprocess and return (status, stdout, stderr)
    """
    orig_cmd = cmd
    if run_with_py3:
        cmd = py3_interpreter + ' ' + cmd
    if display_output:
        stdout_pipe = None
        stderr_pipe = None
    else:
        stdout_pipe = subprocess.PIPE
        stderr_pipe = subprocess.PIPE
    retry = 0 
    status, stdout, stderr = run_command_core(cmd, stdout_pipe, stderr_pipe, shell)
    while status != 0 and retry < num_retries:
        retry += 1
        time.sleep(retry)
        status, stdout, stderr = run_command_core(cmd, stdout_pipe, stderr_pipe, shell)
    if stdout:
        stdout = stdout.strip()
    if stderr:
        stderr = stderr.strip()
    if status != 0:
        err_msg = "Failed to execute '%s' (exit status = %s) " % (cmd, status)
        if stderr:
            err_msg += os.linesep + stderr
        cmds.warning(err_msg)
    return (status, stdout, stderr)


def getAnimClip(frameNum):
    """
    Return clip info for the animation clip that this frame is a part of
    """
    clipInfo = game_exporter.get_clip_info('', include_all=True, include_face_keyframes=False)[2]
    for animClip in clipInfo:
        if frameNum >= animClip[CLIP_START_KEY] and frameNum <= animClip[CLIP_END_KEY]:
            #print("Frame %s is in '%s' animation clip" % (frameNum, animClip[CLIP_NAME_KEY]))
            return animClip
    else:
        return None


def selectKeyframesUsingFrameNum(frameNum, keyframeBefore, keyframeAfter, timeKey=TRIGGER_TIME_KEY):
    # IMPORTANT: keyframeBefore and keyframeAfter should not
    #            both be None and callers should enforce that.
    keyframes = None
    if keyframeBefore is None and keyframeAfter is not None:
        # use keyframeAfter with no interpolation
        keyframes = { int(frameNum) : keyframeAfter }
    elif keyframeAfter is None or frameNum == keyframeBefore[timeKey]:
        # use keyframeBefore with no interpolation
        keyframes = { int(frameNum) : keyframeBefore }
    elif keyframeBefore == keyframeAfter or frameNum == keyframeAfter[timeKey]:
        # use keyframeAfter with no interpolation
        keyframes = { int(frameNum) : keyframeAfter }
    elif frameNum > keyframeBefore[timeKey] and frameNum < keyframeAfter[timeKey]:
        # use keyframeBefore and keyframeAfter to get interpolated face
        keyframes = { int(keyframeBefore[timeKey]) : keyframeBefore,
                      int(keyframeAfter[timeKey]) : keyframeAfter }
    else:
        raise ValueError("Frame %s does not lie between %s and %s" % (frameNum,
                         keyframeBefore[timeKey], keyframeAfter[timeKey]))
    return keyframes


class FacePreview(QWidget):
    def __init__(self, *args, **kwargs):
        super(FacePreview,self).__init__(*args, **kwargs)
        self.setParent(mayaMainWindow)
        self.setWindowFlags(Qt.Window)
        self.resetCache()
        self.animWidgets = []
        self.settingsWidget = None
        self.displayWidget = None
        self.saveWidget = None
        self.gridCount = 0
        self.scroll = None
        self.scrollWidget = None
        self.scrollLayout = None
        self.vbox = None
        self.widget = None
        self.installEventFilter(self)
        self.initUI()

        # Show the face image for the current frame when this tool is launched
        # and then immediately reset the facial keyframe cache since the tool is
        # NOT automatically given the mouse focus when launched (meaning that
        # facial keyframes could be changed after the tool is launched but
        # before the first click of one of its buttons).
        self.displayWidget.reset()
        self.resetCache()

    def _addWidgetToGrid(self, widget, column=0, lastInRow=True):
        self.grid.addWidget(widget, self.gridCount, column)
        if lastInRow:
            self.gridCount += 1

    def resetCache(self):
        self._keyframeCache = {}

    def eventFilter(self, obj, event):
        """
        Event filter to clear the cache of procedural face keyframes
        if focus is shifted away from the Face Preview window.
        """
        if event.type() == QEvent.Type.Leave and obj is self:
            self.resetCache()
        return super(FacePreview, self).eventFilter(obj, event)

    def closeEvent(self, e):
        """
        Remove the event filter
        """
        self.removeEventFilter(self)
        self.resetCache()
        return super(FacePreview, self).closeEvent(e)

    def initUI(self):

        self.setGeometry(100, 100, 470, 350)
        self.setWindowTitle(WIN_TITLE)

        # At the top layer, a grid layout is used to hold buttons and widgets
        self.grid = QGridLayout(self)

        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
        # TODO: Can we use the following instead of forcing the window to always stay on top?
        #self.setProperty("saveWindowPref", True)
        # Along with that setProperty() call, we may need to call setObjectName() to give it a name.

        self.show()
        self.setLayout(self.grid)

        self.addSettingsWidget()

        # The display widget uses data from the settings widget (frame range start/end).
        self.addDisplayWidget(self.settingsWidget)

        # The save widget uses data from the settings widget (frame range start/end) and uses
        # the display widget to save on-screen image and/or display saved image file(s).
        self.addSaveWidget(self.settingsWidget, self.displayWidget)

        self.addBottomButtons()

    def getAllProcFaceKeyframes(self, clipStart, clipEnd, dataNodeName=DATA_NODE_NAME):

        # TODO: Change this to check if the window has focus
        if False and not self.hasFocus():# and not self.displayWidget, self.settingsWidget or self.saveWidget has focus
            print("%s window does NOT have focus" % self)
            # Don't use the cache if the Face Preview window doesn't have the mouse focus, eg. if
            # it is being used via hotkeys, since the user could be updating eye/face keyframes.
            return self._getAllProcFaceKeyframes(clipStart, clipEnd, dataNodeName)

        cacheKey = (clipStart, clipEnd, dataNodeName)
        if cacheKey in self._keyframeCache:
            return self._keyframeCache[cacheKey]
        procFaceKeyframes = self._getAllProcFaceKeyframes(clipStart, clipEnd, dataNodeName)
        self._keyframeCache[cacheKey] = procFaceKeyframes
        return procFaceKeyframes

    def _getAllProcFaceKeyframes(self, clipStart, clipEnd, dataNodeName):
        procFaceKeyframes = {}

        adm = anim_data_manager.AnimDataManager(dataNodeName, clipStart, clipEnd,
                                                check_muted=False, full_setup=False)
        animData = adm.get_anim_data(use_absolute_frames=True, face_only=True)
        animData.update(adm.get_muted_anim_data(use_absolute_frames=True, face_only=True))

        # Setup 'frameNums' to be the list of ALL frames that have ANY eye/face attribute keyed...
        frameNums = set()
        for currAttr, frameData in animData.iteritems():
            if not robot_data.is_procedural_face_attr(currAttr):
                continue
            frameNums.update(frameData.keys())
        frameNums = list(frameNums)
        frameNums.sort()

        for currAttr, frameData in animData.iteritems():
            if not robot_data.is_procedural_face_attr(currAttr):
                continue
            for idx in range(len(frameNums)):
                thisFrame = frameNums[idx]
                if idx > 0 and abs(thisFrame - frameNums[idx-1]) <= FLOAT_EQUALITY_TOLERANCE:
                    continue
                try:
                    frameValue = frameData[thisFrame]
                except KeyError:
                    # If the current attribute is not keyed at the current frame number, then
                    # get the interpolated value of that attribute at the current frame...
                    frameValue = find_value_for_frame(thisFrame, frameNums, dataNodeName + '.' + currAttr)
                robot_data.add_procedural_face_keyframe(currAttr, thisFrame, 0, frameValue,
                                                        (clipStart + thisFrame),
                                                        dataNodeName, procFaceKeyframes,
                                                        fill_new_frame_with_interpolated_values=False,
                                                        frame_nums=frameNums)
        return procFaceKeyframes

    def getProcFaceKeyframes(self, frameNum):
        animClip = getAnimClip(frameNum)
        if not animClip:
            raise ValueError("Frame %s is not part of any existing animation clips" % frameNum)
        try:
            procFaceKeyframes = self.getAllProcFaceKeyframes(animClip[CLIP_START_KEY],
                                                             animClip[CLIP_END_KEY])
        except ValueError, e:
            cmds.warning("Failed to query the procedural face keyframes because: %s" % e)
            return (None, None, None)
        lastKeyframe = None

        for triggerTime, keyframe in sorted(procFaceKeyframes.iteritems()):
            if frameNum == triggerTime:
                return (animClip[CLIP_NAME_KEY], keyframe, None)
            elif frameNum < triggerTime:
                return (animClip[CLIP_NAME_KEY], lastKeyframe, keyframe)
            else:
                # frameNum > triggerTime
                lastKeyframe = keyframe

        #raise ValueError("Unable to locate keyframe at frame %s or two keyframes around that" % frameNum)
        return (animClip[CLIP_NAME_KEY], lastKeyframe, None)

    def addBottomButtons(self):
        self.bottomBtns = QGridLayout(self)

        # Add close button to the grid layout
        self.cancelBtn = QPushButton("Done")
        self.cancelBtn.clicked.connect(self.doClose)
        self.bottomBtns.addWidget(self.cancelBtn, 0, 1)

        self.bottomBtnsWidget = QWidget()
        self.bottomBtnsWidget.setLayout(self.bottomBtns)
        self._addWidgetToGrid(self.bottomBtnsWidget)

    def addSettingsWidget(self):
        self.settingsWidget = FacePreviewSettings(self)
        self._addWidgetToGrid(self.settingsWidget.ui)
        self.settingsWidget.ui.setMinimumSize(450, 70)
        self.settingsWidget.ui.show()

    def addDisplayWidget(self, settingsWidget, imageFile=None):
        self.displayWidget = FacePreviewDisplay(self, settingsWidget)
        self._addWidgetToGrid(self.displayWidget.ui)
        self.displayWidget.ui.setMinimumSize(450, 100)
        if imageFile:
            self.displayWidget.ui.displayLabel.setPixmap(QPixmap(imageFile))
        self.displayWidget.ui.show()

    def addSaveWidget(self, settingsWidget, displayWidget):
        self.saveWidget = FacePreviewSave(self, settingsWidget, displayWidget)
        self._addWidgetToGrid(self.saveWidget.ui)
        self.saveWidget.ui.setMinimumSize(450, 70)
        self.saveWidget.ui.show()

    def startFrameChanged(self, newStartFrame=None):
        if newStartFrame is None:
            newStartFrame = self.settingsWidget.ui.startFrame.text()
        self.displayWidget.newMinFrame(newStartFrame)

    def endFrameChanged(self, newEndFrame=None):
        if newEndFrame is None:
            newEndFrame = self.settingsWidget.ui.endFrame.text()
        self.displayWidget.newMaxFrame(newEndFrame)

    def doClose(self):
        self.close()


class FacePreviewSettings(QWidget):
    def __init__(self, parent, *args, **kwargs):
        super(FacePreviewSettings,self).__init__(*args, **kwargs)
        self.setParent(parent)
        currentDir = os.path.dirname(__file__)
        self.preview_ui_file = QFile(os.path.join(currentDir, SETTINGS_UI_FILE))
        self.initUI()

    def initUI(self):
        # Load UI config from SETTINGS_UI_FILE
        loader = QUiLoader()
        self.preview_ui_file.open(QFile.ReadOnly)
        self.ui = loader.load(self.preview_ui_file, parentWidget=self.parent())
        self.preview_ui_file.close()

        self.ui.startFrame.editingFinished.connect(self.startFrameChanged)
        self.ui.endFrame.editingFinished.connect(self.endFrameChanged)

        self.ui.resetFrameRange.clicked.connect(self.resetFrameRange)

        # TODO: Remove the following two lines after we have support for flipping scan lines
        self.ui.flipScanlinesLabel.setEnabled(False)
        self.ui.flipScanlines.setEnabled(False)

        self.resetFrameRange()

    def resetFrameRange(self):
        minValue = oma.MAnimControl.minTime().value()
        maxValue = oma.MAnimControl.maxTime().value()
        self.ui.startFrame.setText(str(int(minValue)))
        self.ui.endFrame.setText(str(int(maxValue)))

    def _frameChanged(self, widget):
        try:
            widgetFrame = str(int(float(widget.text())))
        except ValueError:
            widgetFrame = ''
        else:
            if widgetFrame.startswith('-'):
                # negative numbers are not supported
                widgetFrame = '0'
        widget.setText(widgetFrame)

    def startFrameChanged(self):
        self._frameChanged(self.ui.startFrame)
        self.parent().startFrameChanged()

    def endFrameChanged(self):
        self._frameChanged(self.ui.endFrame)
        self.parent().endFrameChanged()

    def getFrameRange(self, errorMsg=INVALID_FRAME_RANGE_MSG):
        # Query and validate user input for frame range...
        startFrame = self.ui.startFrame.text()
        endFrame = self.ui.endFrame.text()
        if not startFrame or not endFrame:
            cmds.warning(errorMsg)
            return (None, None)
        try:
            startFrame = int(startFrame)
            endFrame = int(endFrame)
        except ValueError:
            cmds.warning(errorMsg)
            return (None, None)
        if startFrame > endFrame:
            cmds.warning(errorMsg)
            return (None, None)
        return (startFrame, endFrame)

    def getClipInfo(self, startFrame, endFrame, errorMsg=INVALID_FRAME_RANGE_MSG):
        # Get list of animation clips and confirm that this frame range conforms to that...
        clipInfo = game_exporter.get_clip_info('', include_all=True, include_face_keyframes=False)[2]
        for animClip in clipInfo:
            clipName = animClip[CLIP_NAME_KEY]
            clipStart = int(animClip[CLIP_START_KEY])
            clipEnd = int(animClip[CLIP_END_KEY])
            clipRange = range(clipStart, clipEnd+1)
            #print("Range of '%s' is %s" % (clipName, clipRange))
            if startFrame in clipRange and endFrame in clipRange:
                return (clipName, clipStart, clipEnd)

        errorMsg += " (%s to %s" % (startFrame, endFrame)
        errorMsg += " does not match any full or partial animation in the Game Exporter)"
        cmds.warning(errorMsg)
        return (None, None, None)


class FacePreviewDisplay(QWidget):

    updateTimeslider = True

    def __init__(self, parent, settingsWidget, *args, **kwargs):
        super(FacePreviewDisplay,self).__init__(*args, **kwargs)
        self.setParent(parent)
        self.settingsWidget = settingsWidget
        self.currentFrame = None
        self.isPlaying = False
        self.abortPlaying = False
        currentDir = os.path.dirname(__file__)
        self.preview_ui_file = QFile(os.path.join(currentDir, DISPLAY_UI_FILE))
        self.initUI()

    def setCurrentFrame(self, frameNum):
        try:
            self.currentFrame = int(frameNum)
        except ValueError:
            self.currentFrame = float(frameNum)
        self.ui.displayFrame.setText(str(frameNum))

    def displayFrameChanged(self):
        currentFrame = self.ui.displayFrame.text()
        if currentFrame in ['', None]:
            self.ui.displayFrame.setText(str(self.currentFrame))
            return None
        try:
            currentFrame = int(currentFrame)
        except ValueError:
            self.ui.displayFrame.setText(str(self.currentFrame))
            return None
        startFrame, endFrame = self.settingsWidget.getFrameRange()
        if startFrame is not None and currentFrame < startFrame:
            currentFrame = startFrame
        elif endFrame is not None and currentFrame > endFrame:
            currentFrame = endFrame
        self.draw(currentFrame)
        self.setCurrentFrame(currentFrame)

    def initUI(self):
        # Load UI config from DISPLAY_UI_FILE
        loader = QUiLoader()
        self.preview_ui_file.open(QFile.ReadOnly)
        self.ui = loader.load(self.preview_ui_file, parentWidget=self.parent())
        self.preview_ui_file.close()

        # Setup the box that shows the frame/file being displayed.
        font = self.ui.displayFrame.font()
        font.setPointSize(16)
        self.ui.displayFrame.setFont(font)
        self.ui.displayFrame.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.ui.displayFrame.editingFinished.connect(self.displayFrameChanged)

        # Connect the buttons
        self.ui.reset.clicked.connect(self.reset)
        self.ui.reset.setIcon(self.ui.reset.style().standardIcon(QStyle.SP_BrowserReload))
        self.ui.play.clicked.connect(self.play)
        self.ui.play.setIcon(self.ui.play.style().standardIcon(QStyle.SP_MediaPlay))
        self.ui.stepBack.clicked.connect(self.stepBack)
        self.ui.stepBack.setIcon(self.ui.stepBack.style().standardIcon(QStyle.SP_MediaSeekBackward))
        self.ui.stepForward.clicked.connect(self.stepForward)
        self.ui.stepForward.setIcon(self.ui.stepForward.style().standardIcon(QStyle.SP_MediaSeekForward))
        self.ui.jumpBack.clicked.connect(self.jumpBack)
        self.ui.jumpBack.setIcon(self.ui.jumpBack.style().standardIcon(QStyle.SP_MediaSkipBackward))
        self.ui.jumpForward.clicked.connect(self.jumpForward)
        self.ui.jumpForward.setIcon(self.ui.jumpForward.style().standardIcon(QStyle.SP_MediaSkipForward))

    def _focusOnButton(self, button):
        if button:
            button.setFocus()
            button.setDefault(True)

    def reset(self):
        frameNum = cmds.currentTime(query=True)
        self.draw(frameNum)
        self._focusOnButton(self.ui.reset)

    def draw(self, frameNum):
        try:
            animName, keyframeBefore, keyframeAfter = self.parent().getProcFaceKeyframes(frameNum)
        except ValueError, e:
            cmds.warning(str(e))
            return None
        if keyframeBefore is None and keyframeAfter is None:
            return None
        keyframes = selectKeyframesUsingFrameNum(frameNum, keyframeBefore, keyframeAfter)
        self._displayImages(keyframes, frameNum, frameNum)

    def play(self):
        # This function may only PLAY the frames indicated in the UI, but it
        # could easily depend on the keyframes lying just outside that frame
        # range, so we currently get all keyframes in the anim clip and then
        # display the frame range of interest.

        if self.isPlaying:
            # If play() is called while already playing, then abort that
            # playback (providing play/pause functionality).
            self.abortPlaying = True
            return None

        startFrame, endFrame = self.settingsWidget.getFrameRange()
        if startFrame is None or endFrame is None:
            return None
        clipName, clipStart, clipEnd = self.settingsWidget.getClipInfo(startFrame, endFrame)
        if clipStart is None or clipEnd is None:
            return None
        keyframes = self.parent().getAllProcFaceKeyframes(clipStart, clipEnd)

        self._focusOnButton(self.ui.play)

        # Begin playback from current frame, but if the current frame is out of
        # range, then use the starting frame.
        if self.currentFrame < startFrame or self.currentFrame >= endFrame:
            target = startFrame
        else:
            target = self.currentFrame

        # Toggle the local playback settings before/after displaying the images.
        self.isPlaying = True
        self._displayImages(keyframes, target, endFrame, self.abortPlay)
        self.isPlaying = False
        self.abortPlaying = False

    def abortPlay(self):
        return self.abortPlaying

    def _displayImages(self, keyframes, startFrame, endFrame, abortCallback=None):
        startTime = time.time()

        frameRange = face_images.process_face_images(keyframes, startFrame, endFrame,
                                        allow_non_integer_frames=True,
                                        face_image_callback=face_images.draw_images,
                                        abort_callback=abortCallback,
                                        callback_args={"display_label":self.ui.displayLabel,
                                                       "q_app":qApp,
                                                       "sleep_at_end":SLEEP_TIME_BETWEEN_DISPLAY_SEC,
                                                       "frame_time_callback":self.setCurrentFrame})

        endTime = time.time()
        try:
            numImages = frameRange.index(self.currentFrame) - frameRange.index(startFrame) + 1
        except ValueError:
            return None
        if numImages > 1:
            frameRate = numImages / (endTime-startTime)
            print("The %s images were played at an approximate frame rate of %0.2f fps"
                  % (numImages, frameRate))

    def _updateCurrentFrame(self, target, wall, startFrame, endFrame):
        if startFrame is None or endFrame is None:
            # frame range unknown, so just go to target frame and hope for the best
            pass
        elif self.currentFrame < startFrame:
            # can't be before the frame range, so jump forward to the start of that
            target = startFrame
        elif self.currentFrame == wall:
            # already at the wall (start or end of frame range) - no room to move past the wall, so do nothing
            return wall
        elif self.currentFrame > endFrame:
            # can't be past the frame range, so jump back to the end of that
            target = endFrame

        # Go to target frame (which may just be the start or end frame)
        self.draw(target)
        self.setCurrentFrame(target)
        return target

    def stepBack(self):
        startFrame, endFrame = self.settingsWidget.getFrameRange()
        if self.currentFrame is None:
            self.currentFrame = int(cmds.currentTime(query=True))
        target = int(math.ceil(self.currentFrame - 1))
        try:
            result = self._updateCurrentFrame(target, startFrame, startFrame, endFrame)
        except ValueError, e:
            cmds.warning(str(e))
        else:
            if self.updateTimeslider:
                cmds.currentTime(result, edit=True)
        self._focusOnButton(self.ui.stepBack)

    def stepForward(self):
        startFrame, endFrame = self.settingsWidget.getFrameRange()
        if self.currentFrame is None:
            self.currentFrame = int(cmds.currentTime(query=True))
        target = int(math.floor(self.currentFrame + 1))
        try:
            result = self._updateCurrentFrame(target, endFrame, startFrame, endFrame)
        except ValueError, e:
            cmds.warning(str(e))
        else:
            if self.updateTimeslider:
                cmds.currentTime(result, edit=True)
        self._focusOnButton(self.ui.stepForward)

    def jumpBack(self):
        startFrame, endFrame = self.settingsWidget.getFrameRange()
        target = startFrame
        if target is not None:
            result = self._updateCurrentFrame(target, startFrame, startFrame, endFrame)
        if self.updateTimeslider:
            cmds.currentTime(result, edit=True)
        self._focusOnButton(self.ui.jumpBack)

    def jumpForward(self):
        startFrame, endFrame = self.settingsWidget.getFrameRange()
        target = endFrame
        if target is not None:
            result = self._updateCurrentFrame(target, endFrame, startFrame, endFrame)
        if self.updateTimeslider:
            cmds.currentTime(result, edit=True)
        self._focusOnButton(self.ui.jumpForward)

    def newMinFrame(self, minFrame):
        # TODO: If this widget is currently displaying an image for a frame
        #       that is now out of range, should that be updated now?
        pass

    def newMaxFrame(self, maxFrame):
        # TODO: If this widget is currently displaying an image for a frame
        #       that is now out of range, should that be updated now?
        pass


class FacePreviewSave(QWidget):
    def __init__(self, parent, settingsWidget, displayWidget, *args, **kwargs):
        super(FacePreviewSave,self).__init__(*args, **kwargs)
        self.setParent(parent)
        self.settingsWidget = settingsWidget
        self.displayWidget = displayWidget
        currentDir = os.path.dirname(__file__)
        self.preview_ui_file = QFile(os.path.join(currentDir, SAVE_UI_FILE))
        self.initUI()

    def initUI(self):
        # Load UI config from SAVE_UI_FILE
        loader = QUiLoader()
        self.preview_ui_file.open(QFile.ReadOnly)
        self.ui = loader.load(self.preview_ui_file, parentWidget=self.parent())
        self.preview_ui_file.close()

        # Setup the results box to display where image files were saved
        self.ui.result.setReadOnly(True)
        font = self.ui.result.font()
        font.setPointSize(8)
        self.ui.result.setFont(font)

        # TODO: Remove the following two lines after we have support for making a movie file
        self.ui.movieFileLabel.setEnabled(False)
        self.ui.movieFile.setEnabled(False)

        # Connect the buttons
        self.ui.saveImage.clicked.connect(self.saveImage)
        self.ui.saveAllImages.clicked.connect(self.saveAllImages)
        self.ui.openFolder.clicked.connect(self.openFolder)
        self.ui.openFolder.setIcon(self.ui.openFolder.style().standardIcon(QStyle.SP_DirIcon))

    def saveAllImages(self):
        self.ui.saveAllImages.setEnabled(False)
        try:
            self._saveAllImages()
        finally:
            self.ui.saveAllImages.setEnabled(True)

    def _saveAllImages(self):
        startFrame, endFrame = self.settingsWidget.getFrameRange()
        if startFrame is None or endFrame is None:
            return None
        clipName, clipStart, clipEnd = self.settingsWidget.getClipInfo(startFrame, endFrame)
        if clipName is None or clipStart is None or clipEnd is None:
            return None
        keyframes = self.parent().getAllProcFaceKeyframes(clipStart, clipEnd)
        self.saveImagesAndThenShow(clipName, keyframes, startFrame, endFrame)

    def saveImage(self):
        frameNum = self.displayWidget.currentFrame
        if frameNum is None:
            frameNum = cmds.currentTime(query=True)
        animName, keyframeBefore, keyframeAfter = self.parent().getProcFaceKeyframes(frameNum)
        if keyframeBefore is None and keyframeAfter is None:
            return None
        keyframes = selectKeyframesUsingFrameNum(frameNum, keyframeBefore, keyframeAfter)
        self.saveImagesAndThenShow(animName, keyframes, frameNum, frameNum)

    def saveImagesAndThenShow(self, animName, keyframes, startFrame, endFrame):
        # Setup and announce directory where image files will be saved
        homeDir = os.getenv('HOME')
        subDir = WIN_TITLE.replace(' ', '_').lower()
        subDir = os.path.join(homeDir, subDir)
        if not os.path.isdir(subDir):
            os.makedirs(subDir)
        subDir = tempfile.mkdtemp(prefix="%s_" % animName, dir=subDir)
        print("Saving face image files in: %s" % subDir)

        face_images.process_face_images(keyframes, startFrame, endFrame,
                                        allow_non_integer_frames=True,
                                        face_image_callback=face_images.save_images,
                                        callback_args={"dir":subDir})

        self.ui.result.setText(subDir)

        imageFiles = glob.glob(os.path.join(subDir, '*'))
        imageFiles.sort()
        startTime = time.time()
        for imageFile in imageFiles:
            #print("Showing %s" % imageFile)
            self.displayWidget.ui.displayLabel.setPixmap(QPixmap(imageFile))
            self.displayWidget.ui.displayLabel.repaint()
            qApp.processEvents()
            fileName = os.path.splitext(os.path.basename(imageFile))[0]
            self.displayWidget.setCurrentFrame(fileName)
            time.sleep(SLEEP_TIME_BETWEEN_DISPLAY_SEC)
        endTime = time.time()
        numImages = len(imageFiles)
        if numImages > 1:
            frameRate = numImages / (endTime-startTime)
            print("The %s images saved to disk were played at an approximate frame rate of %0.2f fps"
                  % (numImages, frameRate))

    def openFolder(self):
        dirPath = self.ui.result.text()
        if not dirPath:
            return None
        dirPath = dirPath.strip()
        if not dirPath:
            return None
        if not os.path.isdir(dirPath):
            raise ValueError("Invalid directory: %s" % dirPath)
        print("Opening %s" % dirPath)
        cmd = ["open", dirPath]
        subprocess.call(cmd)


def getGlobalPreviewUI():
    # This will allow us to assign hotkeys to buttons.
    return _globalPreviewUI


def main():
    global _globalPreviewUI
    ui = FacePreview()
    ui.show()
    _globalPreviewUI = ui
    return ui


if __name__ == '__main__':
    main()


