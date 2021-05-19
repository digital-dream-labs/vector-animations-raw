
DISABLE_FILE_LOCK_PROMPT_ENV_VAR = "DISABLE_ANKI_FILE_LOCK_PROMPT"

PROMPT_LOCK_WINDOW_TITLE = "Confirm File Lock or Unlock"
PROMPT_LOCK_MSG = "Lock the {0} file?"
PROMPT_UNLOCK_MSG = "Unlock the {0} file?"

NEEDS_UPDATE_MSG = "{0} file is out of date"
PROMPT_UPDATE_WINDOW_TITLE = "Confirm File Update"
PROMPT_UPDATE_MSG = NEEDS_UPDATE_MSG + ". Update that file now?"
MODIFIED_FILE_WINDOW_TITLE = "File Outdated and Modified"
MODIFIED_FILE_MSG = "{0} file is out of date but has local modifications"


import sys
import os
from maya import cmds
from ankiutils.svn_tools import check_file_in_svn, check_file_never_committed, check_svn_file_lock
from ankiutils.svn_tools import check_for_user_match, lock_svn_file, unlock_svn_file
from ankiutils.svn_tools import update_svn_file, check_svn_file_outdated, check_svn_file_modified


def checkFileStatus(reloadAfterUpdate=True):
    """
    Checks the status of the current scene file in SVN and
    prompts the user to update it if needed.
    """
    sceneFile, shortName = _getSceneFileInfo()
    #print("The current scene file to potentially update is %s" % shortName)
    if sceneFile and shortName:
        if not check_svn_file_outdated(sceneFile):
            # do nothing if a version of this file has NOT been
            # committed since the local version was last updated
            return
        if check_svn_file_modified(sceneFile):
            # warn user if he/she has locally modified a file that is (now) outdated
            cmds.confirmDialog(title=MODIFIED_FILE_WINDOW_TITLE,
                               message=MODIFIED_FILE_MSG.format(shortName),
                               icon="warning")
            cmds.warning(MODIFIED_FILE_MSG.format(shortName))
        else:
            # prompt the user to update the outdated scene file
            confirmation = cmds.confirmDialog(title=PROMPT_UPDATE_WINDOW_TITLE,
                                              message=PROMPT_UPDATE_MSG.format(shortName),
                                              button=['Yes', 'No'], defaultButton='Yes',
                                              cancelButton='No', dismissString='No',
                                              icon="question")
            if confirmation == 'Yes':
                # update the outdated scene file and then reload it
                update_svn_file(sceneFile)
                print("File {0} is now updated".format(shortName))
                if reloadAfterUpdate:
                    cmds.file(sceneFile, open=True, force=True)
            else:
                cmds.warning(NEEDS_UPDATE_MSG.format(shortName))


def getFileLockOwner(filePath=None, warnIfLockedByOtherUser=True):
    """
    Given a file path, return the name of user who has that file
    locked or return None if it is not locked.
    """
    if filePath is None:
        filePath, shortName = _getSceneFileInfo()
    else:
        shortName = os.path.basename(filePath)
    #print("Checking SVN lock on {0} file...".format(shortName))
    if filePath is None:
        return None
    if not check_file_in_svn(filePath) or check_file_never_committed(filePath):
        print("{0} file is new and unlocked".format(shortName))
        return None
    lockOwner = check_svn_file_lock(filePath)
    if lockOwner:
        msg = "The {0} file is locked by {1}".format(shortName, lockOwner)
        print(msg)
        if warnIfLockedByOtherUser and not check_for_user_match(lockOwner):
            cmds.warning(msg)
        return lockOwner
    else:
        print("The {0} file is not locked".format(shortName))
        return None


def _getSceneFileInfo():
    """
    If there is a current scene file and it has previously been
    committed (and thus needs to be locked or unlocked), this
    function returns a 2-item tuple of:
        (sceneFile, shortName)
    else it returns a 2-item tuple of (None, None)
    """
    sceneFile = cmds.file(query=True, sceneName=True)
    if not sceneFile:
        return (None, None)
    shortName = os.path.basename(sceneFile)
    if not check_file_in_svn(sceneFile) or check_file_never_committed(sceneFile):
        print("No need to lock or unlock new {0} file yet".format(shortName))
        return (None, None)
    #print("The current scene file is %s" % shortName)
    return (sceneFile, shortName)


def unlockSceneFile():
    """
    Checks to see if the current scene file is locked in SVN and
    prompts the user to unlock that file if it is current locked
    by that user.
    """
    sceneFile, shortName = _getSceneFileInfo()
    #print("The current scene file to potentially unlock is %s" % shortName)
    if sceneFile and shortName:
        lockOwner = getFileLockOwner(sceneFile)
        if check_for_user_match(lockOwner):
            confirmation = cmds.confirmDialog(title=PROMPT_LOCK_WINDOW_TITLE,
                                              message=PROMPT_UNLOCK_MSG.format(shortName),
                                              button=['Yes', 'No'], defaultButton='Yes',
                                              cancelButton='No', dismissString='No',
                                              icon="question")
            if confirmation == 'Yes':
                unlock_svn_file(sceneFile)
                print("File {0} is now unlocked".format(shortName))


def lockSceneFile():
    """
    Checks to see if the current scene file is locked in SVN and
    prompts the user to lock that file if it is current unlocked.
    """
    sceneFile, shortName = _getSceneFileInfo()
    #print("The current scene file to potentially lock is %s" % shortName)
    if sceneFile and shortName:
        lockOwner = getFileLockOwner(sceneFile)
        if not lockOwner:
            confirmation = cmds.confirmDialog(title=PROMPT_LOCK_WINDOW_TITLE,
                                              message=PROMPT_LOCK_MSG.format(shortName),
                                              button=['Yes', 'No'], defaultButton='No',
                                              cancelButton='No', dismissString='No',
                                              icon="question")
            if confirmation == 'Yes':
                lock_svn_file(sceneFile)
                print("File {0} is now locked".format(shortName))


def openSceneFile(disableFileLockPromptEnvVar=DISABLE_FILE_LOCK_PROMPT_ENV_VAR):
    try:
        checkFileStatus()
    except BaseException, e:
        cmds.warning(str(e).strip())
    if os.getenv(disableFileLockPromptEnvVar) in [None, 0, "0"]:
        try:
            lockSceneFile()
        except BaseException, e:
            cmds.warning(str(e).strip())


