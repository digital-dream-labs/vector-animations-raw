"""
Collection of functions to be run pre and post export to check if the scene
has any incompatibilities with the export.
"""

import ast
import copy
import json
import os
import re
import maya.cmds as mc
import ankimaya.export_error_check.error_checker_utils as utils
from ankimaya.exporter_config import getExporterVersion
from ankimaya.eye_keyer import are_eye_attrs_keyed
from ankimaya.game_exporter import GAME_EXPORTER_PRESET
import ankimaya.wheel_movement as wm


KEYS_THRESHHOLD = 0.1

# These are the base message dictionaries, that are being displayed by default, if no problems are
# encountered during the check

# PRE EXPORT DICTS

RIG_REFERENCE_DICT = {"name": "Rig reference",
                      "tool_tip": "Is the rig referenced in the scene",
                      "fix_function": "",
                      "status": "pass",
                      "message": "The default rig is referenced"}

FRAME_RATE_DICT = {"name": "Frame rate",
                   "tool_tip": "What is the scene's frame rate",
                   "fix_function": "",
                   "status": "pass",
                   "message": "Frame rate in the scene is at default 30fps"}

CHECK_CLIPS_DICT = {"name": "Animation clips",
                    "tool_tip": "Checks for animation clips in the scene.",
                    "fix_function": "",
                    "status": "",
                    "message": ""}

EXPORTER_VERSION_DICT = {"name": "Exporter version",
                         "tool_tip": "Which version of the exporter were the clips last exported with",
                         "fix_function": "",
                         "status": "",
                         "message": ""}

MAYA_VERSION_DICT = {"name": "Maya version",
                     "tool_tip": "Is maya version correct",
                     "fix_function": "",
                     "status": "",
                     "message": ""}

WHEEL_FRAMES_DICT = {"name": "Wheel frames",
                     "tool_tip": "Are both of the wheels keyed",
                     "fix_function": "",
                     "status": "pass",
                     "message": "Both weels are keyed on every frame and start from a value of 0"}

EYE_KEYS_DICT = {"name": "Eyes",
                 "tool_tip": "Are all eye attrs keyed",
                 "fix_function": "",
                 "status": "pass",
                 "message": "Eye attributes' keyframes are aligned"}

KEYS_CLOSE_TOGETHER_DICT = {"name": "Treshhold between keyframes",
                            "tool_tip": "Are there keyframes that are positioned too close together",
                            "fix_function": "",
                            "status": "pass",
                            "message": "All keyframes are positioned further apart then %s" % (
                                KEYS_THRESHHOLD)}

# POST EXPORT DICTS

SAME_TRIGGER_TIME = {"name": "Identical trigger time",
                     "tool_tip": "Are there keyframes with the same trigger time",
                     "fix_function": "",
                     "status": "pass",
                     "message": "There are no identical trigger times on the nodes with the same name"}

VICTOR_BACKPACK = {"name": "Backpack lights",
                   "tool_tip": "Are there keyframes with the same trigger time",
                   "fix_function": "",
                   "status": "pass",
                   "message": "There are either no backpack keys or you are not using Vector rig"}

PRE_EXPORT_TYPE2CHECK = {"Animation": ["check_rig_reference(\"%s\")", "check_frame_rate()",
                                       "check_clips_in_scene()", "check_exporter_version()",
                                       "check_maya_version(\"%s\")", "check_wheel_keys()",
                                       "check_eye_keys()", "check_keys()"]}

POST_EXPORT_TYPE2CHECK = {"Animation": ["check_same_trigger_time(\"%s\")",
                                        "check_vector_backpack(anim_jsons, char_name)"]}

BACKPACK_CTR = "x:backpack_ctrl"
BACKPACK_KEYFRAME_NAME = "BackpackLightsKeyFrame"

MESSAGE_STR = "message"
STATUS_STR = "status"
FIX_FUNCTION_STR = "fix_function"
TOOL_TIP_STR = "tool_tip"

PASS_STR = "pass"
WARNING_STR = "warning"
ERROR_STR = "error"


def run_pre_export_checks():
    """
    Generate dictionary of pre-export data
    """
    pre_export_dict = dict()
    char_name = utils.get_char_name()

    for type, checks in PRE_EXPORT_TYPE2CHECK.iteritems():
        pre_export_dict[type] = []
        for check in checks:
            if "%s" in check:
                check = check % char_name

            pre_export_dict[type].append(eval(check))

        utils.write_checks_to_json("Pre Export", pre_export_dict)


def run_post_export_checks(anim_jsons):
    """
    Generate dictionary of post-export data. Works only if exported json files are passed
    """
    anim_jsons = utils.update_anim_jsons(anim_jsons)
    post_export_dict = dict()
    char_name = utils.get_char_name()

    for type, checks in POST_EXPORT_TYPE2CHECK.iteritems():
        post_export_dict[type] = []
        for check in checks:
            if "%s,%s" in check:
                check = check % (anim_jsons, char_name)
            elif "%s" in check:
                check = check % anim_jsons

            post_export_dict[type].append(eval(check))

    utils.write_checks_to_json("Post Export", post_export_dict)

# PRE EXPORT CHECKS

def check_wheel_keys():
    """
    Check for the speed limits, and whether wheel keyframes are aligned
    """
    json_dict = copy.deepcopy(WHEEL_FRAMES_DICT)
    wheel_movement = wm.WheelMovement()
    messages = []
    exceed_limits_frames = wheel_movement.do_speeds_exceed_limits()
    if exceed_limits_frames:
        messages.append("Speeds exceed limits on frames: %s" % exceed_limits_frames)
        json_dict[FIX_FUNCTION_STR] = "fix_wheel_keys(message)"
        json_dict[TOOL_TIP_STR] += os.linesep + "Fix will clamp speeds at problem keyframes"
        json_dict[STATUS_STR] = WARNING_STR
    if not wm.are_wheels_keyed():
        messages.append("No frames on one or both separate wheels")
        json_dict[STATUS_STR] = WARNING_STR
        json_dict[FIX_FUNCTION_STR] = ""
    else:
        if not wm.are_all_frames_on_wheels():
            messages.append("Wheels are not keyed on every frame")
            json_dict[STATUS_STR] = WARNING_STR
            json_dict[FIX_FUNCTION_STR] = "fix_wheel_keys(message)"
            json_dict[TOOL_TIP_STR] += "\nFix will add keyframes to wheels where one is not keyed"

        if not wm.do_wheels_start_from_zero():
            messages.append("Wheels don't start from the value of 0 - robot's movement may not" \
                            " be evaluated as expected")
            json_dict[STATUS_STR] = WARNING_STR
            json_dict[FIX_FUNCTION_STR] = "fix_wheel_keys(message)"
            json_dict[TOOL_TIP_STR] += "\nFix will overwrite the values on the first on the wheel" \
                                       "frames and set them to 0"
    if messages:
        json_dict[MESSAGE_STR] = "\n".join(messages)
    return json_dict


def check_eye_keys():
    """
    Check if eye keys are aligned
    """
    json_dict = copy.deepcopy(EYE_KEYS_DICT)
    message = are_eye_attrs_keyed()
    # If there are problems with eyes are_eye_attrs_keyed returns a message, otherwise returns True
    if message and message!=True:
        json_dict[STATUS_STR] = WARNING_STR
        json_dict[MESSAGE_STR] = message
        # If controller doesn't exist or if no eye controllers are keyed should not offer any fix.
        if "doesn't exist" in message:
            json_dict[TOOL_TIP_STR] += "\nThere is no fix for absence of controllers." \
                                       "Please make sure that rig is referenced with all" \
                                       " the correct controllers"
        elif "No eye controllers are keyed" in message:
            json_dict[TOOL_TIP_STR] += "\nThere is no fix for this warning." \
                                       "If you wish to animate eyes, please set keyframes on at" \
                                       " least one of the eye controllers"

        else:
            json_dict[FIX_FUNCTION_STR] = "fix_eye_keyframes()"
            json_dict[
                TOOL_TIP_STR] += "\nThe fix will place keyframes on all eye controllers on each" \
                                 " frame where there is any eye controller keyframe"

    return json_dict


def check_rig_reference(char_name):
    """
    Check if the correct rig has been referenced
    """
    json_dict = copy.deepcopy(RIG_REFERENCE_DICT)

    if not mc.objExists(utils.CHARS[char_name][3]):
        json_dict[MESSAGE_STR] = "%s does not exist in the scene." \
                                 " Please make sure you have a rig referenced with a correct" \
                                 " namespace" % utils.CHARS[char_name][3]
        add_rig_fix(json_dict, char_name)
        json_dict[STATUS_STR] = ERROR_STR
    elif not mc.referenceQuery(utils.CHARS[char_name][3], isNodeReferenced=True):
        json_dict[MESSAGE_STR] = "Rig is not referneced in the scene"
        json_dict[STATUS_STR] = ERROR_STR
        add_rig_fix(json_dict, char_name)
    else:
        try:
            rig_path = mc.referenceQuery(utils.CHARS[char_name][3], filename=True)
        except StandardError, e:
            json_dict[MESSAGE_STR] = "Cannot find reference.\n%s" % (e)
            json_dict[STATUS_STR] = ERROR_STR
            add_rig_fix(json_dict, char_name)
            return json_dict

        if utils.VECTOR_RIG_PATH != rig_path and utils.CHARS[char_name][1] not in rig_path:
            json_dict[MESSAGE_STR] = "The default rig is %s." \
                                     "\nYou have %s rig referenced" % (
                                         utils.CHARS[char_name][1], rig_path.split("/")[-1])
            json_dict[STATUS_STR] = WARNING_STR
            add_rig_fix(json_dict, char_name)
        elif utils.CHARS[char_name][2] != rig_path:
            json_dict[MESSAGE_STR] = "The default rig is positioned in %s.\n" \
                                     "You are referencing a rig from a different path %s" % (
                                         utils.CHARS[char_name][2], rig_path)
            json_dict[STATUS_STR] = WARNING_STR
            add_rig_fix(json_dict, char_name)

    return json_dict


def add_rig_fix(json_dict, char_name):
    json_dict[FIX_FUNCTION_STR] = "fix_rig_reference()"
    json_dict[TOOL_TIP_STR] += "\nFix will import %s rig into the scene. Use with caution!" % (
    utils.CHARS[char_name][3])


def check_frame_rate():
    """
    Check if the frame rate is correct
    """
    json_dict = copy.deepcopy(FRAME_RATE_DICT)
    try:
        frame_rate_type = mc.currentUnit(query=True, time=True)
    except StandardError, e:
        json_dict[MESSAGE_STR] = "Cannot get frame rate.\n%s" % (e)
        json_dict[STATUS_STR] = ERROR_STR
        return json_dict

    if not frame_rate_type == "ntsc":
        json_dict[MESSAGE_STR] = "The frame rate is set to %s, not ntsc (30fps)" % frame_rate_type
        json_dict[STATUS_STR] = ERROR_STR
        json_dict[FIX_FUNCTION_STR] = "fix_frame_rate()"
        json_dict[TOOL_TIP_STR] += "Fix will set the framerate to ntsc (30fps)"
    return json_dict


def check_clips_in_scene():
    """
    Check if clips are in the scene and are named correctly
    """
    json_dict = copy.deepcopy(CHECK_CLIPS_DICT)

    if not mc.objExists(GAME_EXPORTER_PRESET):
        json_dict[
            MESSAGE_STR] = "Game exporter preset doesn't exist in this scene. Using game exporter" \
                           " and adding clips will automatically create it."
        json_dict[STATUS_STR] = ERROR_STR
    else:
        try:
            clips_num = mc.getAttr(GAME_EXPORTER_PRESET + '.ac', size=True)
        except StandardError:
            json_dict[MESSAGE_STR] = "Cannot find the number of exporter clips"
            json_dict[STATUS_STR] = ERROR_STR
            json_dict[TOOL_TIP_STR] += "\nTo fix please go to File->Game Exporter"
            return json_dict

        if clips_num == 0:
            json_dict[MESSAGE_STR] = "There are no clips (%s) in this scene" % (clips_num)
            json_dict[STATUS_STR] = WARNING_STR
            json_dict[TOOL_TIP_STR] += "\nTo fix please go to File->Game Exporter"
        elif clips_num < 0:
            json_dict[MESSAGE_STR] = "Incorrect clip number: %s" % (clips_num)
            json_dict[STATUS_STR] = WARNING_STR
        else:
            clip_names = []
            for num in range(0, clips_num):
                clip_name = mc.getAttr(GAME_EXPORTER_PRESET + '.ac[%s].acn' % num)
                clip_names.append(clip_name)
            if None in clip_names:
                json_dict[
                    MESSAGE_STR] = "There are unnamed animation clips. Please name all the clips"
                json_dict[TOOL_TIP_STR] += "\nTo fix please go to File->Game Exporter"
                json_dict[STATUS_STR] = ERROR_STR
            elif check_clips_names(json_dict, clip_names):
                json_dict[MESSAGE_STR] = "The following scene has %s clips:\n%s" % (
                    clips_num, "\n".join(clip_names))
                json_dict[STATUS_STR] = PASS_STR
    return json_dict


def check_clips_names(json_dict, clip_names):
    no_lowercase = []
    no_anim_underscore = []
    wrong_end = []
    wrong_chars = []
    messages = []

    for clip_name in clip_names:
        if not clip_name.islower():
            no_lowercase.append(clip_name)
        if not re.match("^[a-zA-Z0-9_]*$", clip_name):
            wrong_chars.append(clip_name)
        if "_" not in clip_name:
            no_anim_underscore.append(clip_name)
        else:
            if clip_name.split("_")[0] != "anim":
                no_anim_underscore.append(clip_name)
            if not (clip_name.split("_")[-1].isdigit() and len(clip_name.split("_")[-1]) == 2):
                wrong_end.append(clip_name)

    if wrong_chars:
        messages.append("Following clip(s) have invalid characters:\n%s" % ("\n".join(wrong_chars)))

    if no_lowercase:
        messages.append("Following clip(s) are not lowercase:\n%s" % ("\n".join(no_lowercase)))

    if no_anim_underscore:
        messages.append(
            "Following clip(s) don't start with \"anim_\":\n%s" % ("\n".join(no_anim_underscore)))
    if wrong_end:
        messages.append("Following clip(s) have wrong ending:\n%s" % ("\n".join(wrong_end)))
        json_dict[TOOL_TIP_STR] = "Clips need to end with underscore followed by a two digit number"

    if messages:
        json_dict[MESSAGE_STR] = "\n\n".join(messages)
        json_dict[STATUS_STR] = WARNING_STR
    else:
        return True


def check_maya_version(char_name):
    """
    Check the version of maya based on the name of the character from env file
    """
    json_dict = copy.deepcopy(MAYA_VERSION_DICT)
    version = mc.about(version=True)
    if int(version) == utils.CHARS[char_name][0]:
        json_dict[MESSAGE_STR] = "Maya is set to version %s" % version
        json_dict[STATUS_STR] = PASS_STR
    else:
        json_dict[MESSAGE_STR] = "Maya is set to version %s, expecting %s" % (
            version, utils.CHARS[char_name][0])
        json_dict[STATUS_STR] = WARNING_STR
    return json_dict


def check_keys():
    """
    Check if the keys exist and if they are positioned too close together
    """
    json_dict = copy.deepcopy(KEYS_CLOSE_TOGETHER_DICT)
    messages = []
    anim_curves = utils.get_anim_curves()
    for anim_curve in anim_curves:
        all_key_times = mc.keyframe(anim_curve, query=True, timeChange=True)
        if all_key_times:
            for i in range(1, len(all_key_times)):
                if all_key_times[i] - all_key_times[i - 1] <= KEYS_THRESHHOLD:
                    message = "Keyframes %s and %s of %s are closer together than %s" % (
                        all_key_times[i], all_key_times[i - 1], anim_curve, KEYS_THRESHHOLD)
                    messages.append(message)
    if messages:
        json_dict[MESSAGE_STR] = "\n".join(messages)
        json_dict[STATUS_STR] = WARNING_STR
        json_dict[FIX_FUNCTION_STR] = "fix_threshold()"
        json_dict[TOOL_TIP_STR] = "A fix will remove each next keyframe"
    return json_dict


def check_exporter_version():
    json_dict = copy.deepcopy(EXPORTER_VERSION_DICT)
    try:
        exporter_version = getExporterVersion()
    except StandardError, e:
        json_dict[MESSAGE_STR] = "Cannot find exporter version.\n%s" % e
        json_dict[STATUS_STR] = ERROR_STR
        return json_dict

    if exporter_version:
        json_dict[MESSAGE_STR] = "Current file is set to an exporter version %s." % exporter_version
        json_dict[STATUS_STR] = WARNING_STR
    else:
        json_dict[MESSAGE_STR] = "Latest exporter version will be used."
        json_dict[STATUS_STR] = PASS_STR

    return json_dict


# POST EXPORT CHECKS

def check_same_trigger_time(anim_jsons):
    json_dict = copy.deepcopy(SAME_TRIGGER_TIME)
    anim_jsons = ast.literal_eval(anim_jsons)
    messages = []
    for anim_json in anim_jsons:
        # need to exclude non-json (tar) files
        if anim_json.split(".")[-1] == "json":
            name_trigger_times = []
            # create list of [[name,trigger_time]] of each node to then check for repetition
            with open(anim_json, "r+") as data_file:
                data = json.load(data_file)
                for node in data.values()[0]:
                    name_trigger_times.append([node["Name"], node["triggerTime_ms"]])

            for sub_name_trigger_time in name_trigger_times:
                keyframe_nums = name_trigger_times.count(sub_name_trigger_time)
                if keyframe_nums > 1:
                    msg = "%s has %s keyframes on %s with trigger time %s" % (anim_json.split("/")[-1],\
                                                                              keyframe_nums,\
                                                                              sub_name_trigger_time[0],\
                                                                              sub_name_trigger_time[1])
                    if msg not in messages:
                        messages.append(msg)

    if messages:
        json_dict[MESSAGE_STR] = "\n\n".join(messages)
        json_dict[STATUS_STR] = WARNING_STR

    return json_dict


def check_vector_backpack(anim_jsons, char_name):
    json_dict = copy.deepcopy(VICTOR_BACKPACK)
    if char_name == "victor":
        for anim_json in anim_jsons:
            # filnd if there is a node with a name backpack
            with open(anim_json, "r+") as data_file:
                data = json.load(data_file)
                for node in data.values()[0]:
                    if node["Name"] == BACKPACK_KEYFRAME_NAME:
                        json_dict[MESSAGE_STR] = "Vector is not using backpack lights, and those" \
                                                 " keyframes will not be read by the robot"
                        json_dict[STATUS_STR] = WARNING_STR
                        return json_dict
    else:
        json_dict[MESSAGE_STR] = "You are not using victor rig. Backpack keyframes are allowed"
    return json_dict


