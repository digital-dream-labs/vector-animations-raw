

# The robot volume is specified as a float between 0.0 and 1.0, but this tool uses a scale
# of 0 to 10 and then converts that. Therefore, the default volume of 5 translates to 0.5
DEFAULT_VOLUME = 5

TOOLS_DIR_ENV_VAR = "ANKI_TOOLS"

EXPORT_PATH_ENV_VAR = "ANKI_ANIM_EXPORT_PATH"

PREPARE_SDK_SCRIPT = "pylibs/ankisdk/prepare_sdk_usage.py"

START_SIM_SCRIPT = "pylibs/ankisdk/start_sim.py -r"

PREVIEW_SCRIPT = "pylibs/ankisdk/preview_anim_on_robot_using_sdk.py"

PYTHON3_INTERPRETER = "/usr/local/bin/python3"

WIN_TITLE = "Play animations on robot"

ANIM_UI_FILE = "preview_anim.ui"
STATUS_UI_FILE = "preview_status.ui"

CLIP_NAME_KEY = "clip_name"

USER_TYPE_ATTR = "animClip"
USER_SELECT_ATTR = "animClips"
LOOPS_ATTR = "numLoops"
ALL_ATTRS = [USER_TYPE_ATTR, USER_SELECT_ATTR, LOOPS_ATTR]

ANIM_NAMES_FLAG = "-anims"
ANIM_FILES_FLAG = "-files"
ANIM_VOLUME_FLAG = "-volume"
ANIM_IGNORE_CLIFFS_FLAG = "-ignore_cliffs"
ANIM_CONNECT_CUBES_FLAG = "-connect_cubes"

ARG_DELIMITER = ','
LOOPS_DELIMITER = ':'


# This will allow us to assign a hotkey to the "Preview" button
_globalPreviewUI = None


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

from ankimaya import game_exporter
from ankiutils.anim_files import get_newest_json_file, get_json_file_for_anim
from robot_config import BATTERY_VOLTAGE_LABEL, BATTERY_VOLTAGE_LOW_THRESHOLD
from ankimaya.head_angle_selector import getHeadAngleVariationExportSettings
from ankiutils.head_angle_config import HeadAngleConfig


mayaMainWindowPtr = omui.MQtUtil.mainWindow()
mayaMainWindow = wrapInstance(long(mayaMainWindowPtr), QWidget)


def get_tools_dir():
    tools_dir = os.getenv(TOOLS_DIR_ENV_VAR)
    if not tools_dir:
        err_msg = "Failed to query the '%s' environment variable" % TOOLS_DIR_ENV_VAR
        cmds.warning(err_msg)
    return tools_dir


def get_export_path(env_var=EXPORT_PATH_ENV_VAR):
    export_path = os.getenv(env_var)
    if not export_path:
        err_msg = "Failed to query the '%s' environment variable" % env_var
        cmds.warning(err_msg)
        raise ValueError(err_msg)
    return export_path


def play_anim_clips(animClips=None, animFiles=None, robotVolume=None, ignoreCliffs=None, connectCubes=None,
                    exportPath=None, preview_script=PREVIEW_SCRIPT, arg_delimiter=ARG_DELIMITER):
    if not exportPath:
        try:
            exportPath = get_export_path()
        except ValueError, e:
            exportPath = None

    if not animClips:
        err_msg = "Unable to determine which animation clips should be played"
        if animFiles:
            animClips = [os.path.splitext(os.path.basename(x))[0] for x in animFiles]
        elif exportPath:
            try:
                animFile = get_newest_json_file(exportPath)
            except ValueError as err:
                cmds.warning(str(err))
                raise ValueError(err_msg)
            animFiles = [animFile]
            animClips = [os.path.splitext(os.path.basename(animFile))[0]]
        else:
            raise ValueError(err_msg)

    if animFiles:
        for animFile in animFiles:
            if not animFile or not os.path.isfile(animFile):
                raise ValueError("File missing: %s" % animFile)

    animClips = arg_delimiter.join(animClips)
    preview_script += " %s %s" % (ANIM_NAMES_FLAG, animClips)
    if animFiles:
        animFiles = arg_delimiter.join(animFiles)
        preview_script += " %s %s" % (ANIM_FILES_FLAG, animFiles)
    if robotVolume is not None:
        preview_script += " %s %s" % (ANIM_VOLUME_FLAG, robotVolume)
    if ignoreCliffs:
        preview_script += " %s" % ANIM_IGNORE_CLIFFS_FLAG
    if connectCubes:
        preview_script += " %s" % ANIM_CONNECT_CUBES_FLAG
    status, stdout, stderr, display_msg = run_command_wrapper(preview_script)
    if stdout:
        low_voltage = check_stdout_for_low_voltage(stdout)
    return display_msg


def check_stdout_for_low_voltage(stdout, threshold=BATTERY_VOLTAGE_LOW_THRESHOLD,
                                 label=BATTERY_VOLTAGE_LABEL, widget=None):
    voltage_feedback = [x for x in stdout.split(os.linesep) if label in x]
    if voltage_feedback:
        for voltage in voltage_feedback:
            voltage = voltage.lstrip(label)
            voltage = ast.literal_eval(voltage)
            if voltage < threshold:
                msg = "Robot battery voltage is low"
                cmds.warning(msg)
                if widget:
                    QMessageBox.critical(widget, "Alert", msg)
                return True
    return False


def get_environ_no_maya_in_pythonpath():
    """
    Strip all the Maya specific directories out of PYTHONPATH
    """
    python_path_no_maya = []
    try:
        python_path = os.environ['PYTHONPATH']
        maya_location = os.environ['MAYA_LOCATION']
    except KeyError:
        return None
    maya_location_parts = maya_location.split(os.sep)
    maya_base_dir = os.sep.join(maya_location_parts[:4])
    for py_dir in python_path.split(os.pathsep):
        if not py_dir.startswith(maya_base_dir):
            python_path_no_maya.append(py_dir)
    if not python_path_no_maya:
        return None
    python_path_no_maya = os.pathsep.join(python_path_no_maya)
    environ = os.environ.copy()
    environ['PYTHONPATH'] = python_path_no_maya
    if 'PYTHONHOME' in environ:
        del environ['PYTHONHOME']
    return environ


def run_command_core(cmd, stdout_pipe, stderr_pipe, shell):
    environ = get_environ_no_maya_in_pythonpath()
    #print("Running: %s" % cmd)
    try:
        p = subprocess.Popen(cmd.split(), stdout=stdout_pipe, stderr=stderr_pipe,
                             shell=shell, env=environ)
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


class PreviewSettings(QWidget):
    def __init__(self, *args, **kwargs):
        super(PreviewSettings,self).__init__(*args, **kwargs)
        self.setParent(mayaMainWindow)
        self.setWindowFlags(Qt.Window)
        self.animWidgets = []
        self.statusWidget = None
        self.gridCount = 0
        self.scroll = None
        self.scrollWidget = None
        self.scrollLayout = None
        self.vbox = None
        self.widget = None
        self.initUI()

    def _addWidgetToGrid(self, widget, column=0, lastInRow=True):
        self.grid.addWidget(widget, self.gridCount, column)
        if lastInRow:
            self.gridCount += 1

    def initUI(self):

        self.setGeometry(100, 100, 700, 330)
        self.setWindowTitle(WIN_TITLE)

        # At the top layer, a grid layout is used to hold buttons and widgets
        self.grid = QGridLayout(self)

        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
        # TODO: Can we use the following instead of forcing the window to always stay on top?
        #self.setProperty("saveWindowPref", True)
        # Along with that setProperty() call, we may need to call setObjectName() to give it a name.

        self.show()
        self.setLayout(self.grid)

        self.addStatusWidget()

        # Add add-another-anim-clip button to the grid layout
        addAnimBtn = QPushButton("Add an animation to play in sequence...")
        addAnimBtn.clicked.connect(self.addAnimToSequence)
        self._addWidgetToGrid(addAnimBtn)

        # The scroll area holds the list of one or more anim clips to be played
        self.initScrollArea()

        self.addAnimToSequence()

        self.addBottomButtons()

    def initScrollArea(self):
        # The scroll area holds the list of one or more anim clips to be played
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

    def addBottomButtons(self):
        self.bottomBtns = QGridLayout(self)

        # Add create button to the grid layout
        self.setBtn = QPushButton("Play Animations")
        self.setBtn.clicked.connect(self.doPlayAnims)
        self.bottomBtns.addWidget(self.setBtn, 0, 0)

        # Add cancel button to the grid layout
        self.cancelBtn = QPushButton("Cancel")
        self.cancelBtn.clicked.connect(self.doCancel)
        self.bottomBtns.addWidget(self.cancelBtn, 0, 1)

        self.bottomBtnsWidget = QWidget()
        self.bottomBtnsWidget.setLayout(self.bottomBtns)
        self._addWidgetToGrid(self.bottomBtnsWidget)

    def addStatusWidget(self):
        self.statusWidget = ToolStatus(self.widget)
        self._addWidgetToGrid(self.statusWidget.ui)
        self.statusWidget.ui.setMinimumSize(500, 70)
        self.statusWidget.ui.show()

    def addAnimToSequence(self):
        anim = AnimToPlay(self.scrollWidget)
        self.animWidgets.append(anim)
        self.scrollLayout.addWidget(anim.ui)
        anim.ui.setMinimumSize(500, 120)
        anim.ui.show()

    def getAnimClipData(self, previewData):
        animClipDataDict = {}
        for attr in ALL_ATTRS:
            uiAttr = eval("previewData.ui.%s" % attr)
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

    def getAnimInfo(self, animWidget, exportPath):
        animClipData = self.getAnimClipData(animWidget)
        try:
            numLoops = int(animClipData[LOOPS_ATTR])
        except (TypeError, ValueError):
            numLoops = 1
        else:
            numLoops = max(1, numLoops)
        animClip = animClipData[USER_TYPE_ATTR].strip()
        if not animClip:
            animClip = animClipData[USER_SELECT_ATTR].strip()
        if animClip:
            try:
                animFile = get_json_file_for_anim(animClip, exportPath)
            except (ValueError, TypeError, AttributeError) as err:
                #cmds.warning(str(err))
                print(str(err))
                return (animClip, numLoops, None)
        else:
            try:
                animFile = get_newest_json_file(exportPath)
            except ValueError as err:
                cmds.warning(str(err))
                return (None, None, None)
            animClip = os.path.splitext(os.path.basename(animFile))[0]

        if not animFile or not os.path.isfile(animFile):
            raise ValueError("File missing: %s" % animFile)

        return (animClip, numLoops, animFile)

    def doPlayAnims(self, loops_delimiter=LOOPS_DELIMITER):

        # The following is a requirement if we only/mostly want to play locally exported animations.
        # If we use this tool to play animations that are already built into the game, we can get
        # rid of this and the subsequent logic for querying and passing along the animation files.
        try:
            exportPath = get_export_path()
        except ValueError, e:
            self.statusWidget.ui.enablePreview.setText(str(e))
            return None

        animClips = []
        animFiles = []
        missingAnimFiles = []
        for animWidget in self.animWidgets:
            if not animWidget.included:
                continue
            animClip, numLoops, animFile = self.getAnimInfo(animWidget, exportPath)
            if not animClip:
                return None
            animClips.append(animClip + loops_delimiter + str(numLoops))
            if not animFile:
                missingAnimFiles.append(animClip)
            elif animFile not in animFiles:
                animFiles.append(animFile)
        if not animClips:
            msg = "No animation specified to play"
            print msg,
            self.statusWidget.ui.enablePreview.setText(msg)
            qApp.processEvents()
            return None

        robotVolume = self.statusWidget.ui.robotVolume.currentText()
        robotVolume = int(robotVolume)/10.0

        ignoreCliffs = _getCheckState(self.statusWidget.ui.ignoreCliffs)
        connectCubes = _getCheckState(self.statusWidget.ui.connectCubes)

        msg = "Playing animations: %s" % ', '.join(animClips)
        if missingAnimFiles:
            cmds.warning("The following animations will be played from build since no local "
                         "animation data was found: %s" % ', '.join(missingAnimFiles))
        else:
            print msg,
        self.statusWidget.ui.enablePreview.setText(msg)
        qApp.processEvents()
        display_msg = play_anim_clips(animClips, animFiles, robotVolume, ignoreCliffs, connectCubes,
                                      exportPath)
        if display_msg:
            self.statusWidget.ui.enablePreview.setText(display_msg)

    def doCancel(self):
        self.close()


def _getCheckState(checkBox):
    state = checkBox.checkState()
    if state == Qt.CheckState.Unchecked:
        return False
    elif state == Qt.CheckState.Checked:
        return True


class ToolStatus(QWidget):
    def __init__(self, parent, *args, **kwargs):
        super(ToolStatus,self).__init__(*args, **kwargs)
        self.setParent(parent)
        currentDir = os.path.dirname(__file__)
        self.tools_dir = None
        self.preview_ui_file = QFile(os.path.join(currentDir, STATUS_UI_FILE))
        self.initUI()

    def initUI(self):
        # Load UI config from STATUS_UI_FILE
        loader = QUiLoader()
        self.preview_ui_file.open(QFile.ReadOnly)
        self.ui = loader.load(self.preview_ui_file, parentWidget=self.parent())
        self.preview_ui_file.close()

        # Setup the status box
        self.ui.enablePreview.setReadOnly(True)

        # Connect the buttons
        self.ui.enable.clicked.connect(self.doEnable)
        self.ui.disable.clicked.connect(self.doDisable)
        self.ui.installAndroid.clicked.connect(self.doInstall)
        self.ui.installIos.clicked.connect(self.doIosInstall)

        # Populate the menu of robot volume values
        for vol in range(11):
            self.ui.robotVolume.addItem(str(vol))
        default_vol = self.ui.robotVolume.findText(str(DEFAULT_VOLUME))
        self.ui.robotVolume.setCurrentIndex(default_vol)

        self.tools_dir = get_tools_dir()

    def doEnable(self, prepare_sdk_script=PREPARE_SDK_SCRIPT, start_sim_script=START_SIM_SCRIPT):
        if not self.tools_dir:
            self.tools_dir = get_tools_dir()
            if not self.tools_dir:
                return None
        display_msg = ""
        low_voltage = False
        cmd = os.path.join(self.tools_dir, prepare_sdk_script)
        status, stdout, stderr = run_command(cmd, run_with_py3=True)
        if status != 0:
            display_msg = stderr.split(os.linesep)[-1]
        else:
            if stdout:
                display_msg = stdout.split(os.linesep)[-1]
            time.sleep(3)
            cmd = os.path.join(self.tools_dir, start_sim_script)
            status, stdout, stderr = run_command(cmd, num_retries=5, run_with_py3=True)
            if status != 0:
                display_msg = stderr.split(os.linesep)[-1]
            if stdout:
                low_voltage = check_stdout_for_low_voltage(stdout)
        if display_msg:
            if status != 0:
                cmds.warning(display_msg)
            elif not low_voltage:
                print display_msg,
            self.ui.enablePreview.setText(display_msg)

    def doDisable(self, prepare_sdk_script=PREPARE_SDK_SCRIPT):
        if not self.tools_dir:
            self.tools_dir = get_tools_dir()
            if not self.tools_dir:
                return None
        prepare_sdk_script += " -stop"
        status, stdout, stderr = self.run_command_wrapper(prepare_sdk_script)

    def doIosInstall(self, prepare_sdk_script=PREPARE_SDK_SCRIPT):
        self.doInstall(prepare_sdk_script, ios=True)

    def doInstall(self, prepare_sdk_script=PREPARE_SDK_SCRIPT, ios=False):
        install = self.alertUserInstall()
        if not install:
            msg = "Installation aborted"
            print msg,
            self.ui.enablePreview.setText(msg)
            return None
        if not self.tools_dir:
            self.tools_dir = get_tools_dir()
            if not self.tools_dir:
                return None
        installMsg = "Installing software on the connected device and this machine..."
        print installMsg,
        self.ui.enablePreview.setText(installMsg)
        qApp.processEvents()
        prepare_sdk_script += " -install"
        if ios:
            prepare_sdk_script += " -ios"
        status, stdout, stderr = self.run_command_wrapper(prepare_sdk_script)

    def alertUserInstall(self):
        """
        Use a message box to confirm installation.
        """
        reply = QMessageBox.question(self, "Message",
            "Install (or reinstall) build on connected device and SDK on this machine?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        return reply == QMessageBox.Yes

    def run_command_wrapper(self, cmd, shell=False):
        status, stdout, stderr, display_msg = run_command_wrapper(cmd, self.tools_dir, shell)
        if display_msg:
            self.ui.enablePreview.setText(display_msg)
        return (status, stdout, stderr)


class AnimToPlay(QWidget):
    def __init__(self, parent, *args, **kwargs):
        super(AnimToPlay,self).__init__(*args, **kwargs)
        self.setParent(parent)
        currentDir = os.path.dirname(__file__)
        self.preview_ui_file = QFile(os.path.join(currentDir, ANIM_UI_FILE))
        self.included = True
        self.initUI()
        self.ui.animClips.installEventFilter(self)

    def eventFilter(self, obj, event):
        """
        Event filter for rerouting wheel events away from combo boxes.
        """
        if event.type() == QEvent.Wheel and isinstance(obj, QComboBox):
            # Handle all wheel events for combo boxes
            event.ignore()
            return True
        else:
            try:
                return super(AnimToPlay, self).eventFilter(obj, event)
            except TypeError:
                return False

    def closeEvent(self, e):
        """
        Remove the event filter
        """
        self.ui.animClips.removeEventFilter(self)
        return super(AnimToPlay, self).closeEvent(e)

    def initUI(self):

        # Load UI config from ANIM_UI_FILE
        loader = QUiLoader()
        self.preview_ui_file.open(QFile.ReadOnly)
        self.ui = loader.load(self.preview_ui_file, parentWidget=self.parent())
        self.preview_ui_file.close()

        # Add current anim clips to the pulldown menu
        try:
            animClips = self.getAnimClips()
        except BaseException, e:
            cmds.warning("Failed to get the list of animation clips from the Game Exporter")
            animClips = []
        for animClip in animClips:
            self.ui.animClips.addItem(animClip)

        # Add pair of checkboxes to allow removal of this anim clip.
        self.ui.removeAnimComboBox.stateChanged.connect(self.removeAnimChanged)
        self.removeAnimChanged()
        self.ui.confirmComboBox.stateChanged.connect(self.confirmRemoveAnimChanged)
        self.confirmRemoveAnimChanged()

    def getAnimClips(self):

        # Get anim clips from Game Exporter...
        gameExporterAnims = game_exporter.get_clip_info('', include_all=True)[2]
        gameExporterAnims = [str(x[CLIP_NAME_KEY]) for x in gameExporterAnims]
        if '' in gameExporterAnims:
            gameExporterAnims.remove('')
        print("Animation clips listed in Game Exporter = %s" % gameExporterAnims)

        numVariations = None
        if gameExporterAnims:
            # Get info for any head angle variations...
            numVariations, whichKeyframes = getHeadAngleVariationExportSettings()
            print("Number of head angle variations = %s" % numVariations)

        # Add all anim clips from Game Exporter...
        animClips = []
        headAngleConfig = HeadAngleConfig()
        for anim in gameExporterAnims:
            if anim not in animClips:
                animClips.append(anim)
            if numVariations:
                varMapping = headAngleConfig.get_anim_variation_to_range_mapping(anim, numVariations)
                sortedClips = varMapping.keys()
                sortedClips.sort()
                for anim_variation in sortedClips:
                    if anim_variation not in animClips:
                        animClips.append(anim_variation)
        return animClips

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


def getGlobalPreviewUI():
    # This will allow us to assign a hotkey to the "Preview" button
    return _globalPreviewUI


def main():
    global _globalPreviewUI
    ui = PreviewSettings()
    ui.show()
    _globalPreviewUI = ui
    return ui


if __name__ == '__main__':
    main()


