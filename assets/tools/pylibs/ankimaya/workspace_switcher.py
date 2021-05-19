import os
import sys
import maya.cmds as cmds
import subprocess
import importlib
from window_docker import Dock

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

ROBOT_PROJECT = 'victor-animation'

HOME_DIR = os.getenv("HOME")
REMOTE_CHECKOUT = os.path.join(os.path.dirname(__file__), '../../other/remote_checkout.sh')

# Only reload the plugin from workspace so we dont have to deal with maya_plugin_path
PLUGIN = os.path.join(os.environ['HOME'], 'workspace', ROBOT_PROJECT, 'tools', 'plugins', 'AnkiMenu.py')

# Only the workspace gets updated via update
SVN_UPDATE_CMD = 'cd {0}/{1}; svn update;'.format(os.environ['HOME'], 'workspace', ROBOT_PROJECT)
ANKI_PACKAGES = ['ankimaya', 'ankiutils', 'ankishotgun', 'ankisdk']
MAYA_ENV_FILE = env_path = os.path.join(HOME_DIR, "Library", "Preferences", "Autodesk", "maya", "2018",
                                        "Maya.env")
VERBOSE = True
stdout_pipe = subprocess.PIPE
stderr_pipe = subprocess.PIPE


def run_command_core(cmd, stdout_pipe=stdout_pipe, stderr_pipe=stderr_pipe, shell=False, split=False):
    if VERBOSE:
        print "CMD=", cmd
    if split:
        cmd = cmd.split()
    try:
        p = subprocess.Popen(cmd, stdout=stdout_pipe, stderr=stderr_pipe, shell=shell)
    except OSError as err:
        print("Failed to execute '%s' because: %s" % (cmd, err))
        return (None, None, None)
    (stdout, stderr) = p.communicate()
    status = p.poll()
    if VERBOSE:
        print "cmd:status: ", status
        print "cmd:stdout: ", stdout
        print "cmd:stderr: ", stderr
    return (status, stdout, stderr)


def switch_workspace():
    print switch_sys_path()
    print switch_env()


def switch_sys_path():
    current_state = ""

    sys_paths = sys.path
    old_paths = []
    new_paths = []

    for sys_path in sys_paths:
        # Switch to Dev
        if "workspace_prod" in sys_path:
            old_paths.append(sys_path)
            new_path = sys_path.replace("workspace_prod", "workspace")
            new_paths.append(new_path)
            current_state = "dev"

        # Switch to Prod(uction)
        elif "workspace" in sys_path:
            old_paths.append(sys_path)
            new_path = sys_path.replace("workspace", "workspace_prod")
            new_paths.append(new_path)
            current_state = "prod"

    for old_path in old_paths:
        if old_path in sys.path:
            sys.path.remove(old_path)

    for new_path in new_paths:
        sys.path.append(new_path)

    return current_state


def switch_env():
    current_state = ""

    env_file = open(MAYA_ENV_FILE, 'r')
    env_lines = env_file.readlines()
    new_env_lines = []

    for line in env_lines:
        if "SVN_WORKSPACE = $HOME/workspace_prod" in line:
            line = line.replace("workspace_prod", "workspace")
            current_state = "prod"

        elif "SVN_WORKSPACE = $HOME/workspace" in line:
            line = line.replace("workspace", "workspace_prod")
            current_state = "dev"

        if "$HOME/code/victor_dev" in line:
            line = line.replace("$HOME/code/victor_prod", "$HOME/code/victor")

        elif "$HOME/code/victor" in line:
            line = line.replace("$HOME/code/victor", "$HOME/code/victor_prod")

        new_env_lines.append(line)

    env_file.close()
    env_file = open(env_path, 'w')
    env_file.writelines(new_env_lines)
    env_file.close()

    if cmds.pluginInfo(PLUGIN, query=True, loaded=True):
        cmds.unloadPlugin(PLUGIN)
    cmds.loadPlugin(PLUGIN)

    if VERBOSE: print "Wrote out maya.env file"
    return current_state


class WorkspaceSwitchWidget(QWidget):
    def __init__(self, *args, **kwargs):
        super(WorkspaceSwitchWidget, self).__init__(*args, **kwargs)
        self.currentState = None
        self.initUI()

    def initUI(self):
        self.lo = QVBoxLayout()
        self.lo.setAlignment(Qt.AlignTop)
        self.setLayout(self.lo)
        self.stateLabel = QLabel('current state is: {0}'.format(self.currentState))
        self.currentState = self._checkState()
        self.lo.addWidget(self.stateLabel)
        self.checkoutButton = QPushButton('Remote Checkout to Prod Depo (workspace_prod)')
        self.updateButton = QPushButton('Update Dev Repo (workspace)')
        self.lo.addWidget(self.updateButton)
        self.lo.addWidget(self.checkoutButton)
        self.checkoutButton.clicked.connect(self._remoteCheckout)
        self.updateButton.clicked.connect(self._updateSVN)
        self.switchButton = QPushButton('Switch Env')
        self.lo.addWidget(self.switchButton)
        self.switchButton.clicked.connect(self.doSwitch)

        self.closeButton = QPushButton("Cancel")
        self.lo.addWidget(self.closeButton)
        self.closeButton.clicked.connect(self.close)
        self.setFixedWidth(320)
        self.setFixedHeight(320)
        self._checkState()
        self.show()

    def close(self):
        global _dockControl
        print _dockControl
        try:
            cmds.deleteUI(_dockControl)
        except:
            pass

    def _updateSVN(self):
        """This is a barebones svn update for the svn_workspace
        it doesnt report anything except for printing stdout stderr to the script editor"""
        (status, stdout, stderr) = run_command_core(SVN_UPDATE_CMD, shell=True)
        print status
        print stdout
        print stderr

    def _remoteCheckout(self):
        """This is a barebones svn checkout for the svn_workspace
        it doesnt report anything except for printing stdout stderr to the script editor"""
        (status, stdout, stderr) = run_command_core(REMOTE_CHECKOUT, shell=True)
        print status
        print stdout
        print stderr

    def _checkState(self):
        self.currentState = 'dev (workspace)'
        for s in sys.path:
            if 'workspace_prod' in s:
                self.currentState = 'prod (workspace_prod)'
                break
        self.stateLabel.setText('current state is: {0}'.format(self.currentState))
        return self.currentState

    def doSwitch(self):
        switch_workspace()
        self._checkState()

        anki_mods = []
        for m in sys.modules:
            # if this is None, it appears in sys.modules[] but is not a loaded object
            if sys.modules[m] is None:
                continue
            # there are four packages to search for
            for ap in ANKI_PACKAGES:
                if ap in m:
                    break
            # didnt find any of these packages so next sys.module
            else:
                continue

            anki_mods.append(m)
            if VERBOSE: print 'before switch: ', m, sys.modules[m]
        for m in anki_mods:
            del sys.modules[m]
        for m in anki_mods:
            importlib.import_module(m)
            if VERBOSE: print 'after switch: ', m, sys.modules[m]


_dockControl = None


def main():
    try:
        cmds.deleteUI('Workspace Switch')
    except:
        pass
    global _dockControl
    winTitle = 'Workspace Switch'
    ui, dockWidget, _dockControl = Dock(WorkspaceSwitchWidget, width=120, winTitle=winTitle)
    ui.setObjectName(winTitle)
    _globalPreviewUI = ui
    return ui


if __name__ == '__main__':
    main()
