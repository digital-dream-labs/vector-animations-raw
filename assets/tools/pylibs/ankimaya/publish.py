"""
This is a publish script for the Anki animators and audio
designers that update animation data in Maya.

This script runs through a list of steps that help validate
the data and/or peform operations on it. Those list of steps
are defined in the STEPS list below, where each step has a
name and corresponding function for that step.

Author: Chris Rogers
Copyright: Anki, Inc. 2018
"""

from ankiutils.svn_tools import ROOT_URL, SVN_CRED


# These are the steps that are run, in this order, to publish animation data.
# The pairs in this list are (name of step, function to execute for step)
STEPS = [('File is named', '_validateSceneName', 'This checks that the current Maya scene has a name.'),
         ('File is saved', '_checkFileIsSaved', 'This checks to see if the current Maya scene needs to be saved.\n'
                                                'If it is not saved, save the file and publish again.'),
         ('SVN available', '_checkSvnStatus', 'This checks to see if the SVN server {0} is reachable.'.format(ROOT_URL)),
         ('File is locked', '_checkSvnLockOnFile', 'This will lock the current Maya scene file in SVN.'),
         ('Has comment', '_confirmComment', 'This step requires the user to enter some comment that is\n'
                                            'different from the default comment.'),
         ('Do export', '_exportAnimation', 'This will export animation data for robot from this Maya scene file.'),
         ('Do svn commit', '_confirmCommit', 'This will actually commit the Maya and tar file in SVN.'),
         ('Unlock file', '_unlockMayaFile', 'This will unlock the Maya file after the commit step.'),
         ('Shotgun', '_updateShotgun', 'This will update Shotgun with the latest commit info.')]


import os
import time
import webbrowser
from pprint import pprint

from ankiutils.svn_tools import add_svn_file, check_file_in_svn, commit_svn_file, is_up
from ankiutils.svn_tools import unlock_svn_file, check_svn_file_lock, check_for_user_match
from ankiutils.svn_tools import check_file_never_committed, lock_svn_file
from ankishotgun import anim_data
from ankimaya import game_exporter
from ankimaya.export_for_robot import export_robot_anim

from maya import cmds

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


TITLE = 'Anki Animation Publisher'
TITLE_STYLE = "QLabel { font-size: 15px;  border: 1px solid rgba(188, 188, 188, 250); } "
TITLE_STYLE += "QSpinBox { color: rgb(50, 50, 50); font-size: 11px; background-color: rgba(255, 188, 20, 50); }"

DEFAULT_COMMENT = 'Enter a useful commit message here!'

JIRA_URL = 'https://ankiinc.atlassian.net/browse/'

DATE_FORMAT = "%H:%M:%S %a %m-%d-%Y"


# Global variable
_dockControl = None


def _killScriptJobs():
    """
    Search existing scriptjobs for these 2 specific job names and delete them
    """
    for j in cmds.scriptJob(lj=True):
        if '_getSceneName' in j or '_newSceneScriptJob' in j:
            id = int(j.split(':')[0])
            cmds.scriptJob(kill=id)


def _checkFileExists(filename):
    ex = os.path.exists(filename)
    return ex


class StepWidget(QWidget):
    """
    This widget is for 1 step,
    it has a label for the description
    2 labels with 'fail' and 'pass' that represent whether the step passed or failed
    1 checkbox to determine whether or not to run this step
    """

    def __init__(self, *args, **kwargs):
        super(StepWidget, self).__init__(*args, **kwargs)
        self.step = kwargs.get('step', 'label')
        self.status = 'stop'
        self.initUI()
        self.setReady()

    def initUI(self):
        lo = QHBoxLayout()
        lo.setAlignment(Qt.AlignRight)
        self.stepLabel = QLabel(str(self.step))
        self.stepLabel.setFixedWidth(90)
        #self.stepLabel.setToolTip('Name of step')
        self.redLabel = QLabel('fail')
        self.redLabel.setStyleSheet("background-color: red")
        self.redLabel.setFixedWidth(28)
        self.greenLabel = QLabel('pass')
        self.greenLabel.setFixedWidth(28)
        self.greenLabel.setStyleSheet("background-color: green")
        tt = 'Grey means this test has not run'
        tt += os.linesep + 'Black means it is running'
        tt += os.linesep + 'Green means it passed'
        tt += os.linesep + 'Red means it failed.'
        self.greenLabel.setToolTip(tt)
        self.redLabel.setToolTip(tt)
        self.setLayout(lo)
        lo.addWidget(self.stepLabel)
        lo.addWidget(self.redLabel)
        lo.addWidget(self.greenLabel)
        self.checkBox = QCheckBox()
        self.checkBox.setToolTip('Check this to run the test, uncheck to skip the test.')
        self.checkBox.setFixedWidth(28)
        lo.addWidget(self.checkBox)
        self.setFixedHeight(36)
        self.show()

    def setReady(self, doCheckbox=True):
        self.status = 'ready'
        self.greenLabel.setStyleSheet("background-color: grey")
        self.redLabel.setStyleSheet("background-color: grey")
        if doCheckbox:
            self.checkBox.setChecked(True)
        # QApplication.processEvents()

    def setStep(self, step):
        if not step:
            return
        self.stepLabel.setText(step)
        self.step = step
        QApplication.processEvents()

    def setRunning(self):
        self.status = 'running'
        self.greenLabel.setStyleSheet("background-color: black")
        self.redLabel.setStyleSheet("background-color: black")
        QApplication.processEvents()

    def setFail(self):
        self.status = 'stop'
        self.greenLabel.setStyleSheet("background-color: grey")
        self.redLabel.setStyleSheet("background-color: red")
        QApplication.processEvents()

    def setPass(self):
        self.status = 'stop'
        self.greenLabel.setStyleSheet("background-color: green")
        self.redLabel.setStyleSheet("background-color: grey")
        QApplication.processEvents()


class PublishWidget(QWidget):
    def __init__(self, *args, **kwargs):
        super(PublishWidget, self).__init__(*args, **kwargs)
        self.steps = STEPS
        self.stepWidgets = []
        self.initUI()
        self.sceneName = None
        self.outputFiles = None
        self.comment = None
        self.mayaFileRev = None
        self.tarFileRev = None
        self.log = []
        self.tarFile = None
        self.exportTime = None
        self._startScriptJob()

    def _startScriptJob(self):
        """Scriptjob to update the name of the file if it saved"""
        _killScriptJobs()
        cmds.scriptJob(e=['SceneSaved', self._getSceneName], killWithScene=True)
        cmds.scriptJob(e=['SceneOpened', self._newSceneScriptJob])

    def initUI(self):
        loNo = QVBoxLayout()
        self.setLayout(loNo)
        tab1 = QTabWidget()
        loNo.addWidget(tab1)

        self.title = QLabel(TITLE)
        self.title.setStyleSheet(TITLE_STYLE)
        self.title.setAlignment(Qt.AlignHCenter)
        self.title.setContentsMargins(0, 10, 0, 10)
        self.sceneNameLabel = QLabel('Scene Name:')
        self.sceneNameLabel.setToolTip(
            'This is the maya file that is currently loaded with its clips listed below.')
        self.copyAnimClipsButton = QPushButton('copy')
        self.copyAnimClipsButton.setFixedWidth(60)

        sceneLabelLO = QHBoxLayout()
        sceneLabelLO.addWidget(self.sceneNameLabel)
        sceneLabelLO.addWidget(self.copyAnimClipsButton)
        self.copyAnimClipsButton.setToolTip('Copy selected clips to the clipboard.')
        self.copyAnimClipsButton.clicked.connect(self._copyToClipboard_clipList)
        self.publishButton = QPushButton('Publish')
        self.publishButton.setToolTip('This button runs through the steps listed below.')
        self.cancelButton = QPushButton('Close')

        self.animClipsTree = QTreeWidget()
        self.animClipsTree.setSelectionMode(QAbstractItemView.MultiSelection)
        self.animClipsTree.setToolTip(
            'This is the list of animation clips present\nin the scene (same as GameExporter)')
        self.commitMessage = QPlainTextEdit(DEFAULT_COMMENT)
        self.commitMessage.setFixedHeight(220)

        policy = QSizePolicy()
        policy.setVerticalStretch(0)
        wid = QWidget()
        wlo = QVBoxLayout()
        wlo.setContentsMargins(0, 0, 0, 0)
        wid.setLayout(wlo)
        owid = QWidget()
        olo = QVBoxLayout()
        owid.setLayout(olo)
        olo.setAlignment(Qt.AlignTop)
        olo.addWidget(QLabel("Output Files"))
        b = QPushButton('Copy all or selected items to clipboard')
        b.clicked.connect(self._copyToClipboard_outputList)
        olo.addWidget(b)

        self.outputFilesTree = QTreeWidget()
        self.outputFilesTree.setHeaderLabels(['rev', 'path', 'time'])
        self.outputFilesTree.setSelectionMode(QAbstractItemView.MultiSelection)

        olo.addWidget(self.outputFilesTree)
        self.logWidget = QTextEdit()

        tab1.addTab(wid, 'Publish')
        tab1.addTab(owid, 'Output')
        tab1.addTab(self.logWidget, 'Log')
        jiraLo = QHBoxLayout()
        jiraLo.setAlignment(Qt.AlignRight)
        jiraLabel = QLabel('Jira Ticket:')
        self.jiraLineEdit = QLineEdit()
        self.jiraLineEdit.setToolTip('Enter a valid JIRA number here, such as "VIC-XXXX" or "COZMO-XXXXX"')
        self.jiraLineEdit.setFixedWidth(120)
        jiraLabel.setAlignment(Qt.AlignRight)
        jiraButton = QPushButton('Open in webbrowser')
        jiraButton.setToolTip(
            'If there is a valid JIRA ticket specified (like "VIC-6767"),\nthis will open it in a web browser.')
        jiraButton.clicked.connect(self._openJiraTicket)
        jiraLo.addWidget(jiraLabel)
        jiraLo.addWidget(self.jiraLineEdit)
        jiraLo.addWidget(jiraButton)
        wlo.addWidget(self.title)
        wlo.addLayout(sceneLabelLO)
        #wlo.addWidget(self.sceneNameLabel)
        wlo.addWidget(self.animClipsTree)
        wlo.addWidget(self.publishButton)
        wlo.addLayout(jiraLo)

        sidebysideLo = QHBoxLayout()
        sidebysideLo.setAlignment(Qt.AlignTop)
        wlo.addLayout(sidebysideLo)
        steplo = QVBoxLayout()
        sidebysideLo.addWidget(self.commitMessage)
        self.commitMessage.setToolTip(
            'This is the SVN commit message. You should input\nsomething useful that describes what changed.')
        sidebysideLo.addLayout(steplo)
        sidebysideLo.setAlignment(Qt.AlignTop)
        for step in self.steps:
            w = StepWidget()
            w.setStep(step[0])
            steplo.addWidget(w)
            w.setToolTip(step[2])
            self.stepWidgets.append(w)

        self.cancelButton.clicked.connect(self.close)
        self.publishButton.clicked.connect(self.runSteps)
        self.animClipsTree.setHeaderLabels(['Clip', 'Start', 'End', 'Length'])
        self._getSceneName()
        self.statusLabel = QLabel("Status: ready")
        wlo.addWidget(self.statusLabel)
        wlo.addWidget(self.cancelButton)

        pwLo = QHBoxLayout()
        pwLo.addWidget(QLabel('Username:'))
        self.usernameLineedit = QLineEdit()
        pwLo.addWidget(self.usernameLineedit)
        pwLo.addWidget(QLabel('Password:'))
        self.passwordLineedit = QLineEdit()
        self.passwordLineedit.setEchoMode(QLineEdit.EchoMode.Password)
        pwLo.addWidget(self.passwordLineedit)
        wlo.addLayout(pwLo)

        self.show()

    def _copyToClipboard_clipList(self):
        text = ''
        items = self.animClipsTree.selectedItems()
        if len(items) == 0:
            items = []
            for i in range(self.animClipsTree.topLevelItemCount()):
                items.append(self.animClipsTree.topLevelItem(i))
        for z in items:
            text += z.text(0).rstrip() + " "
            text += z.text(1).rstrip() + "-"
            text += z.text(2).rstrip() + " "
            text += z.text(3) + os.linesep
        QApplication.clipboard().setText(text)

    def _copyToClipboard_outputList(self):
        text = ''
        items = self.outputFilesTree.selectedItems()
        if len(items) == 0:
            items = []
            for i in range(self.outputFilesTree.topLevelItemCount()):
                items.append(self.outputFilesTree.topLevelItem(i))
        for z in items:
            text += z.text(0) + " "
            text += z.text(1) + " "
            text += z.text(2) + os.linesep
        QApplication.clipboard().setText(text)

    def _setStatus(self, msg):
        print(msg)
        self.statusLabel.setText(msg)
        self.log.append(msg)
        QApplication.processEvents()

    def runSteps(self):
        try:
            self._setAllToReady()
            self._setStatus("Starting {0} at {1}".format(os.path.basename(self.mayaFile),
                                                         time.strftime(DATE_FORMAT, time.gmtime())))
            for idx in range(len(self.steps)):
                stepName, stepFunc, toolTip = self.steps[idx]
                eval("self.{0}({1})".format(stepFunc, idx))
            self._setStatus("Finished {0} at {1}".format(os.path.basename(self.mayaFile),
                                                         time.strftime(DATE_FORMAT, time.gmtime())))
        finally:
            if self.log:
                print("PUBLISH LOG FOR THIS SESSION:")
                pprint(self.log)
                log = map(str, self.log)
                log = os.linesep.join(log)
                self.logWidget.setText(log)
                self.log = []

    def _unlockMayaFile(self, step):
        if not self.stepWidgets[step].checkBox.isChecked():
            msg = "Skipped unlock after commit"
            self._setStatus(msg)
            return
        self.stepWidgets[step].setRunning()
        #_checkFileExists(self.mayaFile)
        credentials = self._getCredentials()
        try:
            unlock_svn_file(self.mayaFile, credentials=credentials)
        except:
            msg = "Failed to unlock file: {0}".format(os.path.basename(self.mayaFile))
            self._setStatus(msg)
            self.stepWidgets[step].setFail()
            raise IOError(msg)
        else:
            msg = "Unlocked {0} after export".format(os.path.basename(self.mayaFile))
            self._setStatus(msg)
            self.stepWidgets[step].setPass()

    def _openJiraTicket(self, jiraUrl=JIRA_URL):
        ticket = self.jiraLineEdit.text()
        url = "{0}{1}".format(jiraUrl, ticket)
        webbrowser.open(url)

    def _setAllToReady(self):
        for s in self.stepWidgets:
            s.setReady(doCheckbox=False)

    def _newSceneScriptJob(self):
        """
        This gets run when a scene is opened to update the default
        comment and the name of the current scene.
        """
        self.commitMessage.setPlainText(DEFAULT_COMMENT)
        self._getSceneName()

    def _getSceneName(self):
        """
        This looks for the current scene name and sets the label in the UI.
        It also clears and repopulates the clip list
        """
        self.sceneName = cmds.file(query=1, sn=1)
        self.mayaFile = str(self.sceneName)
        try:
            self.sceneNameLabel.setText('Scene Name: {0}'.format(os.path.basename(self.sceneName)))
        except:
            print("Problem setting label for scenename")
        self.animClipsTree.clear()
        self.getClips()

    def _validateSceneName(self, step):
        """
        This very simply checks to see if the current maya scene has a name
        :param step: step index
        """
        if not self.stepWidgets[step].checkBox.isChecked():
            msg = "Skipped validation of scene name"
            self._setStatus(msg)
            return
        msg = "Checking if scene is named"
        self._setStatus(msg)
        self.stepWidgets[step].setRunning()
        self._getSceneName()
        if self.sceneName in [None, '', 'untitled']:
            msg = "Please give the file a name and save it"
            self._setStatus(msg)
            self.stepWidgets[step].setFail()
            raise ValueError(msg)
        else:
            msg = "Scene is named"
            self._setStatus(msg)
            self.stepWidgets[step].setPass()

    def _checkFileIsSaved(self, step):
        if not self.stepWidgets[step].checkBox.isChecked():
            msg = "Skipped validation that file is saved"
            self._setStatus(msg)
            return
        msg = "Checking if file is saved"
        self._setStatus(msg)
        self.stepWidgets[step].setRunning()
        mod = cmds.file(q=1, modified=1)
        if mod:
            msg = "The file is not saved. Please save the file."
            self._setStatus(msg)
            self.stepWidgets[step].setFail()
            raise ValueError(msg)
        else:
            msg = "The file is saved."
            self._setStatus(msg)
            self.stepWidgets[step].setPass()

    def _getFinalComment(self):
        """
        This will add the jira ticket number to the comment
        :return: the comment with the jira ticket added
        """
        comment = self.comment
        jiraTicket = self.jiraLineEdit.text()
        if jiraTicket:
            jiraTicket = jiraTicket.strip()
            if jiraTicket:
                comment = jiraTicket + " : " + comment
        return comment

    def _getCredentials(self):
        """
        If the user has entered a username and password into the
        UI, this will return a string with the credentials
        formatted to be used in an SVN command
        :return: a string with the username and password formatted
                 to be used in an SVN command, or None
        """
        username = self.usernameLineedit.text()
        password = self.passwordLineedit.text()
        if not username or not password:
            return None
        return SVN_CRED.format(username, password)

    def _doCommit(self, step):
        """
        This step checks to see if the file is in svn and adds it if it is not
        It then runs svn commit on exported files
        :param step: index
        """
        if not self.stepWidgets[step].checkBox.isChecked():
            msg = "Skipped commit step"
            self._setStatus(msg)
            return
        msg = "Doing commit..."
        self._setStatus(msg)
        self.stepWidgets[step].setRunning()

        credentials = self._getCredentials()
        if not check_file_in_svn(self.mayaFile):
            add_svn_file(self.mayaFile, credentials=credentials)

        commitComment = self._getFinalComment()

        try:
            self.mayaFileRev = commit_svn_file(self.mayaFile, comment=commitComment, unlock=False,
                                               credentials=credentials)
        except ValueError, e:
            msg = "Failed to commit maya file {0} because: {1}".format(self.mayaFile, e)
            self._setStatus(msg)
            self.stepWidgets[step].setFail()
            raise ValueError(msg)

        # look through output files in outputFilesTree and update their rev number if timestamp matches
        for i in range(self.outputFilesTree.topLevelItemCount()):
            top_item = self.outputFilesTree.topLevelItem(i)
            if top_item.text(1) == os.path.basename(self.mayaFile) and top_item.text(2) == self.exportTime:
                top_item.setText(0, str(self.mayaFileRev))

        for f in self.outputFiles:
            if os.path.splitext(f)[1] == '.tar':
                self.tarFile = f
                if not check_file_in_svn(f, credentials=credentials):
                    add_svn_file(f, credentials=credentials)
                break

        try:
            self.tarFileRev = commit_svn_file(self.tarFile, comment=commitComment, credentials=credentials)
        except ValueError, e:
            msg = "Failed to commit tar file {0} because: {1}".format(self.tarFile, e)
            self._setStatus(msg)
            self.stepWidgets[step].setFail()
            raise ValueError(msg)

        msg = "Commited maya file {0} at {1} ".format(os.path.basename(self.mayaFile), self.mayaFileRev)
        msg += "and corresponding tar file at {0}".format(self.tarFileRev)
        self._setStatus(msg)
        self.stepWidgets[step].setPass()

        # look through output files in outputFilesTree and update their rev number if timestamp matches
        for i in range(self.outputFilesTree.topLevelItemCount()):
            top_item = self.outputFilesTree.topLevelItem(i)
            if top_item.text(1) == os.path.basename(self.tarFile) and top_item.text(2) == self.exportTime:
                top_item.setText(0, str(self.tarFileRev))

    def _updateShotgun(self, step):
        if not self.stepWidgets[step].checkBox.isChecked():
            msg = "Skipped shotgun step."
            self._setStatus(msg)
            return
        self.stepWidgets[step].setRunning()
        try:
            anim_data.main([self.mayaFile, self.tarFile])
        except BaseException, e:
            msg = "Problem while updating Shotgun"
            self._setStatus(msg)
            self.stepWidgets[step].setFail()
            raise
        else:
            msg = "Shotgun updating complete"
            self._setStatus(msg)
            self.stepWidgets[step].setPass()

    def _checkSvnStatus(self, step):
        """
        Checks to see if the SVN server is online
        :param step: index
        """
        if not self.stepWidgets[step].checkBox.isChecked():
            msg = "Skipped check that SVN server is available"
            self._setStatus(msg)
            return
        msg = "Checking that SVN server is available"
        self._setStatus(msg)
        self.stepWidgets[step].setRunning()
        if is_up():
            msg = "SVN server is available for use"
            self._setStatus(msg)
            self.stepWidgets[step].setPass()
        else:
            msg = "SVN server cannot be reached; check your network and VPN connections"
            self._setStatus(msg)
            self.stepWidgets[step].setFail()
            raise EnvironmentError(msg)

    def _checkSvnLockOnFile(self, step, filename=None):
        """
        Checks to see if the file is locked in SVN
        :param step: index of step
        :param filename: file to check
        """
        if not self.stepWidgets[step].checkBox.isChecked():
            msg = "Skipped check file lock"
            self._setStatus(msg)
            return
        if not filename:
            filename = self.mayaFile
        msg = "Checking SVN lock on {0} file".format(os.path.basename(filename))
        self._setStatus(msg)
        self.stepWidgets[step].setRunning()
        credentials = self._getCredentials()
        if not check_file_in_svn(filename, credentials=credentials) or \
                check_file_never_committed(filename, credentials=credentials):
            add_svn_file(filename)
            msg = "No need to lock new {0} file".format(os.path.basename(filename))
            self._setStatus(msg)
            self.stepWidgets[step].setReady(False)
            self.stepWidgets[step].setPass()
            return

        lockOwner = check_svn_file_lock(filename)
        if lockOwner:
            msg = "The {0} file is locked by {1}".format(os.path.basename(filename), lockOwner)
            self._setStatus(msg)
            if check_for_user_match(lockOwner):
                self.stepWidgets[step].setPass()
            else:
                self.stepWidgets[step].setFail()
                raise IOError(msg)
        else:
            msg = "The {0} file is not locked.".format(os.path.basename(filename))
            self._setStatus(msg)
            confirmation = cmds.confirmDialog(title='Confirm SVN File Lock',
                                              message=msg + ' Do you want to lock it?',
                                              button=['Yes', 'No'], defaultButton='Yes',
                                              cancelButton='No', dismissString='No')
            if confirmation == 'Yes':
                lock_svn_file(filename)
                msg = "File {0} is locked.".format(os.path.basename(filename))
                self._setStatus(msg)
                self.stepWidgets[step].setPass()
            else:
                msg = "File {0} is not locked.".format(os.path.basename(filename))
                self._setStatus(msg)
                self.stepWidgets[step].setFail()
                raise IOError(msg)

    def _confirmComment(self, step):
        """
        Checks to see if the user entered a comment in the UI
        :param step:
        """
        if not self.stepWidgets[step].checkBox.isChecked():
            msg = "Skipped confirm comment"
            self._setStatus(msg)
            return
        self.stepWidgets[step].setRunning()
        self.comment = self.commitMessage.toPlainText()
        if self.comment is None or len(self.comment) < 2 or self.comment == DEFAULT_COMMENT:
            msg = "You must enter a comment where it says '{0}'".format(DEFAULT_COMMENT)
            self._setStatus(msg)
            self.stepWidgets[step].setFail()
            raise ValueError(msg)
        else:
            msg = "Found valid comment: {0}".format(self._getFinalComment())
            self._setStatus(msg)
            self.stepWidgets[step].setPass()

    def _confirmCommit(self, step):
        """
        Shows the user a confirmation window before commiting file to SVN
        :param step:
        """
        if not self.stepWidgets[step].checkBox.isChecked():
            msg = "Skipped commit step"
            self._setStatus(msg)
            return

        confirmation = cmds.confirmDialog(title='Confirm SVN Commit',
                                          message='Are you sure you want to commit this to SVN?',
                                          button=['Yes', 'No'], defaultButton='Yes',
                                          cancelButton='No', dismissString='No')
        if confirmation == 'Yes':
            self._doCommit(step)
        else:
            msg = "Commit step aborted"
            self._setStatus(msg)
            self.stepWidgets[step].setFail()
            raise ValueError(msg)

    def _exportAnimation(self, step):
        """
        This will export the animations files using export_robot_anim
        :param step:
        """
        self.tarFile = None
        if not self.stepWidgets[step].checkBox.isChecked():
            msg = "Skipped export step"
            self._setStatus(msg)
            return
        msg = "Exporting animation data..."
        self._setStatus(msg)
        self.stepWidgets[step].setRunning()
        cmds.cycleCheck(e=False)
        self.outputFiles = export_robot_anim(all_clips=True)
        self.exportTime = time.strftime(DATE_FORMAT, time.gmtime())
        for f in self.outputFiles:
            if os.path.splitext(f)[1] == '.tar':
                self.tarFile = f
                break
        if not self.outputFiles or self.tarFile is None:
            msg = "Not all expected output files from exporter were found"
            self._setStatus(msg)
            self.stepWidgets[step].setFail()
            raise ValueError(msg)
        else:
            msg = "{0} files were generated.".format(len(self.outputFiles))
            self.log.append(self.outputFiles)
            i = QTreeWidgetItem(self.outputFilesTree)
            i.setText(1, os.path.basename(self.mayaFile))
            i.setText(2, self.exportTime)
            for of in self.outputFiles:
                i = QTreeWidgetItem(self.outputFilesTree)
                i.setText(1, os.path.basename(of))
                i.setText(2, self.exportTime)
            self._setStatus(msg)
            self.stepWidgets[step].setPass()

    def close(self):
        _killScriptJobs()
        cmds.deleteUI(_dockControl)

    def getClips(self):
        """
        Uses game exporter.get_clip_info to get the clips in the scene
        and populates a treewidget with the data
        """
        clips = game_exporter.get_clip_info('', include_all=True)[2]
        for c in clips:
            item = QTreeWidgetItem(self.animClipsTree)
            item.setText(0, str((c['clip_name'])))
            item.setText(1, str(int(c['clip_start'])))
            item.setText(2, str(int(c['clip_end'])))
            start = c['clip_start']
            end = c['clip_end']
            duration = end - start
            item.setText(3, str(int(duration)))
        for i in range(4):
            self.animClipsTree.resizeColumnToContents(i)


def main():
    global _dockControl
    try:
        cmds.deleteUI('Publish')
    except:
        pass
    winTitle = 'Publish'
    ui, dockWidget, _dockControl = Dock(PublishWidget, width=320, winTitle=winTitle)
    ui.setObjectName(winTitle)
    return ui


if __name__ == '__main__':
    main()


