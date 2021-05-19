"""
This module includes some functionality to help package a sequence of
PNG files into a .tar file. It also contains some related functionality
that can be used to help preview PNG images directly on a robot.
"""

DEFAULT_DIRECTORY = "sprites/spriteSequences"

ANIM_DIR_ENV_VAR = "ANKI_ANIM_DIR"

FILE_EXTS = ["*.png", "*.json"]

FILE_BROWSER_FILTER = "sprite data files (%s)" % ' '.join(FILE_EXTS)
FILE_BROWSER_WIN_TITLE  = "Select the PNG files for this sprite sequence..."

PREVIEW_IMAGE_SEQUENCE_FRAME_BUFFER_BTWN_LOOPS = 5
PREVIEW_IMAGE_SEQUENCE_MIN_ANIM_LENGTH_MS = 3000


import os
import sys
import re
import tarfile
import subprocess
import tempfile
import shutil

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

from ankiutils import image_files
import facial_animation
from ankiutils import anim_files
from ankimaya import preview_selector


mayaMainWindowPtr = omui.MQtUtil.mainWindow()
mayaMainWindow = wrapInstance(long(mayaMainWindowPtr), QWidget)


def previewImageSequence(tarFile, animPrefix="test"):
    """
    Given a tar file that contains a sequence of PNG image files,
    this function can be used to:
     (1) generate a simple test animation to trigger that image/sprite
         sequence at the beginning of the animation
     (2) load updated animation assets onto the robot

    This function returns (animName, animFile) for the test animation
    that was generated.
    """
    # Generate a simple test animation to trigger the provided image/sprite sequence at time 0
    exportPath = os.getenv("ANKI_ANIM_EXPORT_PATH")
    if not exportPath:
        raise ValueError("ANKI_ANIM_EXPORT_PATH should be set in the Maya.env file")
    imageSeqName = os.path.splitext(os.path.basename(tarFile))[0]
    frameCount = image_files.get_image_file_count(tarFile)
    animName = animPrefix + "_" + imageSeqName
    animFile = anim_files.get_json_file_for_anim(animName, exportPath, exists=False)
    facial_animation.make_facial_anim(animName, animFile, imageSeqName,
                                      frameCount+PREVIEW_IMAGE_SEQUENCE_FRAME_BUFFER_BTWN_LOOPS,
                                      min_length_ms=PREVIEW_IMAGE_SEQUENCE_MIN_ANIM_LENGTH_MS)

    # Load updated animation assets onto the robot
    ipAddress = os.getenv("ROBOT_IP_ADDRESS")
    if not ipAddress:
        raise ValueError("ROBOT_IP_ADDRESS should be set in the Maya.env file")
    refreshScript = preview_selector.ROBOT_DEPLOY_SCRIPT + " -refresh_robot " + ipAddress
    status, stdout, stderr, display_msg = preview_selector.run_command_wrapper(refreshScript)

    return (animName, animFile)


def _getDefaultImagesDir():
    workspaceRoot = cmds.workspace(q=True, rd=True)
    fileRules = cmds.workspace(q=True, fileRule=True)
    imagesDir = fileRules[fileRules.index('images')+1]
    imagesDir = os.path.join(workspaceRoot, imagesDir)
    if os.path.isdir(imagesDir):
        return imagesDir
    else:
        return None


def _getDefaultFaceAnimDir(dirName=DEFAULT_DIRECTORY):
    animDir = os.getenv(ANIM_DIR_ENV_VAR)
    if not animDir:
        return None
    faceAnimDir = os.path.join(os.path.dirname(animDir), dirName)
    if os.path.isdir(faceAnimDir):
        return faceAnimDir
    else:
        return None


class SelectPngFilesUI(QWidget):
    def __init__(self, *args, **kwargs):
        super(SelectPngFilesUI,self).__init__(*args, **kwargs)
        self.setParent(mayaMainWindow)
        self.setWindowFlags(Qt.Window)
        self.faceAnimDir = None
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.initUI()

    def checkPngFiles(self, pngFiles):
        numericVals = []
        setName = None
        for pngFile in pngFiles:
            baseName = os.path.basename(pngFile)
            matchObj = re.match(r'(.*)_(\d*).png', baseName)
            if not matchObj:
                raise ValueError("The '%s' file does not fit the expected naming convention "
                                 "of '<text>_<5-digit number>.png'" % baseName)
            numericVals.append(int(matchObj.group(2)))
            if setName is None:
                setName = matchObj.group(1)
            elif setName != matchObj.group(1):
                raise ValueError("All PNG files must be named with the same prefix and should only "
                                 "contain different numerical values. '%s' does not match the "
                                 "expected '%s' prefix." % (baseName, setName))
        numericVals.sort()
        if numericVals[0] != 0:
            msg = "Sequence of PNG files should begin with 00000"
            cmds.warning(msg)
            proceed = cmds.confirmDialog(message=msg, icon="critical", title="PNG packaging error",
                                         button=["Proceed", "Abort"], defaultButton="Abort",
                                         dismissString="Abort")
            if proceed != "Proceed":
                raise ValueError(msg)
        for num in range(numericVals[0], numericVals[-1]):
            if num not in numericVals:
                raise ValueError("'%s' PNG file missing for %s" % (setName, num))
        return setName

    def makeTarFile(self, dataFiles, optimizeImages=True):
        if not dataFiles:
            print("No sprite data files selected for .tar file")
            return None
        pngFiles = []
        otherFiles = []
        allFiles = []
        for dataFile in dataFiles:
            if os.path.splitext(dataFile)[1] in [".png"]:
                pngFiles.append(dataFile)
            else:
                otherFiles.append(dataFile)
        if not pngFiles:
            print("No PNG files selected for .tar file")
            return None
        pngFiles.sort()
        setName = self.checkPngFiles(pngFiles)
        tarFile = setName + ".tar"
        if self.faceAnimDir:
            tarFile = os.path.join(self.faceAnimDir, tarFile)
        if not self.confirmWithUser(tarFile):
            return None
        if optimizeImages:
            tmpDir = tempfile.mkdtemp()
            for pngFile in pngFiles:
                baseName = os.path.basename(pngFile)
                tmpFile = os.path.join(tmpDir, baseName)
                shutil.copyfile(pngFile, tmpFile)
                image_files.optimize_image_file(tmpFile)
                allFiles.append(tmpFile)
        else:
            allFiles = pngFiles
        allFiles += otherFiles
        try:
            tar = tarfile.open(tarFile, 'w')
        except (OSError, IOError), e:
            self.close()
            msg = "Failed to write '%s' file because: %s" % (tarFile, e)
            cmds.warning(msg)
            QMessageBox.critical(self, "Alert", msg)
            return None
        for dataFile in map(os.path.abspath, allFiles):
            tar.add(dataFile, arcname=os.path.basename(dataFile))
        tar.close()
        return tarFile

    def confirmWithUser(self, tarFile):
        """
        Use a message box to confirm creation of new tar file
        """
        if os.path.isfile(tarFile):
            msg = "Update existing '%s' PNG sequence?"
        else:
            msg = "Create new '%s' PNG sequence?"
        reply = QMessageBox.question(self, "Message", msg % tarFile,
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            return True
        else:
            return False

    def initUI(self):

        #self.setGeometry(300, 300, 800, 500)
        self.setWindowTitle(FILE_BROWSER_WIN_TITLE)

        # At the top layer, a grid layout is used to hold buttons and widgets
        self.grid = QGridLayout(self)

        # Use file browser widget to have the user select all the PNG files for this sequence.
        fileBrowser = QFileDialog()
        fileBrowser.setOption(QFileDialog.DontUseNativeDialog)
        self.faceAnimDir = _getDefaultFaceAnimDir()
        self.imagesDir = _getDefaultImagesDir()
        if self.imagesDir:
            fileBrowser.setDirectory(self.imagesDir)
        elif self.faceAnimDir:
            fileBrowser.setDirectory(self.faceAnimDir)
        fileBrowser.setFileMode(QFileDialog.ExistingFiles)
        fileBrowser.setNameFilter(FILE_BROWSER_FILTER)
        self.grid.addWidget(fileBrowser, 0, 0)

        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
        # TODO: Can we use the following instead of forcing the window to always stay on top?
        #self.setProperty("saveWindowPref", True)
        # Along with that setProperty() call, we may need to call setObjectName() to give it a name.

        self.show()
        if fileBrowser.exec_():
            dataFiles = fileBrowser.selectedFiles()
            if dataFiles:
                try:
                    tarFile = self.makeTarFile(dataFiles)
                except ValueError, e:
                    self.close()
                    cmds.warning(str(e))
                    cmds.confirmDialog(message=str(e), icon="critical", title="PNG packaging error")
                else:
                    self.close()
                    if tarFile:
                        msg = "Created %s" % tarFile
                        nextStep = cmds.confirmDialog(message=msg, icon="information",
                                                      title="PNG packaging confirmation",
                                                      button=["OK", "Preview"], defaultButton="OK",
                                                      dismissString="OK")
                        if nextStep == "Preview":
                            previewImageSequence(tarFile)
        self.close()


def main():
    ui = SelectPngFilesUI()
    return ui


if __name__ == '__main__':
    main()


