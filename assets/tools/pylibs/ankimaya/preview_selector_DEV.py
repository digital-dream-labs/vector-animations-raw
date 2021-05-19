import os

ROBOT_IP_ADDRESS = "%s.%s.%s.%s"

ANIM_PORT = "8889"
ENGINE_PORT = "8888"

PING_TIMEOUT_SEC = 5
SHORT_TIMEOUT = 0.25
BUTTON_WAIT = 4.0

THIS_WIN_TITLE = "MacBlast"

# This is the order of preference for the dock button:
DOCKING_WINDOW = [THIS_WIN_TITLE, 'ChannelBoxLayerEditor', 'AttributeEditor']
# If none of these are found, then it will get docked into the "main" window.
# User can still drag the window anywhere.

# The IP address should be filled in when using this URL
ROBOT_ANIM_URL = "http://%s:" + ANIM_PORT + "/"

# The variable name and value should be filled in after the IP address when using this URL
ROBOT_ANIM_VAR_SET_URL = ROBOT_ANIM_URL + "consolevarset?key=%s&value=%s"

# The animation file to upload should be filled in after the IP address when using this URL
ROBOT_ANIM_RESOURCES_URL = ROBOT_ANIM_URL + "resources/assets/animations/%s"

# The function name should be filled in after the IP address when using this URL
ROBOT_ANIM_FUNC_CALL_URL = ROBOT_ANIM_URL + "consolefunccall?func=%s"

# The function name and argument should be filled in after the IP address when using this URL
ROBOT_ANIM_FUNC_CALL_WITH_ARGS_URL = ROBOT_ANIM_FUNC_CALL_URL + "&args=%s"

BATTERY_STATS_CMD = 'http://{0}:8888/getenginestats?1000000000000000000000000000000000000'

ABORT_ANIM_CMD = 'http://{0}:{1}/consolefunccall?func=AbortCurrentAnimation'

SHOW_CURRENT_ANIM_CMD = 'http://{0}:{1}/consolefunccall?func=ShowCurrentAnimation'

LIST_ALL_ANIMS_CMD = 'http://{0}:{1}/consolefunccall?func=ListAnimations'

# TODO: Set this default volume back to 5 after https://anki.slack.com/archives/C73H8463E/p1518553466000115 is fixed
# Volume has changed to be from 0 to 5
DEFAULT_VOLUME = 3
VOLUME_CMD1 = 'http://{0}:{1}/consolevarset?key=MasterVolumeLevel&value={2}'
VOLUME_CMD2 = 'http://{0}:{1}/consolefunccall?func=DebugSetMasterVolume&args='
MAX_VOLUME = 5
DEV_DO_NOTHING_CMD0 = 'http://{0}:{1}/consolefunccall?func=SetComplete&args='
DEV_DO_NOTHING_CMD1 = 'http://{0}:{1}/consolefunccall?func=SetDevDoNothing'
DEV_DO_NOTHING_CMD2 = 'http://{0}:{1}/consolevarset?key=DevMoveToStage&value=4'
DEV_DO_NOTHING_CMD3 = 'http://{0}:{1}/consolefunccall?func=MoveToStage&args='

GET_PUBLICKEY_CMD1 = \
    '/usr/bin/curl -sL -o {0}/.ssh/id_rsa_victor_shared https://www.dropbox.com/s/mgxgdouo0id6j9m/id_rsa_victor_shared?dl=0'.format(
        os.environ['HOME'])
GET_PUBLICKEY_CMD2 = '/bin/chmod 600 {0}/.ssh/id_rsa_victor_shared'.format(os.environ['HOME'])
GET_PUBLICKEY_CMD3 = '/usr/bin/ssh-add {0}/.ssh/id_rsa_victor_shared'.format(os.environ['HOME'])

TOOLS_DIR_ENV_VAR = "ANKI_TOOLS"
PREVIEW_SELECTOR_UI_ICONS_DIR = os.path.join(os.getenv(TOOLS_DIR_ENV_VAR), "icons", "PreviewSelectorUI")
PREVIEW_SELECTOR_UI_ALL_PNG = os.path.join(PREVIEW_SELECTOR_UI_ICONS_DIR, "coz_movement_ui_all.png")
RESTART_ICON = os.path.join(PREVIEW_SELECTOR_UI_ICONS_DIR, "restart.png")
INSTALL_ICON = os.path.join(PREVIEW_SELECTOR_UI_ICONS_DIR, "install.png")
REFRESH_ICON = os.path.join(PREVIEW_SELECTOR_UI_ICONS_DIR, "refresh.png")
UPDATE_FACE_ICON = os.path.join(PREVIEW_SELECTOR_UI_ICONS_DIR, "update_face.png")
PING_ICON = os.path.join(PREVIEW_SELECTOR_UI_ICONS_DIR, "ping_robot.png")
BATTERY_ICON = os.path.join(PREVIEW_SELECTOR_UI_ICONS_DIR, "check_battery.png")
ENGINE_PAGE_ICON = os.path.join(PREVIEW_SELECTOR_UI_ICONS_DIR, "engine_web.png")
ANIM_PAGE_ICON = os.path.join(PREVIEW_SELECTOR_UI_ICONS_DIR, "anim_web.png")
ADD_ANIM_ICON = os.path.join(PREVIEW_SELECTOR_UI_ICONS_DIR, "add_anim_to_play.png")
PUBLISH_ICON = os.path.join(PREVIEW_SELECTOR_UI_ICONS_DIR, "../CozmoUI/coz_export2Robot.png")
ABORT_ICON = os.path.join(PREVIEW_SELECTOR_UI_ICONS_DIR, "abort.png")
PLAY_ICON = os.path.join(PREVIEW_SELECTOR_UI_ICONS_DIR, "play_anim.png")

CLOSE_ICON = os.path.join(PREVIEW_SELECTOR_UI_ICONS_DIR, "close.png")
WIN1_ICON = os.path.join(PREVIEW_SELECTOR_UI_ICONS_DIR, "hide.png")
WIN2_ICON = os.path.join(PREVIEW_SELECTOR_UI_ICONS_DIR, "dock.png")
WIN3_ICON = os.path.join(PREVIEW_SELECTOR_UI_ICONS_DIR, "float.png")

ICON_WIDTH = 20
ICON_HEIGHT = 20

SWITCH_ICON_SIZE = [37.0, 37.0]
SWITCH_POSITION = [400.0, 26.0]

EXPORT_PATH_ENV_VAR = "ANKI_ANIM_EXPORT_PATH"

ROBOT_DEPLOY_SCRIPT = "pylibs/ankimaya/robot_deploy.py"

START_SIM_SCRIPT = "pylibs/ankisdk/start_sim.py -r"

PYTHON3_INTERPRETER = "/usr/local/bin/python3"

WIN_TITLE = "Play animations on robot"
TITLE_STYLE = "QLabel { font-size: 15px;  border: 1px solid rgba(188, 188, 188, 250); } "
TITLE_STYLE += "QSpinBox { color: rgb(50, 50, 50); font-size: 11px; background-color: rgba(255, 188, 20, 50); }"

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

SCRIPTJOB_EVENT = 'SceneOpened'

SLEEP_ANIM_CLIP = 'anim_face_sleeping'

PUBLICKEY_MSG = "Permission denied (publickey)"

MAC_CLIENT_DIR = os.path.join(os.getenv(TOOLS_DIR_ENV_VAR), "other", "Mac-client_Helper")

# This will allow us to assign a hotkey to the "Preview" button
_globalPreviewUI = None

# This is used to pass an abort anim flag from the UI class method to a module function
_globalAbortAnim = False

_globalDockControl = None

import subprocess
import time
import ast
import requests
import webbrowser

from maya import cmds
from maya import OpenMayaUI as omui
import maya.mel as mel

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
import ankimaya.publish as publish
from ankiutils.anim_files import get_newest_json_file, get_json_file_for_anim, report_file_stats
from robot_config import BATTERY_VOLTAGE_LABEL, BATTERY_VOLTAGE_LOW_THRESHOLD
from ankimaya.head_angle_selector import getHeadAngleVariationExportSettings
from ankiutils.head_angle_config import HeadAngleConfig
from window_docker import Dock

from vector_dialog import *

mayaMainWindowPtr = omui.MQtUtil.mainWindow()
mayaMainWindow = wrapInstance(long(mayaMainWindowPtr), QWidget)


# the scriptJob runs when a scene has been loaded to refresh the animation clips listed in the drop down menu
def _runReloadAnimScriptJob():
    try:
        main()
    except:
        cmds.warning('problem reinitializing macblast')


def _deleteScriptJob():
    for e in cmds.scriptJob(lj=True):
        if '_runReloadAnimScriptJob' in e:
            n = int(e.split(':')[0])
            cmds.scriptJob(kill=n)


def _createScriptJob():
    _deleteScriptJob()
    cmds.scriptJob(e=(SCRIPTJOB_EVENT, _runReloadAnimScriptJob))


def get_tools_dir(env_var=TOOLS_DIR_ENV_VAR):
    tools_dir = os.getenv(env_var)
    if not tools_dir:
        err_msg = "Failed to query the '%s' environment variable" % env_var
        cmds.warning(err_msg)
    return tools_dir


def get_export_path(env_var=EXPORT_PATH_ENV_VAR):
    export_path = os.getenv(env_var)
    if not export_path:
        err_msg = "Failed to query the '%s' environment variable" % env_var
        cmds.warning(err_msg)
        raise ValueError(err_msg)
    return export_path


def update_animation(ipAddress, animFile, animFuncCallUrl=ROBOT_ANIM_FUNC_CALL_WITH_ARGS_URL,
                     engine=False):
    addAnimUrl = animFuncCallUrl % (ipAddress, "AddAnimation", os.path.basename(animFile))
    if engine:
        addAnimUrl = addAnimUrl.replace(ANIM_PORT, ENGINE_PORT)
    try:
        r = requests.post(addAnimUrl, timeout=10.0)
    except EnvironmentError, e:
        err_msg = "Failed to add/update animation from %s file because: %s" % (animFile, e)
        err_msg += os.linesep + "(tried: %s)" % addAnimUrl
        cmds.warning(err_msg)
        raise RuntimeError(err_msg)


def transfer_file(ipAddress, animFile, animResourcesUrl=ROBOT_ANIM_RESOURCES_URL, retry=True):
    err_msg = None
    file_stat_msg = report_file_stats(animFile)
    print file_stat_msg,
    animFileUrl = animResourcesUrl % (ipAddress, os.path.basename(animFile))
    try:
        r = requests.put(animFileUrl, data=open(animFile, 'rb').read(), timeout=10.0)
    except EnvironmentError, e:
        err_msg = "Failed to transfer %s file because: %s" % (animFile, e)
        err_msg += os.linesep + "(tried: %s)" % animFileUrl
        cmds.warning(err_msg)
    else:
        if r.status_code > 399:
            err_msg = "Failed to transfer %s file (status %s)" % (animFile, r.status_code)
            err_msg += os.linesep + "(tried: %s)" % animFileUrl
            cmds.warning(err_msg)
    if err_msg and retry:
        remountScript = ROBOT_DEPLOY_SCRIPT + " -remount_fs " + ipAddress
        status, stdout, stderr, display_msg = run_command_wrapper(remountScript)
        transfer_file(ipAddress, animFile, animResourcesUrl, retry=False)
    elif err_msg:
        raise RuntimeError(err_msg)


def play_anim_clips(ipAddress, animClips=None, animFiles=None, robotVolume=None, ignoreCliffs=None,
                    connectCubes=None, exportPath=None, animFuncCallUrl=ROBOT_ANIM_FUNC_CALL_WITH_ARGS_URL,
                    robotStatusLabel=None, rgbFace=False):
    global _globalAbortAnim
    _globalAbortAnim = False
    msg = None
    if not exportPath:
        try:
            exportPath = get_export_path()
        except ValueError, e:
            exportPath = None

    if not animClips:
        err_msg = "Unable to determine which animation clips should be played"
        if animFiles:
            animClips = [(os.path.splitext(os.path.basename(x))[0], 1) for x in animFiles]
        elif exportPath:
            try:
                animFile = get_newest_json_file(exportPath)
            except ValueError as err:
                cmds.warning(str(err))
                raise ValueError(err_msg)
            animFiles = [animFile]
            animClips = [(os.path.splitext(os.path.basename(animFile))[0], 1)]
        else:
            raise ValueError(err_msg)

    if animFiles:
        for animFile in animFiles:
            if not animFile or not os.path.isfile(animFile):
                raise ValueError("File missing: %s" % animFile)
            try:
                transfer_file(ipAddress, animFile)
                update_animation(ipAddress, animFile, animFuncCallUrl)
                update_animation(ipAddress, animFile, animFuncCallUrl, engine=True)
            except RuntimeError, e:
                err_msg = str(e).split(os.linesep)[0]
                cmds.warning(err_msg)
                return err_msg

    numClips = len(animClips)
    clipCount = 0
    for animClip, numLoops in animClips:
        # This was the original URL for playing animations from the vic-anim process on robot:
        # playAnimUrl = animFuncCallUrl % (ipAddress, "PlayAnimation", animClip)
        # The following URL will instead play animations from the vic-engine process on robot:
        playAnimUrl = (animFuncCallUrl % (ipAddress, "PlayAnimationByName", animClip)).replace(ANIM_PORT, ENGINE_PORT)
        if numLoops or rgbFace:
            playAnimUrl += "+%s" % numLoops
            if rgbFace:
                # set 'renderInEyeHue' to false when we want to preserve the image RGB colors on robot's face
                playAnimUrl += "+false"
        try:
            r = requests.post(playAnimUrl, timeout=10.0)
            # this seems to fix sequences not playing
            # do not wait if we are playing the last or only script
            if numClips > 1 and clipCount != numClips - 1:
                waitForAnim(robotStatusLabel=robotStatusLabel, robotIpAddress=ipAddress)
        except requests.exceptions.ConnectionError, e:
            msg = "Failed to play '%s' animation; check robot connection" % animClip
            cmds.warning(msg)
            if PUBLICKEY_MSG in msg:
                cmds.warning("Public key error; try 'Get Public Key' in the context menu to fix this")
        except EnvironmentError, e:
            msg = "Failed to play '%s' animation because: %s" % (animClip, e)
            cmds.warning(msg)
        clipCount += 1
        if _globalAbortAnim:
            _globalAbortAnim = False
            break
    return msg


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


def is_pingable(ip_address):
    # this function should either raise an exception or return None if it fails to determine online or offline
    # this function should internally handle any exceptions that could happen based on the specific implementation
    cmd = '/sbin/ping {0} -c 1 -t {1}'.format(ip_address, PING_TIMEOUT_SEC)
    try:
        status, stdout, stderr = run_command(cmd)
    except:
        cmds.warning("ping command failed")
        return None
    return (status == 0)  # this will return True if the ping command succeeded or else return False


class PreviewSettings(QWidget):
    def __init__(self, *args, **kwargs):
        super(PreviewSettings, self).__init__(*args, **kwargs)
        self.setParent(mayaMainWindow)
        self.setWindowFlags(Qt.Window)
        self.animWidgets = []
        self.scroll = None
        self.scrollWidget = None
        self.scrollLayout = None
        self.vbox = None
        self.widget = None
        self.isConnectedToRobot = False
        self.dockingTabHome = kwargs.get('dockingTabHome', DOCKING_WINDOW[0])
        self.lastPlayButtonPress = 0
        self.robotIpAddress = None
        self.iconButtons = []
        self.initUI()
        self.initUIToolStatus()

        self.show()
        self.vectorSettings = SettingsDialog()

    def initUI(self):
        self.setWindowTitle(WIN_TITLE)

        # Main layout is this vertical box
        self.lo = QVBoxLayout()
        self.setLayout(self.lo)
        self.lo.setAlignment(Qt.AlignTop)

        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)

        # Title row
        self.titleLabel = QLabel(WIN_TITLE)
        self.titleLabel.setAlignment(Qt.AlignHCenter)
        self.titleLabel.setStyleSheet(TITLE_STYLE)
        self.lo.addWidget(self.titleLabel)

        # Status row
        hlo = QHBoxLayout()
        self.lo.addLayout(hlo)
        rgbLabel = QLabel('RGB Face:')
        hlo.addWidget(rgbLabel)
        self.rgbCheckbox = QCheckBox()
        hlo.addWidget(self.rgbCheckbox)
        statusLabel = QLabel('Status: ')
        statusLabel.setAlignment(Qt.AlignRight)
        self.statusLineedit = QLineEdit('Ready')
        hlo.addWidget(statusLabel)
        hlo.addWidget(self.statusLineedit)

        # Volume combobox and IP address row
        self.midrow = QHBoxLayout()
        volumeLabel = QLabel("Volume")
        self.midrow.addWidget(volumeLabel)
        self.robotVolume = QComboBox()

        self.midrow.addWidget(self.robotVolume)

        # Populate the menu of robot volume values
        for vol in range(MAX_VOLUME + 1):
            self.robotVolume.addItem(str(vol))
        default_vol = self.robotVolume.findText(str(DEFAULT_VOLUME))
        self.robotVolume.setCurrentIndex(default_vol)
        self.robotVolume.currentIndexChanged.connect(self._changeVolume)
        label = QLabel("Robot IP:")
        self.midrow.addWidget(label)
        self.robotID = QLineEdit("")
        self.midrow.addWidget(self.robotID)
        self.lo.addLayout(self.midrow)

        # Main Icon row
        self.lo.addLayout(self.layoutTopRow())

        # The scroll area holds the list of one or more anim clips to be played
        self.lo.addWidget(self.initScrollArea())

        self.addAnimToSequence()

        # Bottom row of icons that deal with the window docking
        self.lo.addWidget(self.addBottomButtons())

        # Right click menu
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.openMenu)

    def layoutTopRow(self):

        lo_toprow = QHBoxLayout()
        lo_toprow.setAlignment(Qt.AlignLeft)

        restartButton = self.createSelectorButton(iconImg=RESTART_ICON,
                                                  tooltip="Restart Victor",
                                                  callback=self.doRestart)

        installButton = self.createSelectorButton(iconImg=INSTALL_ICON,
                                                  tooltip="Install latest master build from your ~/Downloads folder onto robot",
                                                  callback=self.doInstallRobot)

        refreshButton = self.createSelectorButton(iconImg=REFRESH_ICON,
                                                  tooltip="Send the local animation assets to the robot",
                                                  callback=self.doRefreshRobot)

        faceButton = self.createSelectorButton(iconImg=UPDATE_FACE_ICON,
                                               tooltip="('Update Face') update consolevars for face settings",
                                               callback=self.doUpdateFace)

        pingButton = self.createSelectorButton(iconImg=PING_ICON,
                                               tooltip="Ping Robot's IP address.",
                                               callback=self.update_ping_button_text)

        engineButton = self.createSelectorButton(iconImg=ENGINE_PAGE_ICON,
                                                 tooltip="Open the robot's engine web page.",
                                                 callback=self._openEngineWebpage)

        animButton = self.createSelectorButton(iconImg=ANIM_PAGE_ICON,
                                               tooltip="Open the robot's animation web page.",
                                               callback=self._openAnimWebpage)

        publishButton = self.createSelectorButton(iconImg=PUBLISH_ICON,
                                                  tooltip="Publish: Export and commit animation.",
                                                  callback=self.openPublish)

        playButton = self.createSelectorButton(iconImg=PLAY_ICON,
                                               tooltip="Play Anim",
                                               callback=self.doPlayAnims)

        addAnimBtn = self.createSelectorButton(iconImg=ADD_ANIM_ICON,
                                               tooltip="Add Animation To Sequence",
                                               callback=self.addAnimToSequence)

        abortButton = self.createSelectorButton(iconImg=ABORT_ICON,
                                                tooltip="Abort It",
                                                callback=self._stopAnims)

        batteryButton = self.createSelectorButton(iconImg=BATTERY_ICON,
                                                  tooltip="Checks Battery",
                                                  callback=self._getBatteryLevel)

        # Add button widgets
        lo_toprow.addWidget(publishButton)
        lo_toprow.addWidget(playButton)
        lo_toprow.addWidget(addAnimBtn)
        lo_toprow.addWidget(abortButton)

        qs = QLabel("|")
        qs.setFixedWidth(4)
        qs.setFixedHeight(50)
        qs.setStyleSheet("QLabel {  color: black ; font-size: 24px; }")
        lo_toprow.addWidget(qs)

        lo_toprow.addWidget(restartButton)
        lo_toprow.addWidget(installButton)
        lo_toprow.addWidget(refreshButton)
        lo_toprow.addWidget(faceButton)  # update face button
        lo_toprow.addWidget(pingButton)

        lo_toprow.addWidget(batteryButton)
        lo_toprow.addWidget(engineButton)
        lo_toprow.addWidget(animButton)

        return lo_toprow

    def createSelectorButton(self, iconImg, tooltip, callback, iconWidth=ICON_WIDTH, iconHeight=ICON_HEIGHT):
        aButton = QPushButton()
        icon = QIcon()
        icon.addPixmap(QPixmap(iconImg))
        aButton.setIcon(icon)
        aButton.setIconSize(QSize(iconWidth, iconHeight))
        aButton.setFixedWidth(iconWidth + 1)
        aButton.setToolTip(tooltip)
        aButton.clicked.connect(callback)
        self.iconButtons.append(aButton)
        return aButton

    def initUIToolStatus(self):
        # Setup the status box
        self.statusLineedit.setReadOnly(True)

        # Try to fill in the IP address from option var or environment variable
        ipAdd = str(cmds.optionVar(q='ROBOT_IP_ADDRESS'))
        if len(ipAdd) > 8:
            self.robotID.setText(ipAdd)
        else:
            self.robotID.setText(os.getenv('ROBOT_IP_ADDRESS'))

        self.tools_dir = get_tools_dir()

    def openMenu(self, pos, *args, **kwargs):
        """
        Opens a right-click menu anywhere on the widget, its not really a 'context' menu
        """
        menu = QMenu()

        loadNewClipAction = menu.addAction(self.tr("Refresh List of Animations"))
        stopAction = menu.addAction(self.tr("Stop Animation"))
        playAction = menu.addAction(self.tr("Play Animation"))

        toolsSubmenu = menu.addMenu(self.tr("Tools"))
        batteryAction = toolsSubmenu.addAction(self.tr("Check Battery Level"))
        publickeyAction = toolsSubmenu.addAction(self.tr("Get Public Key"))
        devDoNothingAction = toolsSubmenu.addAction(self.tr("Set Dev Do Nothing"))
        setCompleteAction = toolsSubmenu.addAction(self.tr("Set Complete (Toggle AI and DevDoNothing)"))
        pingAction = toolsSubmenu.addAction(self.tr("Ping Robot"))
        vectorSettingsAction = toolsSubmenu.addAction(self.tr("Vector Settings"))
        openMacClientAction = toolsSubmenu.addAction(self.tr("Open mac-client"))
        connectoToWifiAction = toolsSubmenu.addAction(self.tr("Connect to WiFi"))
        otaVectorAction = toolsSubmenu.addAction(self.tr("OTA To Latest"))

        webpageSubmenu = menu.addMenu(self.tr("Webpages"))
        enginePageAction = webpageSubmenu.addAction(self.tr("Open Engine Webpage"))
        animPageAction = webpageSubmenu.addAction(self.tr("Open Anim Webpage"))
        allAnimAction = webpageSubmenu.addAction(self.tr("Open All Animations Page"))

        widgetSubmenu = menu.addMenu(self.tr("Widgets"))
        floatAction = widgetSubmenu.addAction(self.tr("Toggle Float/Dock Widget"))
        hideAction = widgetSubmenu.addAction(self.tr("Hide and Dock Widget"))
        closeAction = widgetSubmenu.addAction(self.tr("Close Widget"))

        iconSizeSubmenu = menu.addMenu(self.tr("Change Icon Size"))
        smallIconAction = iconSizeSubmenu.addAction(self.tr("Small Icon Size (20)"))
        mediumIconAction = iconSizeSubmenu.addAction(self.tr("Med Icon Size (30)"))
        largeIconAction = iconSizeSubmenu.addAction(self.tr("Large Icon Size (40)"))

        action = menu.exec_(QCursor.pos())

        if action == loadNewClipAction:
            main()

        if action == stopAction:
            self._stopAnims()

        if action == playAction:
            self.doPlayAnims()

        if action == pingAction:
            self.update_ping_button_text()

        if action == batteryAction:
            self._getBatteryLevel()

        if action == enginePageAction:
            self._openEngineWebpage()

        if action == animPageAction:
            self._openAnimWebpage()

        if action == closeAction:
            self.close()

        if action == floatAction:
            self._toggleFloat()

        if action == hideAction:
            self._toggleDock()

        if action == allAnimAction:
            self._showAllAnimPage()

        if action == publickeyAction:
            self._getPublicKey()

        if action == devDoNothingAction:
            self._setDevDoNothing()

        if action == setCompleteAction:
            self._setComplete()

        if action == openMacClientAction:
            self.openMacClient()

        if action == connectoToWifiAction:
            self.connectToWifi()

        if action == vectorSettingsAction:
            self.openVectorSettings()

        if action == otaVectorAction:
            self.otaVectorToLatest()

        if action == smallIconAction:
            self._resizeIcons(20)

        if action == mediumIconAction:
            self._resizeIcons(30)

        if action == largeIconAction:
            self._resizeIcons(40)

    def _resizeIcons(self, value):
        for i in self.iconButtons:
            i.setFixedWidth(value)
            i.setFixedHeight(value)

    def getVectorSettingsStruct(self):
        vss = VectorSettingsStruct()
        vss.vector_id = self.vectorSettings.get_vector_id()
        vss.is_using_anki_robits = self.vectorSettings.is_using_anki_robits()
        vss.wifi_id = self.vectorSettings.get_wifi_id()
        vss.wifi_pass = self.vectorSettings.get_wifi_pass()
        return vss

    def openMacClient(self):
        MacClientDialog(self, self.getVectorSettingsStruct(), self.robotID, MacClientMode.MAC_CLIENT)

    def connectToWifi(self):
        MacClientDialog(self, self.getVectorSettingsStruct(), self.robotID, MacClientMode.WIFI)

    def otaVectorToLatest(self):
        MacClientDialog(self, self.getVectorSettingsStruct(), self.robotID, MacClientMode.OTA)

    def openVectorSettings(self):
        self.vectorSettings.show()

    def openPublish(self):
        # TODO when publish is ready, make this button launch it
        #publish.main()
        mel.eval('AnkiAnimExport')

    def _setComplete(self):
        ip = self.getRobotIpAddress()
        if ip is None:
            return
        cmd1 = DEV_DO_NOTHING_CMD0.format(ip, ENGINE_PORT)
        cmd2 = DEV_DO_NOTHING_CMD1.format(ip, ENGINE_PORT)
        try:
            r1 = requests.post(cmd1, timeout=SHORT_TIMEOUT)
            r2 = requests.post(cmd2, timeout=SHORT_TIMEOUT)
        except:
            cmds.warning("Failed to setComplete")
        else:
            if r1.status_code == 200:  # http OK
                print("Successfully set setComplete")

    def _setDevDoNothing(self):
        ip = self.getRobotIpAddress()
        if ip is None:
            return
        cmd1 = DEV_DO_NOTHING_CMD1.format(ip, ENGINE_PORT)
        cmd2 = DEV_DO_NOTHING_CMD2.format(ip, ENGINE_PORT)
        cmd3 = DEV_DO_NOTHING_CMD3.format(ip, ENGINE_PORT)
        try:
            r1 = requests.post(cmd1, timeout=SHORT_TIMEOUT)
            r2 = requests.post(cmd2, timeout=SHORT_TIMEOUT)
            r3 = requests.post(cmd3, timeout=SHORT_TIMEOUT)
        except:
            cmds.warning("Failed to set DevDoNothing")
        else:
            if r1.status_code == 200:  # http OK
                print("Successfully set DevDoNothing")

    def _getPublicKey(self):
        """
        This function can be used to download and install the robot's
        public key to fix the "permission denied (publickey)" error.
        """
        identity_added_msg = "Identity added"
        status, stdout, stderr = run_command(GET_PUBLICKEY_CMD1, shell=False)
        if status != 0:
            cmds.warning("problem fetching public key")
            return
        status, stdout, stderr = run_command(GET_PUBLICKEY_CMD2, shell=False)
        if status != 0:
            cmds.warning("problem changing permissions of '.ssh/id_rsa_victor_shared' file")
            return
        status, stdout, stderr = run_command(GET_PUBLICKEY_CMD3, shell=False)
        if identity_added_msg in stderr:
            msg = "success! you installed robot's .ssh/id_rsa_victor_shared"
            self.statusLineedit.setText(msg)
            return
        if status != 0:
            cmds.warning("problem adding ssh key")
            return
        print("Done getting key but did not detect '%s'" % identity_added_msg)

    def _stopAnims(self):
        self._enablePlayButton()
        global _globalAbortAnim
        ipAddress = self.getRobotIpAddress()
        url = ABORT_ANIM_CMD.format(ipAddress, ANIM_PORT)
        try:
            r = requests.post(url, timeout=PING_TIMEOUT_SEC)
        except:
            cmds.warning("Failed to abort the animation currently playing")
        _globalAbortAnim = True

    def initScrollArea(self):
        # The scroll area holds the list of one or more anim clips to be played
        self.scrollWidget = QWidget()
        self.scrollWidget.setGeometry(10, 400, 10, 400)
        self.scrollWidget.setParent(self)
        self.scrollLayout = QVBoxLayout(self.scrollWidget)
        self.scrollWidget.setLayout(self.scrollLayout)
        self.scroll = QScrollArea(self)
        self.scroll.setWidgetResizable(True)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setWidget(self.scrollWidget)
        return self.scroll

    def addBottomButtons(self):

        self.bottomBtns = QHBoxLayout()
        self.bottomBtns.setAlignment(Qt.AlignLeft)
        qid = QWidget()
        qid.setLayout(self.bottomBtns)

        closeButton = self.createSelectorButton(iconImg=CLOSE_ICON,
                                                tooltip="Close window",
                                                callback=self.close)

        hideButton = self.createSelectorButton(iconImg=WIN1_ICON,
                                               tooltip="Hide Window",
                                               callback=self._toggleDock)

        dockButton = self.createSelectorButton(iconImg=WIN2_ICON,
                                               tooltip="Dock Window",
                                               callback=self._toggleFloat)

        floatButton = self.createSelectorButton(iconImg=WIN3_ICON,
                                                tooltip="Float Window",
                                                callback=self._toggleFloat)

        self.bottomBtns.addWidget(closeButton)
        self.bottomBtns.addWidget(hideButton)
        self.bottomBtns.addWidget(floatButton)

        self.isDockedHidden = False
        self.isFloating = False

        return qid

    def _showAllAnimPage(self):
        ip_address = self.getRobotIpAddress()
        url = LIST_ALL_ANIMS_CMD.format(ip_address, ANIM_PORT)
        try:
            webbrowser.open(url)
        except:
            cmds.warning("Unable to display list of all animations installed on robot")

    def _toggleFloat(self):
        self.isFloating = not cmds.workspaceControl(_globalDockControl, query=True, floating=True)
        cmds.workspaceControl(_globalDockControl, edit=True, floating=self.isFloating)
        if self.isFloating:
            # self.toggleFloatButton.setText('Dock Widget')
            pass
        else:
            # self.toggleFloatButton.setText('Float Widget')
            # Searches for MacBlast, ChannelBox then Attr editor and finally the main window to dock to
            for dw in DOCKING_WINDOW:
                if cmds.workspaceControl(dw, exists=True) and cmds.workspaceControl(dw, q=True, visible=True):
                    cmds.workspaceControl(_globalDockControl, edit=True, tabToControl=[dw, -1])
                    cmds.workspaceControl(_globalDockControl, edit=True, restore=True)
                    break
            else:
                cmds.workspaceControl(_globalDockControl, edit=True, dockToMainWindow=('right', 1))

    def _toggleDock(self):
        if self.isFloating:
            self._toggleFloat()
        if cmds.workspaceControl(_globalDockControl, query=True, collapse=True):
            for dw in DOCKING_WINDOW:
                if cmds.workspaceControl(dw, exists=True):
                    cmds.workspaceControl(_globalDockControl, edit=True, tabToControl=[dw, -1])
                    break
            else:
                cmds.workspaceControl(_globalDockControl, edit=True, dockToMainWindow=('right', 1))
        self.isDockedHidden = not cmds.workspaceControl(_globalDockControl, query=True, collapse=True)
        cmds.workspaceControl(_globalDockControl, edit=True, collapse=self.isDockedHidden)

    def update_ping_button_text(self):
        ip_address = self.getRobotIpAddress()
        try:
            pingable = is_pingable(ip_address)
        except:
            text = "unknown"
        else:
            if pingable is None:
                text = "unknown"
            elif pingable:
                text = "online"
            else:
                text = "offline"
        self.statusLineedit.setText('Ping:[{0}] {1}'.format(ip_address, text))

    def _openEngineWebpage(self):
        ipAddress = self.getRobotIpAddress()
        url = 'http://{0}:{1}'.format(ipAddress, ENGINE_PORT)
        webbrowser.open(url)

    def _openAnimWebpage(self):
        ipAddress = self.getRobotIpAddress()
        url = 'http://{0}:{1}'.format(ipAddress, ANIM_PORT)
        webbrowser.open(url)

    def addAnimToSequence(self):
        anim = AnimToPlay(self.scrollWidget)
        self.animWidgets.append(anim)
        self.scrollLayout.addWidget(anim.ui)
        anim.ui.setMinimumSize(380, 120)
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
                # cmds.warning(str(err))
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

    def _enablePlayButton(self):
        # self.setBtn.setEnabled(True)
        pass

    def doPlayAnims(self, ignoreCliffs=ANIM_IGNORE_CLIFFS_FLAG):
        now = time.time()
        # self.setBtn.setEnabled(False)
        waitForAnim(robotIpAddress=self.getRobotIpAddress())
        # self.setBtn.setEnabled(True)
        QApplication.processEvents()
        # enableButton = QTimer.singleShot(BUTTON_WAIT, self._enablePlayButton)

        self.lastPlayButtonPress = now
        # The following is a requirement if we only/mostly want to play locally exported animations.
        # If we use this tool to play animations that are already built into the game, we can get
        # rid of this and the subsequent logic for querying and passing along the animation files.
        try:
            exportPath = get_export_path()
        except ValueError, e:
            self.statusLineedit.setText(str(e))
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
            animClips.append((animClip, numLoops))
            if not animFile:
                missingAnimFiles.append(animClip)
            elif animFile not in animFiles:
                animFiles.append(animFile)
        if not animClips:
            msg = "No animation specified to play"
            print msg,
            self.statusLineedit.setText(msg)
            qApp.processEvents()
            return None

        robotVolume = self.robotVolume.currentText()
        robotVolume = int(robotVolume)

        # ignoreCliffs = _getCheckState(self.statusWidget.ui.ignoreCliffs)
        # connectCubes = _getCheckState(self.statusWidget.ui.connectCube)
        connectCubes = None

        msg = "Playing animations: "
        for animClip, numLoops in animClips:
            msg += "%s (%s), " % (animClip, numLoops)
        msg = msg.strip()
        msg = msg.rstrip(',')
        if missingAnimFiles:
            cmds.warning("The following animations will be played from build since no local "
                         "animation data was found: %s" % ', '.join(missingAnimFiles))
        self.statusLineedit.setText(msg)
        qApp.processEvents()
        ipAddress = self.getRobotIpAddress()
        rgbFace = self.rgbCheckbox.checkState() == Qt.CheckState.Checked
        display_msg = play_anim_clips(ipAddress, animClips, animFiles, robotVolume, ignoreCliffs, connectCubes,
                                      exportPath, robotStatusLabel=self.statusLineedit, rgbFace=rgbFace)
        if display_msg:
            self.statusLineedit.setText(display_msg)

    def close(self):
        _deleteScriptJob()
        try:
            cmds.deleteUI("PreviewSettings")
        except:
            pass

    def _getBatteryLevel(self):
        ipAddress = self.getRobotIpAddress()
        self.statusLineedit.setText("Checking battery at {0}...".format(ipAddress))
        QApplication.processEvents()
        r = requests.get(BATTERY_STATS_CMD.format(ipAddress), timeout=0.5)
        batteryLevel = r.content.split(os.linesep)[0]
        # self.batteryLevelButton.setText("Battery V:{0}".format(batteryLevel))
        batteryLevel = float(batteryLevel)

        if batteryLevel < 3.7:
            # self.batteryLevelButton.setStyleSheet('QPushButton { color: rgb(255, 0, 0) }')
            self.statusLineedit.setText("Battery V:{0}".format(batteryLevel))
        elif batteryLevel < 4.0:
            # self.batteryLevelButton.setStyleSheet(
            # 'QPushButton { color: rgb(255, 236, 94) }')
            self.statusLineedit.setText("Battery V:{0}".format(batteryLevel))
        else:
            # self.batteryLevelButton.setStyleSheet(
            # 'QPushButton {color: rgb(255,255,255); }')
            self.statusLineedit.setText("Battery V:{0}".format(batteryLevel))

    def _changeVolume(self):
        # this is getting called on load with an invalid url so make sure its valid
        vol = int(self.robotVolume.currentText())
        ipAddress = self.getRobotIpAddress()

        if ipAddress is None or vol is None:
            return
        cmd1 = VOLUME_CMD1.format(ipAddress, ENGINE_PORT, vol)
        cmd2 = VOLUME_CMD2.format(ipAddress, ENGINE_PORT)
        try:
            r1 = requests.post(cmd1, timeout=SHORT_TIMEOUT)
            r2 = requests.post(cmd2, timeout=SHORT_TIMEOUT)
        except:
            cmds.warning("Failed to change volume: {0}".format(cmd1))
        else:
            if r1.status_code == 200:  # http OK
                print("volume changed to {0}.".format(vol))

    def getRobotIpAddress(self, ipAddress=ROBOT_IP_ADDRESS):
        robotID = self.robotID.text().strip()
        try:
            a, b, c, d = robotID.split('.')
            int(a)
            int(b)
            int(c)
            int(d)
        except (TypeError, ValueError):
            self.robotIpAddress = str(cmds.optionVar(q='ROBOT_IP_ADDRESS'))
            if self.robotIpAddress:
                return self.robotIpAddress
            displayMsg = "Provide four integer values for the robot's IP address (X.X.X.X)"
            cmds.warning(displayMsg)
            self.statusLineedit.setText(displayMsg)
            return None
        vals = robotID.split('.')
        self.robotIpAddress = ipAddress % (vals[0], vals[1], vals[2], vals[3])

        # remember the setting between maya sessions
        cmds.optionVar(sv=('ROBOT_IP_ADDRESS', self.robotIpAddress))
        return self.robotIpAddress

    def doConnect(self, connectScript=ROBOT_DEPLOY_SCRIPT):
        ipAddress = self.getRobotIpAddress()
        if ipAddress:
            connectScript += " -connect " + ipAddress
            self._updateConnection(connectScript)

    def doDisconnect(self, connectScript=ROBOT_DEPLOY_SCRIPT):
        connectScript += " -disconnect"
        self._updateConnection(connectScript)

    def _updateConnection(self, connectCmd):
        if not self.tools_dir:
            self.tools_dir = get_tools_dir()
            if not self.tools_dir:
                return None
        status, stdout, stderr = self.runCommandWrapper(connectCmd)
        if PUBLICKEY_MSG in stderr:
            cmds.warning("Public key error; try 'Get Public Key' in the context menu to fix this")

    def doRestart(self, restartScript=ROBOT_DEPLOY_SCRIPT):
        ipAddress = self.getRobotIpAddress()
        if ipAddress:
            restartScript += " -restart " + ipAddress
            self._updateConnection(restartScript)

    def _prepInstall(self, installMsg):
        install = self.alertUserInstall(installMsg)
        if not install:
            msg = "Installation aborted"
            print msg,
            self.statusLineedit.setText(msg)
            return False
        if not self.tools_dir:
            self.tools_dir = get_tools_dir()
            if not self.tools_dir:
                return False
        return True

    def doInstallRobot(self, installScript=ROBOT_DEPLOY_SCRIPT):
        ipAddress = self.getRobotIpAddress()
        if ipAddress:
            installScript += " -install_robot " + ipAddress
            installMsg = "software on robot " + ipAddress
            self._install(installScript, installMsg)

    def doRefreshRobot(self, refreshScript=ROBOT_DEPLOY_SCRIPT):
        ipAddress = self.getRobotIpAddress()
        if ipAddress:
            refreshScript += " -refresh_robot " + ipAddress
            refreshMsg = "assets on robot " + ipAddress
            self._install(refreshScript, refreshMsg)

    def doUpdateFace(self, funcCallUrl=ROBOT_ANIM_FUNC_CALL_URL, varSetUrl=ROBOT_ANIM_VAR_SET_URL):
        """
        This function will read the CONSOLE_FUNCTIONS list from the
        console_var_settings.py file and execute those console functions
        on the robot. It will also read the CONSOLE_VAR_VALUES dictionary
        from that file and set those console variable/values on the robot.
        See VIC-1445 for additional details.
        """
        import console_var_settings
        reload(console_var_settings)
        ipAddress = self.getRobotIpAddress()
        for consoleFunc in console_var_settings.CONSOLE_FUNCTIONS:
            thisUrl = funcCallUrl % (ipAddress, consoleFunc)
            try:
                r = requests.post(thisUrl, timeout=5.0)
            except EnvironmentError, e:
                display_msg = "Failed to call '%s' function because: %s" % (consoleFunc, e)
                cmds.warning(display_msg)
        for var, val in console_var_settings.CONSOLE_VAR_VALUES.items():
            thisUrl = varSetUrl % (ipAddress, var, val)
            print(thisUrl)
            try:
                r = requests.post(thisUrl, timeout=5.0)
            except EnvironmentError, e:
                display_msg = "Failed to set '%s' variable to '%s' because: %s" % (var, val, e)
                cmds.warning(display_msg)

    def _install(self, installCmd, installMsg):
        if not self._prepInstall(installMsg):
            return None
        inProgressMsg = "Installing %s..." % installMsg
        print inProgressMsg,
        self.statusLineedit.setText(inProgressMsg)
        qApp.processEvents()
        status, stdout, stderr = self.runCommandWrapper(installCmd)
        if status == 0:
            completedMsg = "Installation of %s completed" % installMsg
            print completedMsg,
            self.statusLineedit.setText(completedMsg)

    def alertUserInstall(self, installMsg):
        """
        Use a message box to confirm installation.
        """
        reply = QMessageBox.question(self, "Message",
                                     "Install %s?" % installMsg,
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        return reply == QMessageBox.Yes

    def runCommandWrapper(self, cmd, shell=False):
        status, stdout, stderr, display_msg = run_command_wrapper(cmd, self.tools_dir, shell)
        if display_msg:
            self.statusLineedit.setText(display_msg)
        return (status, stdout, stderr)


def _getCheckState(checkBox):
    state = checkBox.checkState()
    if state == Qt.CheckState.Unchecked:
        return False
    elif state == Qt.CheckState.Checked:
        return True


def waitForAnim(robotStatusLabel=None, robotIpAddress=None, pollTimeout=0.1):
    if robotStatusLabel:
        # TODO this is not getting set
        robotStatusLabel.setText('starting playback')
        QApplication.processEvents()

    url = SHOW_CURRENT_ANIM_CMD.format(robotIpAddress, ANIM_PORT)
    startTime = time.time()
    # 300 loops as a failsafe timeout
    for i in range(300):
        queryTime = time.time()
        r = requests.post(url, timeout=PING_TIMEOUT_SEC)
        endTime = time.time()
        duration = endTime - queryTime
        time.sleep(pollTimeout)
        QApplication.processEvents()
        if _globalAbortAnim:
            break
        if 'anim' in r.text and SLEEP_ANIM_CLIP not in r.text:
            clip = r.text.split('anim_')[1]
            clip = clip.split('</html>')[0].strip()
            if robotStatusLabel:
                robotStatusLabel.setText(clip + ' ' + str(i))
        else:
            if robotStatusLabel:
                robotStatusLabel.setText('done')
                QApplication.processEvents()
            return


class AnimToPlay(QWidget):
    def __init__(self, parent, *args, **kwargs):
        super(AnimToPlay, self).__init__(*args, **kwargs)
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


previewSettings = None


def main():
    try:
        cmds.deleteUI(THIS_WIN_TITLE)
    except:
        pass
    global _globalPreviewUI, _globalDockControl
    ui, dockWidget, _globalDockControl = Dock(PreviewSettings, width=320, winTitle=THIS_WIN_TITLE)
    ui.setObjectName(THIS_WIN_TITLE)
    ui.show()
    _globalPreviewUI = ui
    return ui


# this sets up a scriptJob to update the animation list dropdown when a new file is opened
_createScriptJob()


if __name__ == '__main__':
    main()


