
DEFAULT_AUDIO_EVENT = "Play__Robot_Vo__Placeholder"

AUDIO_GROUPS_FILE = "audioGroups"

EVENT_NAME_DELIMITER = "__"
PARAMETER_NAME_DELIMITER = ""

ALL_GROUP = "(all)"

AUDIO_NODE_NAME = "x:AnkiAudioNode"
AUDIO_ENUM_ATTR = "WwiseIdEnum"
AUDIO_ENUM_SHORT_NAME = "wwid"

WWISE_PLUGIN_NAME = "AnkiMayaWWisePlugIn"
UPDATE_WWISE_PLUGIN_DATA_CMD = WWISE_PLUGIN_NAME + "_UpdateEventData"
PLAY_AUDIO_EVENT_CMD = WWISE_PLUGIN_NAME + "_PlayAudioEvent"
SET_PARAMETER_CMD = WWISE_PLUGIN_NAME + "_SetParameter"

AUDIO_EVENT_JSON_FILE = "audio_event_info.json"

UPDATE_SCRIPT_IN_GIT_REPO = "tools/audio/UpdateAudioAssets.py"
PY_EMITTER_SCRIPT_IN_GIT_REPO = "victor-clad/tools/message-buffers/emitters/Python_emitter.py"
AUDIO_CLAD_DIR_IN_GIT_REPO = "robot/clad/src/clad/audio"
AUDIO_CSV_FILE_IN_GIT_REPO = "tools/audio/audioEventMetadata.csv"

AUDIO_EVENT_TYPES = "audioEventTypes"
AUDIO_PARAMETER_TYPES = "audioParameterTypes"
AUDIO_SWITCH_TYPES = "audioSwitchTypes"
AUDIO_STATE_TYPES = "audioStateTypes"

AUDIO_INFO_CLASSES = { AUDIO_EVENT_TYPES : ["Anki.AudioMetaData.GameEvent.GenericEvent"],
                       AUDIO_STATE_TYPES : ["Anki.AudioMetaData.GameState.StateGroupType"],
                       AUDIO_SWITCH_TYPES : ["Anki.AudioMetaData.GameState.SwitchState.SwitchGroupType"],
                       AUDIO_PARAMETER_TYPES : ["Anki.AudioMetaData.GameParameter.ParameterType"] }

AUDIO_GROUPS_FILES = { AUDIO_EVENT_TYPES : "EVENT_GROUPS",
                       AUDIO_PARAMETER_TYPES : "RTPC_GROUPS" }

DELIMITERS = { AUDIO_EVENT_TYPES : EVENT_NAME_DELIMITER,
               AUDIO_PARAMETER_TYPES : PARAMETER_NAME_DELIMITER }

SOUNDBANK_SVN_REPO = "victor-audio-assets"
SOUNDBANK_PACKAGE_NAME = None
SOUNDBANK_ENV_VAR = "ANKI_SOUNDBANKS"

EVENT_NAME_ATTR = "audioName"
PARAMETER_NAME_ATTR = "parameterName"
TRIGGER_TIME_ATTR = "triggerTime_ms"

EVENT_GROUPS_ATTR = "eventGroups"
EVENT_IDS_ATTR = "eventIds"
VOLUMES_ATTR = "volumes"
PROBABILITIES_ATTR = "probabilities"
STATES_ATTR = "states"
STATE_GROUP_ID_ATTR = "stateGroupId"
STATE_ID_ATTR = "stateName"

SWITCHES_ATTR = "switches"
SWITCH_GROUP_ID_ATTR = "switchGroupId"
SWITCH_ID_ATTR = "switchName"

PARAMETERS_ATTR = "parameters"
PARAMETER_ID_ATTR = "parameterID"
VALUE_ATTR = "value"
TIME_MS_ATTR = "timeMs"
CURVE_ATTR = "curveType"

PROB_ATTR = "probability"
VOLUME_ATTR = "volume"
ALT_SOUNDS_ATTR = "hasAlts"

VARIANT_ATTR_SUFFIX_START_INDEX = 2
AUDIO_EVENT_ATTRS_WITH_VARIATIONS = [AUDIO_ENUM_ATTR, PROB_ATTR, VOLUME_ATTR]
AUDIO_EVENT_ATTRS = AUDIO_EVENT_ATTRS_WITH_VARIATIONS
EVENT_ENUM_ATTRS = [EVENT_NAME_ATTR]
PARAMETER_ENUM_ATTRS = [EVENT_NAME_ATTR]
STATE_ENUM_ATTRS = [STATE_ID_ATTR, STATE_GROUP_ID_ATTR]
SWITCH_ENUM_ATTRS = [STATE_ID_ATTR, STATE_GROUP_ID_ATTR]

DEFAULT_VOLUME = 100
DEFAULT_PROBABILITY = 100

NUMERICAL_EVENT_ATTR_VALUES = { PROB_ATTR   : {"default":DEFAULT_PROBABILITY, "min":1,  "max":100} ,
                                VOLUME_ATTR : {"default":DEFAULT_VOLUME, "min":10, "max":100} }

INT_ATTRS = [PROB_ATTR, VOLUME_ATTR, TIME_MS_ATTR]
FLOAT_ATTRS = [VALUE_ATTR]

NUMERICAL_ATTRS = INT_ATTRS + FLOAT_ATTRS

ENUM_ATTRS = [EVENT_NAME_ATTR, EVENT_NAME_ATTR, CURVE_ATTR,
              SWITCH_GROUP_ID_ATTR, STATE_GROUP_ID_ATTR, STATE_ID_ATTR]

NUMERICAL_EVENT_ATTRS = NUMERICAL_EVENT_ATTR_VALUES.keys()
EVENT_ATTRS = [EVENT_NAME_ATTR] + NUMERICAL_EVENT_ATTRS
ALL_ATTRS = ENUM_ATTRS + NUMERICAL_ATTRS

SHORT_NAMES_DICT = { AUDIO_ENUM_ATTR : "wwid",
                     PARAMETER_NAME_ATTR : "param",
                     SWITCH_ID_ATTR : "sw",
                     SWITCH_GROUP_ID_ATTR : "swid",
                     STATE_ID_ATTR : "st",
                     STATE_GROUP_ID_ATTR : "stid",
                     CURVE_ATTR : "ctype"}

# This is similar to AudioMultiplexerTypes.clad. Each of the curve types has an assigned index.
CURVE_TYPES = { "No interpolation" : 0,
                "Linear" : 1,
                "SCurve" : 2,
                "InversedSCurve" : 3,
                "Sine" : 4,
                "SineReciprocal" : 5,
                "Exp1" : 6,
                "Exp3" : 7,
                "Log1" : 8,
                "Log3" : 9  }

TOP_LEVEL_ENUM_ATTRS = [CURVE_ATTR, PARAMETER_NAME_ATTR, SWITCH_GROUP_ID_ATTR, STATE_GROUP_ID_ATTR]
SUB_LEVEL_ENUM_ATTRS = [STATE_ID_ATTR, SWITCH_ID_ATTR]
AUDIO_ACTION_TO_GROUP_DICT = { STATES_ATTR : STATE_GROUP_ID_ATTR,
                               SWITCHES_ATTR : SWITCH_GROUP_ID_ATTR }

def one_hundredth(value):
    return float("%.2f" % (value * 0.01))

AUDIO_ATTR_CONVERSION = { VOLUME_ATTR: one_hundredth,
                          PROB_ATTR: one_hundredth }

DEFAULT_EVENT_GROUPS_DICT = { EVENT_IDS_ATTR: [],
                              EVENT_NAME_ATTR: [],
                              VOLUMES_ATTR: [], # Full volume = 1.0
                              PROBABILITIES_ATTR: [] }

DEFAULT_STATES_DICT = { STATE_GROUP_ID_ATTR: 0,
                        STATE_ID_ATTR: 0 }

DEFAULT_SWITCHES_DICT = { SWITCH_GROUP_ID_ATTR: 0,
                          STATE_ID_ATTR: 0 }

DEFAULT_PARAMS_DICT = { PARAMETER_ID_ATTR: 0,
                        VALUE_ATTR: 0.0,
                        TIME_MS_ATTR: 0,
                        CURVE_ATTR: 0 }

_DEFAULT_AUDIO_JSON = {
    "Name": "RobotAudioKeyFrame",
    TRIGGER_TIME_ATTR: 0,
    EVENT_GROUPS_ATTR: [DEFAULT_EVENT_GROUPS_DICT]
}

# For cases when there is no audio event in the keyframe
DEFAULT_EMPTY_AUDIO_JSON = {
    "Name": "RobotAudioKeyFrame",
    TRIGGER_TIME_ATTR: 0
}

TOOLS_DIR_ENV_VAR = "ANKI_TOOLS"

STIM_WWISE_PARAMETER = "Robot_Vic_Stimulation"
STIM_SETTING_ENV_VAR = "AUDIO_STIMULATION_SETTING"
STIM_PARAM_RANGE = (0.0, 1.0)
#STIM_TOOLTIP = "-2.0 for Frustrated, -1.0 for LowStim, 0.0 for MedStim, 1.0 for HighStim"
STIM_TOOLTIP = None

SELECTED_GROUP_ENV_VAR = "SELECTED_AUDIO_GROUP"

INVALID = "Invalid"


import sys
import os
import copy
import json
import pprint
import tempfile
import shutil
import subprocess
import filecmp
import imp
import bisect
from ankimaya.export_error_check.error_checker_utils import add_json_node

try:
    from maya import cmds
    from maya import mel
except ImportError, e:
    print("WARNING: %s" % e)
try:
    from PySide2.QtCore import QObject, Signal
except ImportError, e:
    print("WARNING: %s" % e)
    QObject = object
from ankiutils import svn_tools


# This global variable helps track the "active" audio keyframes
# based on the selected audio group of interest.
globalActiveKeyframes = None


def _getDataDestination(repo):
    sbDir = os.getenv(SOUNDBANK_ENV_VAR)
    if not sbDir:
        raise ValueError("'%s' environment variable should be set" % SOUNDBANK_ENV_VAR)
    repoDir = sbDir.split(repo)[0]
    repoDir = os.path.join(repoDir, repo)
    if not os.path.isdir(repoDir):
        os.makedirs(repoDir)
    return repoDir


def getSoundBanks(pkg_name=SOUNDBANK_PACKAGE_NAME, repo=SOUNDBANK_SVN_REPO, version="head"):
    dataDest = _getDataDestination(repo)
    print("Destination for SoundBanks: %s" % dataDest)
    msg = "Checking out %s (version %s) could take several minutes." % (repo, version)
    result = cmds.confirmDialog(message=msg, title="Proceed?", icon="question",
                                button=["OK", "Cancel"], defaultButton="Cancel",
                                cancelButton="Cancel")
    if result != "OK":
        print("SoundBank download canceled")
        return None
    try:
        result = svn_tools.checkout_svn_package(pkg_name, repo, dataDest, version=version, verbose=False)
    except ValueError, e:
        cmds.warning(str(e))
        cmds.confirmDialog(message=str(e), title="Failed to checkout %s (version %s)" % (repo, version),
                           icon="critical")
    else:
        cmds.confirmDialog(message=result, title="Checked out %s (version %s)" % (repo, version),
                           icon="information")


def getAudioWorkingDir():
    # When executed from within Maya, the $ANKI_SB_WORKING environment variable will point at the Soundbank directory
    # that should be used, which is typically EXTERNALS/victor-audio-assets/victor_robot/dev_mac/ or
    # EXTERNALS/local-audio-assets/victor_robot/dev_mac/
    sbDir = os.getenv('ANKI_SB_WORKING')
    while sbDir not in ['', None, os.sep]:
        metadataDir = os.path.join(sbDir, 'metadata')
        if os.path.isdir(metadataDir):
            break
        else:
            sbDir = os.path.dirname(sbDir)
    return sbDir


def syncWwisePlugin(pluginName=WWISE_PLUGIN_NAME, melCmd=UPDATE_WWISE_PLUGIN_DATA_CMD):
    # Run the MEL command that keeps Wwise plugin in sync with latest keyframes
    try:
        mel.eval("%s;" % melCmd)
    except RuntimeError, e:
        cmds.warning("Failed to execute %s because: %s" % (melCmd, str(e).replace(os.linesep, '. ')))
        if "cannot find procedure" in str(e).lower():
            cmds.warning("Try reloading the '%s' plugin" % pluginName)


def playAudioEvent(audioEvent, pluginName=WWISE_PLUGIN_NAME, melCmd=PLAY_AUDIO_EVENT_CMD):
    # Run the MEL command that plays an audio event by name
    melCmd = "%s %s" % (melCmd, audioEvent)
    try:
        mel.eval("%s;" % melCmd)
    except RuntimeError, e:
        cmds.warning("Failed to execute %s because: %s" % (melCmd, str(e).replace(os.linesep, '. ')))
        if "cannot find procedure" in str(e).lower():
            cmds.warning("Try reloading the '%s' plugin" % pluginName)


def setParameter(paramName, paramValue, pluginName=WWISE_PLUGIN_NAME, melCmd=SET_PARAMETER_CMD):
    # Run the MEL command that sets an RTPC parameter value
    print("Setting '%s' audio parameter to %s" % (paramName, paramValue))
    melCmd = "%s %s %s" % (melCmd, paramName, paramValue)
    try:
        mel.eval("%s;" % melCmd)
    except RuntimeError, e:
        cmds.warning("Failed to execute %s because: %s" % (melCmd, str(e).replace(os.linesep, '. ')))
        if "cannot find procedure" in str(e).lower():
            cmds.warning("Try reloading the '%s' plugin" % pluginName)


def setStimulationSetting(stimValue, wwiseParam=STIM_WWISE_PARAMETER,
                          stimSettingEnvVar=STIM_SETTING_ENV_VAR):
    """
    Set the stimulation RTPC in Wwise and the environment variable.
    """
    setParameter(wwiseParam, stimValue)
    os.environ[stimSettingEnvVar] = str(stimValue)


def getStimulationSetting(defaultStimSetting=None, stimSettingEnvVar=STIM_SETTING_ENV_VAR):
    """
    Query the environment variable and return the current stimulation setting.

    If there is no stimulation currently set in the environment variable and
    'defaultStimSetting' is set, then that default stimulation will be returned
    (and the environment variable will be set to that).
    """
    currentStim = os.getenv(stimSettingEnvVar)
    if currentStim is None and defaultStimSetting is not None:
        currentStim = defaultStimSetting
        os.environ[stimSettingEnvVar] = str(currentStim)
    return currentStim


def getDefaultAudioJson():
    return copy.deepcopy(_DEFAULT_AUDIO_JSON)


def getAudioEventJsonFile():
    audioEventJsonFile = None
    toolsDir = os.getenv(TOOLS_DIR_ENV_VAR)
    if toolsDir:
        otherDir = os.path.join(toolsDir, "other")
        audioEventJsonFile = os.path.join(otherDir, AUDIO_EVENT_JSON_FILE)
    return audioEventJsonFile


def getAudioToolsDir():
    audioToolsDir = None
    toolsDir = os.getenv(TOOLS_DIR_ENV_VAR)
    if toolsDir:
        audioToolsDir = os.path.join(toolsDir, "audio")
    return audioToolsDir


def balanceLoopingEvents(eventName, eventTrackerList):
    """
    This function can be used to help keep track of looping audio
    events so we can later issue a warning if there is a
    "Play__Blah__Foo_Loop_Play" audio event that is NOT followed
    by a "Stop__Blah__Foo_Loop_Stop" audio event.
    """
    eventName = str(eventName)
    if eventName.lower().endswith("_loop_play") and eventName.lower().startswith("play__"):
        eventTrackerList.append(eventName)
    elif eventName.lower().endswith("_loop_stop") and eventName.lower().startswith("stop__"):
        loopPlayName = eventName.replace("_loop_stop", "_loop_play")
        loopPlayName = loopPlayName.replace("_Loop_Stop", "_Loop_Play")
        loopPlayName = loopPlayName.replace("_LOOP_STOP", "_LOOP_PLAY")
        loopPlayName = loopPlayName.replace("stop__", "play__", 1)
        loopPlayName = loopPlayName.replace("Stop__", "Play__", 1)
        loopPlayName = loopPlayName.replace("STOP__", "PLAY__", 1)
        while loopPlayName in eventTrackerList:
            eventTrackerList.remove(loopPlayName)


def loadAudioGroupsFromPy(audioGroupsPyFile=None, audioGroupsFile=AUDIO_GROUPS_FILE,
                          audioGroupsAttr="EVENT_GROUPS"):
    if not audioGroupsPyFile:
        audioToolsDir = getAudioToolsDir()
        audioGroupsPyFile = os.path.join(audioToolsDir, audioGroupsFile + ".py")
    if audioGroupsPyFile and os.path.isfile(audioGroupsPyFile):
        audioGroupsMod = imp.load_source(audioGroupsFile, audioGroupsPyFile)
        audioGroups = copy.copy(eval("audioGroupsMod.%s" % audioGroupsAttr))
        return audioGroups
    else:
        # Saving error to the Export errors, since loadAudioGroupsFromPy is being called in
        # load_audio_to_globals() during export_robot_anim() of export_for_robot.
        msg = "Unable to load audio groups from %s" % audioGroupsPyFile
        add_json_node(node_name="Audio groups",
                      fix_function="", status="error",
                      message=msg)
        raise ValueError(msg)


def loadAudioAttrsFromPy(audioPyFile=None, audioTypes=AUDIO_EVENT_TYPES, audioGroups=None,
                         audioGroupPaths=None, recursive=False):
    """
    The 'audioGroups' input argument can be used to limit the results
    to specific groups:
     - when set to None (default value), this will load the list of
       audio groups from audioGroups.py
     - when set to an empty list, all audio events are returned
    """
    audioIds = {}
    audioNamesSorted = []
    groupedAudioNames = {}

    # The audioTypes.py file imports and uses the "msgbuffers" python
    # package, so sys.path needs to be updated to find that.
    gitRepoRoot = getGitRepoRoot()
    msgBuffersDir = os.path.join(gitRepoRoot, "victor-clad", "tools", "message-buffers", "support", "python")
    sys.path.append(msgBuffersDir)

    if audioGroups is None:
        audioGroups = loadAudioGroupsFromPy(audioGroupsAttr=AUDIO_GROUPS_FILES[audioTypes])
    elif isinstance(audioGroups, str):
        audioGroups = [audioGroups]

    subAudioGroups = {}

    if not audioPyFile:
        audioToolsDir = getAudioToolsDir()
        audioPyFile = os.path.join(audioToolsDir, audioTypes + ".py")

    if audioPyFile and os.path.isfile(audioPyFile):
        audioMod = imp.load_source(audioTypes, audioPyFile)

        if not audioGroupPaths:
            audioGroupPaths = AUDIO_INFO_CLASSES[audioTypes]
        for audioGroupPath in audioGroupPaths:
            groupObj = audioMod
            for part in audioGroupPath.split('.'):
                try:
                    groupObj = getattr(groupObj, part)
                except AttributeError:
                    continue
            for audioGroup in audioGroups:
                groupedAudioNames[audioGroup] = []
            groupedAudioNames[ALL_GROUP] = []
            for wwiseName in dir(groupObj):
                if wwiseName.startswith("_"):
                    continue
                if audioGroups == []:
                    wwiseId = getattr(groupObj, wwiseName)
                    audioIds[wwiseName] = wwiseId
                    if recursive:
                        outerGroup = ".".join(audioGroupPath.split('.')[:-1])
                        subAudioGroups[wwiseName]=("%s.%s" %(outerGroup, wwiseName))
                    continue

                for audioGroup in audioGroups:
                    delimiter = DELIMITERS[audioTypes]
                    if delimiter != "":
                        isGroupInWwiseName = delimiter + audioGroup + delimiter in wwiseName
                    else:
                        isGroupInWwiseName = audioGroup in wwiseName
                    if isGroupInWwiseName:
                        wwiseId = getattr(groupObj, wwiseName)
                        audioIds[wwiseName] = wwiseId
                        if wwiseName not in groupedAudioNames[audioGroup] and wwiseName != INVALID:
                            groupedAudioNames[audioGroup].append(wwiseName)
                        if wwiseName not in groupedAudioNames[ALL_GROUP] and wwiseName != INVALID:
                            groupedAudioNames[ALL_GROUP].append(wwiseName)
                        break
                    else:
                        if wwiseName not in groupedAudioNames[ALL_GROUP]and wwiseName != INVALID:
                            groupedAudioNames[ALL_GROUP].append(wwiseName)

        audioNamesSorted = audioIds.keys()
        audioNamesSorted.sort()

        if recursive:
            all_subAudioIds = {}
            for wwiseName, subAudioGroup in subAudioGroups.iteritems():
                # If we decide to NOT have invalid be selectable...
                # if wwiseName == "Invalid":
                #     all_subAudioIds[wwiseName] = []
                #     continue
                subNamesSorted, subAudioIds, groupedNames = loadAudioAttrsFromPy(
                    audioTypes=audioTypes, audioGroups=[],
                    audioGroupPaths=[subAudioGroup], recursive=False)
                all_subAudioIds[wwiseName]=subAudioIds

    else:
        msg = "audio events python file (%s) not found" % audioPyFile
        try:
            cmds.warning(msg)
        except NameError:
            print("WARNING: %s" % msg)

    if recursive:
        return (audioNamesSorted, audioIds, all_subAudioIds)

    return (audioNamesSorted, audioIds, groupedAudioNames)


# This function was taken from the AnkiMenu.py plugin and updated.
def loadAudioAttrsFromJson(audioEventJsonFile=None):
    audioIds = {}
    audioNamesSorted = []
    if not audioEventJsonFile:
        audioEventJsonFile = getAudioEventJsonFile()
    if audioEventJsonFile and os.path.isfile(audioEventJsonFile):
        try:
            with open(audioEventJsonFile) as data_file:
                data = json.load(data_file)
        except ValueError:
            msg = "Failed to parse the '%s' file" % audioEventJsonFile
            cmds.warning(msg)
            cmds.confirmDialog(message=msg, title="Anki Audio Error", icon="critical")
            return (audioNamesSorted, audioIds)
        for event in data:
            audioIds[event["wwiseName"]] = event["wwiseIdValue"]
        if data:
            audioNamesSorted = audioIds.keys()
            audioNamesSorted.sort()
    else:
        cmds.warning("audio events json file (%s) not found" % audioEventJsonFile)
    return (audioNamesSorted, audioIds)


loadAudioAttrs = loadAudioAttrsFromPy


def getGitRepoRoot():
    # The UpdateAudioAssets.py script that we run to generate updated audio
    # data is in the cozmo-one or victor git repo, so we need access to that.
    gitRepoRoot = os.getenv("ANKI_PROJECT_ROOT")
    if not gitRepoRoot:
        raise ValueError("Cannot update the audio event list unless ANKI_PROJECT_ROOT "
                         "is set to the root of your cozmo-one or victor git repo")
    return gitRepoRoot


def runCommand(cmd, verbose=False, context=None, path_additions=['/usr/local/bin']):
    for addition in path_additions:
        os.environ['PATH'] += os.pathsep + addition
    #print("Running: %s" % cmd)
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (stdout, stderr) = p.communicate()
    if verbose:
        print(stdout)
        print(stderr)
    status = p.poll()
    if status != 0:
        errMsg = "Failed to execute [%s] because: %s" % (cmd, stderr)
        if context:
            errMsg += os.linesep + str(context)
        add_json_node(node_name="Update audio files",
                      fix_function="", status="error",
                      message=errMsg)
        raise RuntimeError(errMsg)
    return (status, stdout, stderr)


def updateAudioPyFiles(updateScript=UPDATE_SCRIPT_IN_GIT_REPO,
                       pyEmitterScript=PY_EMITTER_SCRIPT_IN_GIT_REPO,
                       audioCladDir=AUDIO_CLAD_DIR_IN_GIT_REPO,
                       audioCsvFile=AUDIO_CSV_FILE_IN_GIT_REPO):

    gitRepoRoot = getGitRepoRoot()
    updateScript = os.path.join(gitRepoRoot, updateScript)
    pyEmitterScript = os.path.join(gitRepoRoot, pyEmitterScript)

    # Get the path to the working sound banks
    workingSbs = getAudioWorkingDir()

    # Execute the UpdateAudioAssets.py script to update the CSV file.
    # ['$HOME/workspace/cozmo-one/tools/audio/UpdateAudioAssets.py', 'update-alt-workspace', '<workingSoundBankDir>']
    updateCmd = [updateScript]
    updateCmd.append('update-alt-workspace')
    updateCmd.append(workingSbs)
    #print("Update command: %s" % updateCmd)
    errMsg = "Failed to update the CSV file"
    status, stdout, stderr = runCommand(updateCmd, context=errMsg)

    # Execute the UpdateAudioAssets.py script to update the CLAD files.
    # ['$HOME/workspace/cozmo-one/tools/audio/UpdateAudioAssets.py', 'generate', '--soundBankDir', '<workingSoundBankDir>']
    updateCmd = [updateScript]
    updateCmd.append("generate")
    updateCmd.extend(['--soundBankDir', workingSbs])
    #print("Update command: %s" % updateCmd)
    errMsg = "Failed to update the CLAD files"
    status, stdout, stderr = runCommand(updateCmd, context=errMsg)

    # Update the PYTHON files from the CLAD files...
    for audioFile in AUDIO_INFO_CLASSES.keys():
        audioPyFile = audioFile + ".py"

        audioCladFile = os.path.join(gitRepoRoot, audioCladDir, audioFile + ".clad")
        emitCmd = [pyEmitterScript]
        emitCmd.append(audioCladFile)
        #print("Emit command: %s" % emitCmd)
        errMsg = "Failed to emit PYTHON from CLAD"
        status, stdout, stderr = runCommand(emitCmd, context=errMsg)

        prefix, suffix = os.path.splitext(audioPyFile)
        tmpFile = tempfile.mkstemp(dir="/tmp", prefix="%s-" % prefix, suffix=suffix)[1]
        with open(tmpFile, 'w') as fh:
            fh.write(stdout)

        if audioFile == AUDIO_EVENT_TYPES:
            # Refresh the internal list of audio events.
            eventNamesSorted, audioIds, groupedAudioNames = loadAudioAttrsFromPy(tmpFile)
            try:
                setupEnumAttr(eventNamesSorted)
            except TypeError:
                # The "x:AnkiAudioNode" object hasn't been created yet
                pass

        # Copy the temp output file into place if it has any updates.
        audioToolsDir = getAudioToolsDir()
        destFile = os.path.join(audioToolsDir, audioPyFile)
        copyTmpFile(tmpFile, destFile)

    # Revert changes to the CSV file and CLAD files...
    revertCmd = ["git", "checkout"]
    os.chdir(gitRepoRoot)
    revertTargets = [audioCladDir, audioCsvFile]
    for revertTarget in revertTargets:
        errMsg = "Failed to revert changes to %s" % revertTarget
        status, stdout, stderr = runCommand(revertCmd + [revertTarget], context=errMsg)


def updateAudioEventJsonFile(audioGroups=None, updateScript=UPDATE_SCRIPT_IN_GIT_REPO):

    if audioGroups is None:
        audioGroups = loadAudioGroupsFromPy()
    elif isinstance(audioGroups, str):
        audioGroups = [audioGroups]

    prefix, suffix = os.path.splitext(AUDIO_EVENT_JSON_FILE)
    tmpFile = tempfile.mkstemp(dir="/tmp", prefix="%s-" % prefix, suffix=suffix)[1]

    gitRepoRoot = getGitRepoRoot()
    updateScript = os.path.join(gitRepoRoot, updateScript)

    # Build the command (as a list) to execute the UpdateAudioAssets.py script.
    # ['$HOME/workspace/cozmo-one/tools/audio/UpdateAudioAssets.py', 'generate-maya-cozmo-data',
    #          <temp_json_file>, 'groups', 'Robot', 'Robot_Vo', 'Robot_Sfx', 'Dev_Robot',
    #          --soundBankDir, <sound_bank_directory>]
    updateCmd = [updateScript]
    updateCmd.append("generate-maya-cozmo-data")
    updateCmd.append(tmpFile)
    updateCmd.extend(["groups"] + audioGroups)
    updateCmd.extend(["--soundBankDir", getAudioWorkingDir()])
    #print("Update command: %s" % updateCmd)

    # Before executing the UpdateAudioAssets.py script, remove the temp output
    # file if it already exists.
    if os.path.isfile(tmpFile):
        os.remove(tmpFile)

    # Execute the UpdateAudioAssets.py script and raise exception if that fails.
    errMsg = "Failed to generate the temp audio event list in %s" % tmpFile
    status, stdout, stderr = runCommand(updateCmd, context=errMsg)
    if not os.path.isfile(tmpFile):
        raise RuntimeError(errMsg)

    # Refresh the internal list of audio events.
    audioNamesSorted, audioIds = loadAudioAttrsFromJson(tmpFile)
    try:
        setupEnumAttr(audioNamesSorted)
    except TypeError:
        # The "x:AnkiAudioNode" object hasn't been created yet
        pass

    # Copy the temp output file into place if it has any updates.
    audioEventJsonFile = getAudioEventJsonFile()
    copyTmpFile(tmpFile, audioEventJsonFile)


def copyTmpFile(tmpFile, destFile):
    # Copy a temp output file into place if it has any updates.
    destDir = os.path.dirname(destFile)
    if not os.path.isdir(destDir):
        os.makedirs(destDir)
    if not os.path.isfile(destFile) or not filecmp.cmp(destFile, tmpFile):
        msg = "Copying %s to %s" % (tmpFile, destFile)
        shutil.copy(tmpFile, destFile)
    else:
        msg = "There are no changes in %s to copy to %s" % (tmpFile, destFile)
    print msg


# Maya stores these enums as an int list, and doing them not in order puts hold in the drop down box :(
# If these ever get out of order, we reconcile them when the node is selected.
# Since we can't "key" strings, we key the enums.


# This function was taken from the AnkiMenu.py plugin and updated.
def updateEventIdEnum(oldEnumList, newEnumStr, audioNamesSorted, renameMapping=None,
                      nodeName=AUDIO_NODE_NAME, enumAttr=AUDIO_ENUM_ATTR,
                      shortName=AUDIO_ENUM_SHORT_NAME, updateVariantAttr=False):

    # TODO: Can this function be refactored and/or moved so it can be used to set keyframes
    #       that trigger facial animation PNG sequences.  (Nishkar Grover, 07/14/2016)

    # Store the old values...
    audioVs = cmds.keyframe(nodeName, attribute=enumAttr, query=True, valueChange=True)
    audioTs = cmds.keyframe(nodeName, attribute=enumAttr, query=True, timeChange=True)

    # Stomp with the new values, takes care of removals and additions that weren't keyed so UI updates.
    # The Maya attribute UI is stupid and will error out on just a change or
    # attribute editor gets out of sync with channel box, so remove everything.
    if cmds.attributeQuery(enumAttr, node=nodeName, exists=True):
        cmds.deleteAttr(nodeName, at=enumAttr)
    else:
        return

    cmds.select(nodeName, replace=True)
    if updateVariantAttr and enumAttr[-1].isdigit():
        cmds.addAttr(longName=enumAttr, shortName=shortName+str(enumAttr[-1]), attributeType='enum',
                     keyable=True, enumName=newEnumStr)
    else:
        cmds.addAttr(longName=enumAttr, shortName=shortName, attributeType='enum',
                     keyable=True, enumName=newEnumStr)

    if audioVs is None:
        return None

    num_events_renamed = 0

    i = 0
    for keyframe_enum_index in audioVs:
        enum_index = (int)(keyframe_enum_index)
        oldEvent = oldEnumList[enum_index]
        if renameMapping and oldEvent in renameMapping:
            newName = renameMapping[oldEvent]
            if newName in audioNamesSorted:
                print("Renaming '%s' audio event to '%s'" % (oldEvent, newName))
                oldEvent = newName
                enum_index = -1
                num_events_renamed += 1
            else:
                print("Cannot rename '%s' audio event to '%s' because the latter "
                      "is not currently available for use" % (oldEvent, newName))
        if enum_index < 0 or len(audioNamesSorted) < enum_index or audioNamesSorted[enum_index] != oldEvent:
            if oldEvent and oldEvent in audioNamesSorted:
                updatedIdx = audioNamesSorted.index(oldEvent)
                cmds.setKeyframe(nodeName, v=updatedIdx, t=audioTs[i], at=enumAttr)
            else:
                try:
                    default_event_idx = audioNamesSorted.index(DEFAULT_AUDIO_EVENT)
                except ValueError:
                    default_event_idx = 0
                cmds.setKeyframe(nodeName, v=default_event_idx, t=audioTs[i], at=enumAttr, outTangentType="step")
                msg  = "Replacing audio event at frame %s with '%s' " % (audioTs[i], audioNamesSorted[default_event_idx])
                msg += "default marker because '%s' not found" % oldEvent
                # This is currently counted as an audio event rename...
                num_events_renamed += 1
                cmds.warning(msg)
                cmds.confirmDialog(message=msg, title="Anki Audio Error", icon="critical")
        else:
            # The order of this key didn't change but still rekey it since we had to remove the attribute.
            cmds.setKeyframe(nodeName, v=audioVs[i], t=audioTs[i], at=enumAttr, outTangentType="step")
        i += 1

    return num_events_renamed


def setAudioParameterKeyframe(keyframeData, parameterNames, displayedAttrNames, nodeName=AUDIO_NODE_NAME):
    currentTime = cmds.currentTime(query=True)
    for attr_name, attr_values in keyframeData.iteritems():
        if attr_name in displayedAttrNames.keys():
            displayedAttr = displayedAttrNames[attr_name]
        else:
            displayedAttr = attr_name

        for existing_attr in cmds.listAttr(nodeName):
            if len(existing_attr) == len(displayedAttr):
                continue
            if (existing_attr[:len(displayedAttr)] == displayedAttr):
                if int(existing_attr[len(displayedAttr):]) > len(attr_values):
                    cmds.cutKey('.'.join((nodeName, existing_attr)), clear=True, time=(currentTime,))

        if attr_name in NUMERICAL_ATTRS:
            for i in range(len(attr_values)):
                if i == 0:
                    variantAttr = displayedAttr
                else:
                    variantAttr = displayedAttr+str(i+1)
                if not cmds.attributeQuery(variantAttr, node=nodeName, exists=True):
                    # Here can check without basename (unlike in _addNumericalAttr) because checking
                    # that it's not variant attr above
                    if attr_name in INT_ATTRS:
                        cmds.addAttr(nodeName, hasMinValue=False, hasMaxValue=False,
                                     longName=variantAttr, attributeType='long', keyable=True,
                                     defaultValue=0)
                    elif attr_name in FLOAT_ATTRS:
                        cmds.addAttr(nodeName, hasMinValue=False, hasMaxValue=False,
                                     longName=variantAttr, attributeType='float', keyable=True,
                                     defaultValue=0)
                cmds.setAttr("%s.%s" %(nodeName, variantAttr), attr_values[i])
                cmds.setKeyframe("%s.%s" % (nodeName, variantAttr), outTangentType="step")

        if attr_name in ENUM_ATTRS:
            for i in range(len(attr_values)):
                if i == 0:
                    variantAttr = displayedAttr
                else:
                    variantAttr = displayedAttr + str(i+1)
                enumNames = parameterNames[attr_name].keys()
                enumNames.sort()

                if not cmds.attributeQuery(variantAttr, node=nodeName, exists=True):
                    enums_as_str = ":".join(enumNames)
                    cmds.addAttr(longName=variantAttr,
                                 attributeType='enum',
                                 keyable=True, enumName=enums_as_str)

                parameterIdx = enumNames.index(attr_values[i])
                cmds.setAttr("%s.%s"%(nodeName, variantAttr), parameterIdx)
                cmds.setKeyframe("%s.%s"%(nodeName, variantAttr), outTangentType="step")


def setAudioEventKeyframe(keyframeData, eventNamesSorted, nodeName=AUDIO_NODE_NAME,
                     enumAttr=AUDIO_ENUM_ATTR, enumAttrShortName=AUDIO_ENUM_SHORT_NAME,
                     variantSuffixStart=VARIANT_ATTR_SUFFIX_START_INDEX):
    currentTime = cmds.currentTime(query=True)
    # keyframeData structure: {'volume': [100], 'eventName': ['Play__Robot_Vic_Sfx__Blink'], 'probability': [100]}
    eventNames = keyframeData[EVENT_NAME_ATTR]
    if isinstance(eventNames, str):
        eventNames = [eventNames]

    idx = 0
    while True:
        if idx == 0:
            if not cmds.attributeQuery(enumAttr, node=nodeName, exists=True):
                setupEnumAttr(eventNamesSorted, nodeName, enumAttr, enumAttrShortName)
            eventName = eventNames[idx]
            eventIdx = eventNamesSorted.index(eventName)
            cmds.setAttr('.'.join((nodeName, enumAttr)), eventIdx)
            cmds.setKeyframe('.'.join((nodeName, enumAttr)))

        if idx > 0:
            suffix = variantSuffixStart + idx - 1
            variantAttr = enumAttr + str(suffix)
            if idx < len(eventNames):
                variantAttrShortName = enumAttrShortName + str(suffix)
                setupEnumAttr(eventNamesSorted, nodeName, variantAttr, variantAttrShortName)
            audioAttr = '.'.join((nodeName, variantAttr))
        else:
            audioAttr = '.'.join((nodeName, enumAttr))

        if idx < len(eventNames):
            eventName = eventNames[idx]
            eventIdx = eventNamesSorted.index(eventName)
            cmds.setAttr(audioAttr, eventIdx)
            cmds.setKeyframe(audioAttr)
        else:
            attrExists = cmds.attributeQuery(variantAttr, node=nodeName, exists=True)
            if attrExists:
                cmds.cutKey(audioAttr, clear=True, time=(currentTime,))
                for otherAttr in AUDIO_EVENT_ATTRS:
                    otherVariantAttr = variantAttr.replace(enumAttr, otherAttr)
                    if cmds.attributeQuery(otherVariantAttr, node=nodeName, exists=True):
                        otherAudioAttr = audioAttr.replace(enumAttr, otherAttr)
                        cmds.cutKey(otherAudioAttr, clear=True, time=(currentTime,))
            else:
                break
        idx += 1

    for attr, vals in keyframeData.items():
        if attr == EVENT_NAME_ATTR:
            # already handled above
            continue
        if attr in AUDIO_EVENT_ATTRS:
            if not isinstance(vals, list) and not isinstance(vals, tuple):
                vals = [vals]
            for idx in range(len(vals)):
                val = vals[idx]
                if idx == 0:
                    if attr in NUMERICAL_EVENT_ATTRS:
                        if not cmds.attributeQuery(attr, node=nodeName, exists=True):
                            values = NUMERICAL_EVENT_ATTR_VALUES[attr]
                            _addNumericalAttr(attr, values)
                        cmds.setAttr('.'.join((nodeName, attr)), val)
                        cmds.setKeyframe('.'.join((nodeName, attr)), outTangentType="step")

                if idx > 0:
                    suffix = variantSuffixStart + idx - 1
                    variantAttr = attr + str(suffix)
                    if attr in NUMERICAL_EVENT_ATTRS and not cmds.attributeQuery(variantAttr, node=nodeName, exists=True):
                        values = NUMERICAL_EVENT_ATTR_VALUES[attr]
                        _addNumericalAttr(variantAttr, values)
                    attrWithVars = '.'.join((nodeName, variantAttr))
                else:
                    attrWithVars = '.'.join((nodeName, attr))
                cmds.setAttr(attrWithVars, val)
                cmds.setKeyframe(attrWithVars, outTangentType="step")
        else:
            attr = '.'.join((nodeName, attr))
            cmds.setAttr(attr, vals)
            cmds.setKeyframe(attr, outTangentType="step")

    if SELECTED_GROUP_ENV_VAR:
        selectedGroup = os.getenv(SELECTED_GROUP_ENV_VAR)
        if selectedGroup:
            selectedGroup = EVENT_NAME_DELIMITER + selectedGroup + EVENT_NAME_DELIMITER
            if selectedGroup in eventNames[0]:
                changeTimelineTickColorAtTime(currentTime)
                if globalActiveKeyframes:
                    bisect.insort(globalActiveKeyframes, currentTime)


def getAudioKeyframe(nodeName=AUDIO_NODE_NAME, displayedActionAttrs=None):
    # displayedActionAttrs = {"attr name in maya scene":"name in ui file"}
    keyframeData = {}
    currentTime = cmds.currentTime(query=True)
    allAttrs = cmds.listAttr(nodeName)
    for attr in allAttrs:
        for actionAttr in displayedActionAttrs.keys():
            if (attr[:len(actionAttr)] == actionAttr):
                if displayedActionAttrs[actionAttr] not in keyframeData:
                    keyframeData[displayedActionAttrs[actionAttr]] = []
                currentValue = cmds.keyframe(nodeName, at=attr,
                                             time=(currentTime, currentTime), q=True)
                if currentValue is not None:
                    if cmds.attributeQuery(attr, node=AUDIO_NODE_NAME, enum=True):
                        attr_name = cmds.getAttr("%s.%s" %(AUDIO_NODE_NAME,attr), asString=True, time=currentTime)
                        keyframeData[displayedActionAttrs[actionAttr]].append(attr_name)
                    else:
                        attr_value = cmds.getAttr("%s.%s" %(AUDIO_NODE_NAME,attr), time=currentTime)
                        keyframeData[displayedActionAttrs[actionAttr]].append(attr_value)
    return keyframeData


def removeAudioKeys(nodeName=AUDIO_NODE_NAME, actionAttrs=None):
    currentTime = cmds.currentTime(query=True)
    allAttrs = cmds.listAttr(nodeName)
    for attr in allAttrs:
        for actionAttr in actionAttrs:
            if (attr[:len(actionAttr)] == actionAttr):
                cmds.cutKey('.'.join((nodeName, attr)), clear=True, time=(currentTime,))


def setGlobalActiveKeyframes(activeKeyframes):
    global globalActiveKeyframes
    globalActiveKeyframes = activeKeyframes


def _getEventName(audioNamesSorted, audioAttr, currentTime=None):
    if currentTime is None:
        currentTime = cmds.currentTime(query=True)
    eventIdx = cmds.getAttr(audioAttr, time=currentTime)
    try:
        return audioNamesSorted[eventIdx]
    except IndexError:
        return None


def _getActionName(audioAttr, currentTime=None):
    if currentTime is None:
        currentTime = cmds.currentTime(query=True)
    audioName = cmds.getAttr(audioAttr, time=currentTime)
    return audioName


def _getKeyedVariants(currentTime, attr, variantSuffixStart):
    variantAttrs = []
    variant = variantSuffixStart
    while True:
        variantAttr = attr + str(variant)
        try:
            keyframes = cmds.keyframe(variantAttr, query=True)
        except ValueError:
            keyframes = None
        if not keyframes:
            break
        if currentTime is None or currentTime in keyframes:
            variantAttrs.append(variantAttr)
        variant += 1
    return variantAttrs


def refreshAttrAndVariants(audioNamesSorted, attr, currentTime=None,
                           variantSuffixStart=VARIANT_ATTR_SUFFIX_START_INDEX, nodeName=AUDIO_NODE_NAME):
    if currentTime is None:
        currentTime = cmds.currentTime(query=True)
    attrVariants = _getKeyedVariants(currentTime, "%s.%s" % (nodeName, attr), variantSuffixStart)
    try:
        setupEnumAttr(audioNamesSorted, enumAttrShortName=SHORT_NAMES_DICT[attr],
                      nodeName=nodeName, enumAttr=attr, changeAttr=True)
    except TypeError:
        # The "x:AnkiAudioNode" object hasn't been created yet
        return
    for var_attr in attrVariants:
        var_attr = var_attr.split(".")[-1]
        var_num = var_attr[len(attr):]
        setupEnumAttr(audioNamesSorted, enumAttrShortName=SHORT_NAMES_DICT[attr]+var_num,
                      nodeName=nodeName, enumAttr=var_attr, changeAttr=True)


def getEventKeyframeTimes(nodeName=AUDIO_NODE_NAME, enumAttr=AUDIO_ENUM_ATTR):
    audioAttr = '.'.join((nodeName, enumAttr))
    try:
        keyframes = cmds.keyframe(audioAttr, query=True)
    except ValueError:
        keyframes = None
    #print("audio keyframe times = %s" % keyframes)
    return keyframes


def getAudioKeyframeAtTime():
    raise NotImplementedError("You may need to call 'getEventKeyframeAtTime' instead of 'getAudioKeyframeAtTime'")


def getEventKeyframeAtTime(time, audioNamesSorted, nodeName=AUDIO_NODE_NAME, enumAttr=AUDIO_ENUM_ATTR,
                           variantSuffixStart=VARIANT_ATTR_SUFFIX_START_INDEX):
    keyframeData = {}

    audioAttr = '.'.join((nodeName, enumAttr))
    eventName = _getEventName(audioNamesSorted, audioAttr, time)
    if eventName is None:
        return keyframeData
    keyframeData[EVENT_NAME_ATTR] = [eventName]

    variantAttrs = _getKeyedVariants(time, audioAttr, variantSuffixStart)
    for variantAttr in variantAttrs:
        eventName = _getEventName(audioNamesSorted, variantAttr, time)
        if eventName:
            keyframeData[EVENT_NAME_ATTR].append(eventName)

    for attr in EVENT_ATTRS:
        if attr in ENUM_ATTRS:
            continue
        if not cmds.attributeQuery(attr, node=nodeName, exists=True):
            continue
        fqAttr = '.'.join((nodeName, attr))
        keyframesThisAttr = cmds.keyframe(fqAttr, query=True)
        if keyframesThisAttr and time in keyframesThisAttr:
            keyframeData[attr] = cmds.getAttr(fqAttr, time=time)

        if attr in AUDIO_EVENT_ATTRS_WITH_VARIATIONS:
            try:
                keyframeData[attr] = [keyframeData[attr]]
            except KeyError:
                variantAttrs = []
            else:
                variantAttrs = _getKeyedVariants(time, fqAttr, variantSuffixStart)
            for variantAttr in variantAttrs:
                keyframeData[attr].append(cmds.getAttr(variantAttr, time=time))

    return keyframeData


def getEventKeyframe(audioNamesSorted, nodeName=AUDIO_NODE_NAME, enumAttr=AUDIO_ENUM_ATTR):
    keyframes = getEventKeyframeTimes(nodeName, enumAttr)
    currentTime = cmds.currentTime(query=True)
    audioAttr = '.'.join((nodeName, enumAttr))
    if keyframes and currentTime in keyframes:
        return getEventKeyframeAtTime(currentTime, audioNamesSorted, nodeName, enumAttr)
    else:
        return {}


def changeTimelineTickColorAtTime(time, nodeName=AUDIO_NODE_NAME, enumAttr=AUDIO_ENUM_ATTR):
    cmds.selectKey(nodeName, attribute=enumAttr, time=(time,))
    cmds.keyframe(tds=True)


def resetTimelineTickColorAtTime(time, nodeName=AUDIO_NODE_NAME, enumAttr=AUDIO_ENUM_ATTR):
    cmds.selectKey(nodeName, attribute=enumAttr, time=(time,))
    cmds.keyframe(tds=False)


def setupEnumAttr(audioNamesSorted, nodeName=AUDIO_NODE_NAME, enumAttr=AUDIO_ENUM_ATTR,
                  enumAttrShortName=AUDIO_ENUM_SHORT_NAME, renameMapping=None, changeAttr=False):
    # Add enum attribute if it doesn't exist...
    enums_as_str = ":".join(audioNamesSorted)
    if not cmds.attributeQuery(enumAttr, node=nodeName, exists=True):
        cmds.select(nodeName, replace=True)
        cmds.addAttr(longName=enumAttr, shortName=enumAttrShortName, attributeType='enum',
                     keyable=True, enumName=enums_as_str)
    else:
        # Verify attributes are up to date as the wwise id orders could have changed.
        old_enums_as_str = cmds.attributeQuery(enumAttr, node=nodeName, listEnum=True)[0]
        if renameMapping or enums_as_str != old_enums_as_str:
            print("Attributes found but don't match or a rename was requested so updating...")
            # [daria] Not sure if enumAttr was supposed to be given as aparameter to updateEventIdEnum
            # adding a bool so that it remains as was in existing function implementations
            if not changeAttr:
                num_events_renamed = updateEventIdEnum(oldEnumList = old_enums_as_str.split(':'),
                                                       newEnumStr = enums_as_str,
                                                       audioNamesSorted = audioNamesSorted,
                                                       renameMapping = renameMapping,
                                                       nodeName = nodeName,
                                                       enumAttr = enumAttr,
                                                       shortName= enumAttrShortName)
            else:
                num_events_renamed = updateEventIdEnum(oldEnumList = old_enums_as_str.split(':'),
                                                       newEnumStr = enums_as_str,
                                                       audioNamesSorted = audioNamesSorted,
                                                       renameMapping = renameMapping,
                                                       nodeName = nodeName,
                                                       enumAttr = enumAttr,
                                                       shortName= enumAttrShortName,
                                                       updateVariantAttr=True)
            return num_events_renamed


# This function was taken from the AnkiMenu.py plugin and updated.
def setupAudioNode(audioNamesSorted, nodeName=AUDIO_NODE_NAME, enumAttr=AUDIO_ENUM_ATTR,
                   enumAttrShortName=AUDIO_ENUM_SHORT_NAME,
                   variantSuffixStart=VARIANT_ATTR_SUFFIX_START_INDEX, selectNode=True):

    if not isinstance(audioNamesSorted, list) or not audioNamesSorted:
        audioNamesSorted, audioIds, groupedAudioNames = loadAudioAttrs()

    if not cmds.objExists(nodeName):
        cmds.createNode("transform", n=nodeName)
        attributes = cmds.listAttr(nodeName, k=True)
        # Loop through all attributes and lock things like translation since we don't need them...
        for curr_attr in attributes:
            cmds.setAttr(nodeName + '.' + curr_attr, keyable=False,
                         lock=True, channelBox=False)
    if selectNode:
        cmds.select(nodeName, replace=True)

    if len(audioNamesSorted) > 0:
        setupEnumAttr(audioNamesSorted, nodeName, enumAttr, enumAttrShortName)
        audioAttr = '.'.join((nodeName, enumAttr))
        variantAttrs = _getKeyedVariants(None, audioAttr, variantSuffixStart)
        for variantAttr in variantAttrs:
            suffix = variantAttr.lstrip(audioAttr)
            variantAttr = enumAttr + str(suffix)
            variantAttrShortName = enumAttrShortName + str(suffix)
            setupEnumAttr(audioNamesSorted, nodeName, variantAttr, variantAttrShortName)


def _addNumericalAttr(attr, vals):
    # In case of variant attrs, need to check for whether the attr without a number is in the list of
    # either int or float attrs.
    base_attr = ''.join([i for i in attr if not i.isdigit()])
    if base_attr in INT_ATTRS or attr[len(attr)]:
        cmds.addAttr(longName=attr, attributeType='byte', keyable=True, hasMinValue=True,
                     hasMaxValue=True, hasSoftMinValue=True, hasSoftMaxValue=True,
                     minValue=vals["min"], maxValue=vals["max"], softMinValue=vals["min"],
                     softMaxValue=vals["max"], defaultValue=vals["default"])
    elif base_attr in FLOAT_ATTRS:
        cmds.addAttr(longName=attr, attributeType='float', keyable=True, hasMinValue=True,
                     hasMaxValue=True, hasSoftMinValue=True, hasSoftMaxValue=True,
                     minValue=vals["min"], maxValue=vals["max"], softMinValue=vals["min"],
                     softMaxValue=vals["max"], defaultValue=vals["default"])


def sortAudioEventsByTriggerTime(audioKeyframes):
    audioEvents = []
    triggerTimeToEventMapping = {}
    for audioKeyframe in audioKeyframes:
        audioEvent = audioKeyframe[EVENT_NAME_ATTR][0]
        triggerTime = audioKeyframe[TRIGGER_TIME_ATTR]
        if triggerTime in triggerTimeToEventMapping:
            cmds.warning("Found multiple audio events for trigger time %s ('%s' and '%s')"
                         % (triggerTime, triggerTimeToEventMapping[triggerTime], audioEvent))
        triggerTimeToEventMapping[triggerTime] = audioEvent
    triggerTimes = triggerTimeToEventMapping.keys()
    triggerTimes.sort()
    for triggerTime in triggerTimes:
        audioEvents.append((triggerTimeToEventMapping[triggerTime], triggerTime))
    return audioEvents


class AudioKeyframeChange(QObject):
    try:
        audio_keyframe_change = Signal()
    except NameError:
        audio_keyframe_change = None

    def broadcast(self):
        self.audio_keyframe_change.emit()

# The "Set Audio Event Trigger" UI will use the following instance of AudioKeyframeChange to
# broadcast a signal whenever an audio keyframe is updated. Meanwhile, the "Audio Settings" UI will
# use the following instance to listen for audio keyframe updates and refresh the displayed list of
# currently set audio event keyframes accordingly.

audio_keyframe_updated = AudioKeyframeChange()


