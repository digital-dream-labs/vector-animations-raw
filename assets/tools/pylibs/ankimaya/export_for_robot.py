
# We are using 30 fps in Maya, so the time of a single frame is 33.33 ms.  Because the engine is
# running on the robot's clock, it needs to be at 33.0 ms instead of 33.33 ms, so we scale time
# to 99% is to force the time of a single frame to be 33.0 ms.
TIME_SCALE_HACK = 0.99

# Python does a poor job of comparing floating point numbers because of
# precision. Therefore, we use this constant when comparing floating point values
# and checking for "equality". If the delta between two numbers is less than this
# value, then we consider them to be equal. This particular value (0.005) was
# chosen because of the scaleKey() behavior described in RemoveDuplicateKeyframes().
FLOAT_EQUALITY_TOLERANCE = 0.005

# The Maya rig allows the lift to rotate from 0 degrees (lowered) to -55.5 degrees (raised).
# The corresponding min/max height values are imported from robot_config.py below.
LIFT_ANGLE_MAX_RIG_DEG = -55.5
LIFT_ANGLE_MIN_RIG_DEG = 0.0

DEFAULT_TAR_FILE = "untitled.tar"

CLIP_NAME_KEY = "clip_name"

HIDE_USER_WARNINGS = "HIDE_USER_WARNINGS"

EXPORT_TO_ROBOT_ENV_VAR = "EXPORT_TO_ROBOT"
ROBOT_IP_ADDRESS_ENV_VAR = "ROBOT_IP_ADDRESS"

EVENT_CTRL = "x:event_ctrl"
EVENT_ENUM_ATTR = "event_trigger"

# We explicitly delete the following MentalRay nodes when exporting (COZMO-12578)
MENTAL_RAY_NODES = ['miDefaultOptions', 'miDefaultFramebuffer', 'mentalrayItemsList',
                    'mentalrayGlobals', 'mentalrayOptions', 'mentalrayFramebuffer']

RENDERING_PLUGINS = ["mtor", "Mayatomr"]

GRAPH_EDITOR = "graphEditor1FromOutliner"


import sys
import os
import traceback
import maya.cmds as cmds
import maya.mel as mel
import json
import tempfile
import tarfile
import copy
import pprint
from operator import itemgetter

from ankimaya import ctrs_manager
from ankimaya import exporter_config
from ankimaya.anim_data_manager import AnimDataManager
import ankimaya.json_exporter as je
import ankimaya.wheel_movement
import ankimaya.recorded_angle_turn
from ankimaya.curves_interpolation import CurvesInterpolation
from ankimaya.game_exporter import get_clip_info, get_num_clips
from ankimaya.robot_data import is_procedural_face_attr, add_procedural_face_keyframe, reset_children_cache
from ankimaya.robot_data import TRIGGER_TIME_KEY, DURATION_TIME_KEY
from ankimaya.audio_core import AUDIO_NODE_NAME, AUDIO_EVENT_ATTRS, AUDIO_EVENT_ATTRS_WITH_VARIATIONS
from ankimaya.audio_core import VARIANT_ATTR_SUFFIX_START_INDEX
from ankimaya.audio_core import VALUE_ATTR, CURVE_ATTR, PARAMETER_NAME_ATTR, STATE_ID_ATTR, TIME_MS_ATTR
from ankimaya.audio_core import STATE_GROUP_ID_ATTR, SWITCH_ID_ATTR, SWITCH_GROUP_ID_ATTR
from ankimaya.audio_core import PARAMETERS_ATTR, SWITCHES_ATTR, STATES_ATTR, EVENT_GROUPS_ATTR
from ankimaya.head_angle_selector import getHeadAngleVariationExportSettings
from ankiutils.head_angle_config import HeadAngleConfig, ANIM_VARIATION_SUFFIX
from ankiutils.head_angle_config import MIN_HEAD_ANGLE_DEG, MAX_HEAD_ANGLE_DEG
from ankiutils.check_anim_times import get_clip_length
from robot_config import LIFT_HEIGHT_MIN_ROBOT_MM, LIFT_HEIGHT_MAX_ROBOT_MM
from ankimaya.constants import DATA_NODE_NAME, HACK_TIMELINE_SCALE, ANIM_FPS
from ankimaya.export_error_check.error_checker_utils import add_json_node
from ankimaya.export_error_check.export_error_checker_ui import export_with_error_check


_msgs_for_user = []
_export_path_global = ""  # something like $HOME/workspace/cozmo-one/EXTERNALS/cozmo-assets/animations/


def adjust_lift_height_value(old_lift_height, idx):
    """
    In a previous version of the robot's rig for Maya, we incorrectly
    had the minimum lift angle of 0.0 degrees mapped to a lift height
    of 0.0 mm. That has since been corrected per COZMO-1582 since a
    fully lowered lift with an angle of 0.0 degrees is actually at
    lift height 32.0 mm.  For backwards compatibility, we convert the
    corrected lift height to the corresponding angle and then convert
    that angle back to height using the old incorrect mapping.
    """
    lift_angle = get_lift_angle_from_height(old_lift_height)
    new_lift_height = get_lift_height_from_angle(lift_angle, height_min=0.0)
    if new_lift_height < 0.0:
        new_lift_height = 0.0
    print("Lift height at idx %s was changed from %s mm to %s mm (angle = %s degrees)"
          % (idx, old_lift_height, new_lift_height, lift_angle))
    return new_lift_height


def get_lift_angle_from_height(height_mm,
                               height_min=LIFT_HEIGHT_MIN_ROBOT_MM, height_max=LIFT_HEIGHT_MAX_ROBOT_MM,
                               angle_min=LIFT_ANGLE_MIN_RIG_DEG, angle_max=LIFT_ANGLE_MAX_RIG_DEG):
    """
    An equation in the slope-intercept form is written as: y = mx + b
    Where "m" is the slope of the line and "b" is the y-intercept.
    For the lift, we have: height_mm = (slope * angle_deg) + intercept
                      and: angle_deg = (height_mm - intercept) / slope
    """
    slope = (height_min - height_max) / (angle_min - angle_max)
    intercept = height_min
    angle_deg = (height_mm - intercept) / slope
    return angle_deg


def get_lift_height_from_angle(angle_deg,
                               height_min=LIFT_HEIGHT_MIN_ROBOT_MM, height_max=LIFT_HEIGHT_MAX_ROBOT_MM,
                               angle_min=LIFT_ANGLE_MIN_RIG_DEG, angle_max=LIFT_ANGLE_MAX_RIG_DEG):
    """
    An equation in the slope-intercept form is written as: y = mx + b
    Where "m" is the slope of the line and "b" is the y-intercept.
    For the lift, we have: height_mm = (slope * angle_deg) + intercept
                      and: angle_deg = (height_mm - intercept) / slope
    """
    slope = (height_min - height_max) / (angle_min - angle_max)
    intercept = height_min
    height_mm = (slope * angle_deg) + intercept
    return height_mm


def enforce_head_angle_limits(angle_deg):
    if angle_deg > MAX_HEAD_ANGLE_DEG:
        angle_deg = MAX_HEAD_ANGLE_DEG
    elif angle_deg < MIN_HEAD_ANGLE_DEG:
        angle_deg = MIN_HEAD_ANGLE_DEG
    return angle_deg


def get_head_angle_keyframe_json(angle_deg, trigger_time_ms, duration_time_ms, angle_variability_deg=0):
    angle_deg = enforce_head_angle_limits(angle_deg)
    return {
        "angle_deg": int(round(angle_deg)),
        "angleVariability_deg": angle_variability_deg,
        TRIGGER_TIME_KEY: trigger_time_ms,
        DURATION_TIME_KEY: duration_time_ms,
        "Name": "HeadAngleKeyFrame",
    }


def set_export_path(item):
    global _export_path_global

    if not _export_path_global:
        # default to last temp file location
        _export_path_global = cmds.file(query=True, lastTempFile=True)
    filenames = cmds.fileDialog2(fileMode=3, caption="Export Directory")
    if filenames:
        _export_path_global = filenames[0]
        print("Anki Set: exported path is " + _export_path_global)
    else:
        print("ERROR: No directory selected")


def verify_export_path():
    global _export_path_global

    # Check if we've set something before this session.
    # If not, use a Maya.env variable or force user to pick.

    if not _export_path_global:
        _export_path_global = mel.eval("getenv ANKI_ANIM_EXPORT_PATH")
        if not _export_path_global:
            set_export_path(None)

    return _export_path_global


class JsonAnimClip(object):

    def __init__(self, clip_info, groupedAudioKeyframes, eventKeyframes, dataNodeName, time_scale,
                 problem_list):
        self.json_arr = []
        self.clip_info = clip_info
        self.clip_start = clip_info["clip_start"]
        self.clip_end = clip_info["clip_end"]
        self.head_angle_offset = clip_info.get("head_angle_offset", 0)
        self.head_angle_which_keyframes = clip_info.get("head_angle_which_keyframes", {})
        self.groupedAudioKeyframes = copy.deepcopy(groupedAudioKeyframes)
        self.eventKeyframes = eventKeyframes
        self.dataNodeName = dataNodeName
        if dataNodeName:
            anim_data_manager = AnimDataManager(dataNodeName, (self.clip_start/time_scale),
                                                (self.clip_end/time_scale))
            self.anim_data = anim_data_manager.anim_data  # {attr_name:{frame_num:value}}
            self.ctrs = ctrs_manager.get_all_connected_ctrs()
            if anim_data_manager.messages_for_user:
                anim_data_manager.messages_for_user.sort()
                problem_list.extend(anim_data_manager.messages_for_user)
        else:
            self.anim_data = {}
        self.problem_list = problem_list

    def fill_face_head_lift_data(self, first_head_angle_keyframe_offset=0,
                                       all_head_angle_keyframes_offset=0,
                                       last_head_angle_keyframe_offset=0):
        # We store the procedural anim as one keyframe with all params in the JSON file.
        # In maya they are stored as multiple params, we have this system for inserting them all.

        procFaceKeyframes = {}
        head_angle_keyframes = []
        unscaled_start_frame = self.clip_start / TIME_SCALE_HACK
        for curr_attr, frame_data in self.anim_data.iteritems():
            isProceduralFaceAttr = is_procedural_face_attr(curr_attr)
            frame_nums = frame_data.keys()
            frame_nums.sort()
            for idx in range(len(frame_nums)):
                trigger_time_ms = int(je.convert_time(frame_nums[idx]))
                if isProceduralFaceAttr:
                    if idx > 0 and abs(frame_nums[idx] - frame_nums[idx-1]) <= FLOAT_EQUALITY_TOLERANCE:
                        continue
                    add_procedural_face_keyframe(curr_attr, trigger_time_ms, 0,
                                                 frame_data[frame_nums[idx]],
                                                 (unscaled_start_frame + frame_nums[idx]),
                                                 self.dataNodeName, procFaceKeyframes,
                                                 frame_nums=frame_nums)

                elif (curr_attr in ["HeadAngle", "ArmLift"]) and (idx < len(frame_nums) - 1):
                    if abs(frame_nums[idx] - frame_nums[idx+1]) <= FLOAT_EQUALITY_TOLERANCE:
                        continue
                    self.add_head_lift_keyframe(idx, curr_attr, frame_data, frame_nums, trigger_time_ms,
                                                head_angle_keyframes, first_head_angle_keyframe_offset,
                                                all_head_angle_keyframes_offset, last_head_angle_keyframe_offset)
        if procFaceKeyframes:
            # Append the procedural face keyframes in order of trigger time...
            for trigger_time, keyframe in sorted(procFaceKeyframes.iteritems()):
                self.json_arr.append(keyframe)

    def is_last_keyframe(self, keyframe_idx, frame_nums, frame_data):
        keyframe_value = frame_data[frame_nums[keyframe_idx]]
        total_keyframes = len(frame_nums)
        idx = total_keyframes - 1
        while idx > keyframe_idx:
            last_val = frame_data[frame_nums[idx]]
            if last_val != keyframe_value:
                return False
            idx = idx - 1
        return True

    def add_head_lift_keyframe(self, idx, curr_attr, frame_data, frame_nums, trigger_time_ms,
                               head_angle_keyframes, first_head_angle_keyframe_offset=0,
                               all_head_angle_keyframes_offset=0, last_head_angle_keyframe_offset=0):
        if len(frame_nums) <= 1:
            return None
        if frame_nums[idx] not in frame_nums or frame_nums[idx+1] not in frame_nums:
            return None
        if (frame_data[frame_nums[idx]] == frame_data[frame_nums[idx+1]]) and (idx != 0):
            return None
        keyframe_value = frame_data[frame_nums[idx+1]]
        duration_time_ms = int(je.convert_time(frame_nums[idx+1], offset=frame_nums[idx]))
        curr = None
        if curr_attr == "HeadAngle":

            # If we have a value set for 'all_head_angle_keyframes_offset', then we simply offset
            # ALL head angle keyframes by that amount and we don't care if we have any values set
            # for 'first_head_angle_keyframe_offset' or 'last_head_angle_keyframe_offset'.
            #
            # If we have a value set for 'first_head_angle_keyframe_offset', then only the FIRST
            # head angle keyframe is offset by that amount and then all subsequent head angle
            # keyframes (possibly except for the last one) are calculated using the original delta
            # between the previous keyframe and the next one.
            #
            # If we have a value set for 'last_head_angle_keyframe_offset', then the LAST head angle
            # keyframe is offset by that amount. If not, then the last head angle keyframe might be
            # calculated using the original delta between the previous keyframe and this last one.
            #
            # TODO: Do we have any use cases where we want to offset all other head angle keyframes,
            # but we want the LAST head angle keyframe to exactly match the last head angle keyframe
            # from the original animation clip?

            if last_head_angle_keyframe_offset and not all_head_angle_keyframes_offset \
                       and self.is_last_keyframe(idx+1, frame_nums, frame_data):
                # This is the last head angle keyframe and we have an offset to apply
                offset_value = keyframe_value + last_head_angle_keyframe_offset
                offset_value = enforce_head_angle_limits(offset_value)
                head_angle_keyframes.append((keyframe_value, offset_value))
            elif first_head_angle_keyframe_offset and not all_head_angle_keyframes_offset:
                try:
                    prev_keyframe_value, prev_offset_value = head_angle_keyframes[-1]
                except IndexError:
                    # This is the first head angle keyframe and we have an offset to apply
                    offset_value = keyframe_value + first_head_angle_keyframe_offset
                else:
                    # Take the delta between this keyframe value and the previous one and then
                    # apply that to the previous offset value to get this offset value
                    delta = keyframe_value - prev_keyframe_value
                    offset_value = prev_offset_value + delta
                offset_value = enforce_head_angle_limits(offset_value)
                head_angle_keyframes.append((keyframe_value, offset_value))
            else:
                offset_value = keyframe_value + all_head_angle_keyframes_offset
            curr = get_head_angle_keyframe_json(offset_value, trigger_time_ms, duration_time_ms)
        elif curr_attr == "ArmLift":

            # As our exporter is currently designed, each lift keyframe in an animation is used as
            # the relative starting/trigger time for the next lift keyframe. As a result, we don't
            # export any keyframe that puts the lift at the height specified by the FIRST keyframe.
            # If we want to export a keyframe that achieves the lift height of the "first" keyframe
            # relative to the start of the animation, the animators must insert an extra keyframe
            # before that "first" one. For example, if they want to lower the arm lift at the start
            # of an animation, they can key the arm lift lowered at the first AND second frames of
            # the animation (or at the first and tenth frames if the lift happens to be raised when
            # the animation starts and they want it to be lowered more slowly). We could do this in
            # code by inserting an artificial keyframe at the start of the animation:
            #
            #if idx == 0 and trigger_time_ms > 0 and frame_data[frame_nums[idx]] != frame_data[frame_nums[idx+1]]:
            #    curr = {
            #        "height_mm": int(round(frame_data[frame_nums[idx]])),
            #        "heightVariability_mm": 0,
            #        "triggerTime_ms": 0,
            #        "durationTime_ms": trigger_time_ms,
            #        "Name": "LiftHeightKeyFrame"
            #    }
            #    self.json_arr.append(curr)
            #
            # However, we made a conscious decision to NOT insert that keyframe automatically and
            # leave it to the animators so they have more control over this.

            if exporter_config.get_adjust_lift_height():
                # We only want to call adjust_lift_height_value() here for old legacy Maya files
                # (see COZMO-1582 for details)
                keyframe_value = adjust_lift_height_value(keyframe_value, idx)

            curr = {
                "height_mm": int(round(keyframe_value)),
                "heightVariability_mm": 0,
                TRIGGER_TIME_KEY: trigger_time_ms,
                DURATION_TIME_KEY: duration_time_ms,
                "Name": "LiftHeightKeyFrame"
            }
        if curr is not None:
            self.json_arr.append(curr)

    def fill_audio_data(self, clip_name):
        # Grab the robot sounds from the main timeline or own node, not a datanode attribute
        try:
            (event_audio_json, problems) = je.get_audio_json(self.groupedAudioKeyframes, clip_name,
                                                             self.clip_start, self.clip_end)
        except ValueError, e:
            self.problem_list.extend(str(e).split(os.linesep))
            return None
        event_audio_json = sorted(event_audio_json, key=lambda k: k[TRIGGER_TIME_KEY])
        if problems:
            self.problem_list.extend(problems)
        if event_audio_json:
            self.json_arr.extend(event_audio_json)

    def fill_event_data(self):
        # Grab any event trigger data
        if self.eventKeyframes:
            event_json = je.get_event_json(self.eventKeyframes, self.clip_start, self.clip_end,
                                           self.problem_list)
            if event_json:
                self.json_arr.extend(event_json)

    def fill_lights_data(self):
        if self.dataNodeName:
            json_exporter = je.JsonExporter(self.clip_start, self.clip_end, self.dataNodeName)
            lights_json = json_exporter.get_backpack_lights_json()
            if lights_json:
                self.json_arr.extend(lights_json)

    def fill_movement_data(self):
        # Grab the robot movement relative to the curve
        if self.dataNodeName:
            # movement_json and wheel_movement_json have the same structure. The difference is in
            # which ctrs are being set in maya
            movement_json = je.get_movement_json(self.clip_start,
                                                 self.clip_end,
                                                 self.dataNodeName)

            wheel_movement = ankimaya.wheel_movement.WheelMovement()
            wheel_movement_json = wheel_movement.get_json(self.clip_start, self.clip_end)

            all_movement_json = []
            if movement_json:
                all_movement_json.extend(movement_json)
            if wheel_movement_json:
                all_movement_json.extend(wheel_movement_json)
            if all_movement_json:
                # Currently if node with earlier trigger time goes after the later one,
                # only the later one (that comes first in the file) gets triggered
                # We are sorting it by the trigger time to avoid that issue.
                all_movement_json = sorted(all_movement_json,
                                           key=lambda keyframe: keyframe[TRIGGER_TIME_KEY])

                rat = ankimaya.recorded_angle_turn.RecordedAngleTurn()
                return_to_recorded_json = rat.get_return_to_recorded_json(all_movement_json[-1],
                                                                          self.clip_start,
                                                                          self.clip_end)
                recorded_key_json = rat.get_recorded_key_json(self.clip_start, self.clip_end)

                if (return_to_recorded_json and recorded_key_json):
                    if rat.overwrite_last:
                        del all_movement_json[-1]
                    all_movement_json.append(return_to_recorded_json)
                    all_movement_json.append(recorded_key_json)

                self.problem_list.extend(wheel_movement.problem_list)
                self.json_arr.extend(all_movement_json)

    def fill_sprite_box_data(self):
        if self.dataNodeName:
            png_json = je.get_sprite_box_json(self.clip_start, self.clip_end)
            png_json = sorted(png_json, key=lambda k: k[TRIGGER_TIME_KEY])
            if png_json:
                self.json_arr.extend(png_json)

    def export(self, export_path, show_json=False):
        json_filename = None
        fileId = None
        clip_name = self.clip_info[CLIP_NAME_KEY]
        print("Exporting '%s'..." % clip_name)

        # If we set 'all_head_angle_keyframes_offset' to the offset value, ALL head angle keyframes
        # are offset by that amount.  Alternatively, if we set 'first_head_angle_keyframe_offset' to
        # the offset value, only the FIRST head angle keyframe is offset by that amount and then all
        # subsequent head angle keyframes are calculated using the original delta between the
        # previous keyframe and this one.  If we set 'last_head_angle_keyframe_offset' to the offset
        # value, the LAST head angle keyframe is offset by that amount.
        #
        keyframe_offsets = {}
        if self.head_angle_offset and self.head_angle_which_keyframes:
            for keyframe_to_offset in self.head_angle_which_keyframes:
                keyframe_offsets[keyframe_to_offset] = self.head_angle_offset
        self.fill_face_head_lift_data(**keyframe_offsets)

        if cmds.objExists(AUDIO_NODE_NAME):
            self.fill_audio_data(clip_name)
        if cmds.objExists(EVENT_CTRL):
            self.fill_event_data()
        self.fill_lights_data()
        self.fill_movement_data()
        #self.fill_sprite_box_data()

        if not self.json_arr:
            return None

        if clip_name:
            json_dict = {clip_name: self.json_arr}
            output_json = json.dumps(json_dict, sort_keys=False, indent=2, separators=(',', ': '))
            if not os.path.exists(export_path):
                os.makedirs(export_path)
            json_filename = os.path.join(export_path, clip_name + ".json")
            with open(json_filename, 'w') as fh:
                fh.write(output_json)
            if show_json:
                print(output_json)
            #print("The length of %s is %s ms" % (clip_name, get_clip_length(self.json_arr)))
        else:
            self.problem_list.append("Invalid clip name: %s" % clip_name)

        return json_filename


def _get_keyframe_list(node_name, attr_name, msgs=None):
    if not cmds.attributeQuery(attr_name, node=node_name, exists=True):
        return (None, None)
    fq_attr_name = node_name + "." + attr_name
    if cmds.mute(fq_attr_name, q=True):
        msg = "Skipping muted channel: %s" % fq_attr_name
        if isinstance(msgs, list):
            msgs.append(msg)
        #print(msg)
        return (None, None)
    vs = cmds.keyframe(node_name, attribute=attr_name, query=True, valueChange=True)
    ts = cmds.keyframe(node_name, attribute=attr_name, query=True, timeChange=True)
    return (vs, ts)


def get_keyframe_lists(node_name, attr_names, time_scale=None, attrs_with_variants_names=None,
                       variant_suffix_start=None, enum_attrs=None, msgs=None):
    lists_by_attr = {}
    if cmds.objExists(node_name):
        for attr_name in attr_names:
            lists_by_attr[attr_name] = _get_keyframe_list(node_name, attr_name, msgs)
            if attrs_with_variants_names and attr_name in attrs_with_variants_names:
                if not isinstance(variant_suffix_start, int):
                    msg = "'variant_suffix_start' should be an integer value, eg. 1 for " \
                          "'wwid1' or 2 for 'wwid2', not: %s" % variant_suffix_start
                    add_json_node(node_name="Getting Keyframe List",
                                  fix_function="", status="error",
                                  message=msg)
                    raise TypeError(msg)
                _add_attr_variant_lists(lists_by_attr, node_name, attr_name, variant_suffix_start, msgs)
        if enum_attrs is not None:
            lists_by_attr.update(get_enum_attrs(enum_attrs, node_name))
    return lists_by_attr


def get_enum_attrs(enum_attrs=None, node_name=AUDIO_NODE_NAME):
    lists_by_attr = {}
    attrs_by_time = {}
    enum_attrs_with_variants = []

    allAttrs = cmds.listAttr(node_name)
    for attr in allAttrs:
        for enum_attr in enum_attrs:
            if (attr[:len(enum_attr)] == enum_attr):
                enum_attrs_with_variants.append(attr)

    # Getting a dictionary of attr name by time, so that have to go through keyframes only once
    for attr_name in enum_attrs_with_variants:
        ts = cmds.keyframe(node_name, attribute=attr_name, query=True, timeChange=True)
        if ts is not None:
            for frame_num in ts:
                if frame_num not in attrs_by_time:
                    attrs_by_time[frame_num] = []
                attrs_by_time[frame_num].append(attr_name)

    # Going through keyframes and getting attributes, so that can get their names and then look up
    # their ids through dictionary, instead of looking up by index
    for frame_num in attrs_by_time.keys():
        cmds.currentTime(frame_num)
        for attr_name in attrs_by_time[frame_num]:
            if attr_name not in lists_by_attr:
                lists_by_attr[attr_name] = ([],[])
            value = cmds.getAttr("%s.%s" %(node_name, attr_name), asString=True)
            lists_by_attr[attr_name][0].append(value)
            lists_by_attr[attr_name][1].append(frame_num)

    return lists_by_attr


def _add_attr_variant_lists(lists_by_attr, node_name, attr_name, var_count, msgs=None):
    while True:
        attr_var_name = attr_name + str(var_count)
        vs, ts = _get_keyframe_list(node_name, attr_var_name, msgs)
        if vs is None and ts is None:
            return
        lists_by_attr[attr_var_name] = (vs, ts)
        var_count += 1


def create_export_package(output_files, tar_file=DEFAULT_TAR_FILE,
                          include_playblast=False, include_maya_file=False,
                          export_to_robot=False):
    msg = None
    package_files = output_files[:]
    scene_file = cmds.file(query=True, sceneName=True)
    if include_maya_file and scene_file:
        package_files.append(scene_file)
    if include_playblast:
        # Playblast scene, save that in a temp .mov file and then add
        # that .mov file to the exported package.
        temp_dir = tempfile.mkdtemp()
        mov_file = os.path.join(temp_dir, 'playblast.mov')
        cmds.playblast(format='movie', viewer=False, filename=mov_file,
                       forceOverwrite=True)
        package_files.append(mov_file)
    # Exported package (tar file) is named after the Maya scene file.
    scene_file_name = os.path.basename(scene_file)
    if scene_file_name:
        tar_file = os.path.splitext(scene_file_name)[0] + '.tar'
    tar_file_dir = mel.eval("getenv ANKI_ANIM_DIR")
    if not tar_file_dir:
        msg = "ERROR: No value set for ANKI_ANIM_DIR environment variable " \
              "(check your Maya.env file)"
        add_json_node(node_name="Export package",
                      fix_function="", status="error",
                      message=msg)
        tar_file_dir = _export_path_global
    if not os.path.exists(tar_file_dir):
        os.makedirs(tar_file_dir)
    tar_file = os.path.join(tar_file_dir, tar_file)
    tar = tarfile.open(tar_file, 'w')
    for output_file in package_files:
        tar.add(output_file, arcname=os.path.basename(output_file))
    tar.close()
    export_to_robot_env_var = os.getenv(EXPORT_TO_ROBOT_ENV_VAR)
    if export_to_robot or (export_to_robot_env_var and export_to_robot_env_var.lower() in ["true", "1"]):
        msg = convert_to_binary_and_send_to_robot(output_files, tar_file)
        add_json_node(node_name="Conversion to binary",
                      fix_function="", status="error",
                      message=msg)
    output_files.append(tar_file)
    return msg


def convert_to_binary_and_send_to_robot(json_files, tar_file, ip_address=None):
    msg = None
    import binary_conversion
    from ankimaya import preview_selector
    bin_name = os.path.splitext(os.path.basename(tar_file))[0] + binary_conversion.BIN_FILE_EXT
    bin_name = bin_name.lower()
    try:
        bin_file = binary_conversion.main(json_files, bin_name)
    except StandardError, e:
        print("%s: %s" % (type(e).__name__, e.message))
    else:
        if not ip_address:
            ip_address = os.getenv(ROBOT_IP_ADDRESS_ENV_VAR)
        if ip_address:
            try:
                preview_selector.transfer_file(ip_address, bin_file)
                preview_selector.update_animation(ip_address, bin_file)
                preview_selector.update_animation(ip_address, bin_file, engine=True)
            except RuntimeError, e:
                msg = str(e).split(os.linesep)[0]
            else:
                print("Transfered %s to %s" % (bin_file, ip_address))
        else:
            msg = "ERROR: No value set for '%s' environment variable" % ROBOT_IP_ADDRESS_ENV_VAR
            msg += " (check your Maya.env file)"
            print(msg)
    return msg


def add_head_angle_variations(clip_info, head_angle_offsets=None, head_angle_which_keyframes=None,
                              anim_variation_suffix=ANIM_VARIATION_SUFFIX):
    num_variations, which_keyframes = getHeadAngleVariationExportSettings()
    if num_variations < 1:
        return None
    if head_angle_offsets is None or head_angle_which_keyframes is None:
        head_angle_config = HeadAngleConfig()
        if head_angle_offsets is None:
            head_angle_offsets = head_angle_config.get_offsets(num_variations)
        if head_angle_which_keyframes is None:
            head_angle_which_keyframes = head_angle_config.get_which_keyframe_params(which_keyframes)
    for idx in range(len(clip_info)):
        clip = clip_info[idx]
        clip_name = clip[CLIP_NAME_KEY]
        for offset in head_angle_offsets:
            if not offset:
                continue
            offset_clip = copy.deepcopy(clip)
            offset_clip[CLIP_NAME_KEY] = clip_name + anim_variation_suffix % offset
            offset_clip["head_angle_offset"] = offset
            offset_clip["head_angle_which_keyframes"] = head_angle_which_keyframes
            clip_info.append(offset_clip)


def export_robot_anim(export_path=None, package_output=True, all_clips=False,
                      dataNodeName=DATA_NODE_NAME, time_scale=TIME_SCALE_HACK,
                      save_maya_file=True, show_json=False, verbose=True):
    global _msgs_for_user

    output_files = []
    _msgs_for_user = []

    print("Anki animation export started...")

    if not export_path:
        export_path = verify_export_path()

    # Reset the node's children cache in ankimaya.robot_data before calling get_clip_info()
    reset_children_cache()
    export_subdir, clip_names_updated, clip_info = get_clip_info(time_scale=time_scale,
                                                        default_name=DEFAULT_TAR_FILE.split('.')[0],
                                                        include_all=all_clips)
    num_orig_clips = len(clip_info)
    add_head_angle_variations(clip_info)
    pprint.pprint(clip_info, depth=2)

    if export_subdir:
        export_path = os.path.join(export_path, export_subdir)

    eventKeyframes = get_keyframe_lists(EVENT_CTRL, [EVENT_ENUM_ATTR], time_scale=time_scale,
                                        msgs=_msgs_for_user)

    # Grab the wwise audio data before we lock only to one layer.
    audioKeyframes = get_keyframe_lists(AUDIO_NODE_NAME, AUDIO_EVENT_ATTRS, time_scale=time_scale,
                                        attrs_with_variants_names=AUDIO_EVENT_ATTRS_WITH_VARIATIONS,
                                        variant_suffix_start=VARIANT_ATTR_SUFFIX_START_INDEX,
                                        msgs=_msgs_for_user)
    parameterKeyframes = get_keyframe_lists(AUDIO_NODE_NAME, [VALUE_ATTR, TIME_MS_ATTR],
                                            time_scale=time_scale,
                                            attrs_with_variants_names=[VALUE_ATTR, TIME_MS_ATTR],
                                            variant_suffix_start=VARIANT_ATTR_SUFFIX_START_INDEX,
                                            enum_attrs=[CURVE_ATTR,PARAMETER_NAME_ATTR],
                                            msgs=_msgs_for_user)
    stateKeyframes = get_keyframe_lists(AUDIO_NODE_NAME, [],
                                        time_scale=time_scale,
                                        attrs_with_variants_names=[],
                                        variant_suffix_start=VARIANT_ATTR_SUFFIX_START_INDEX,
                                        enum_attrs=[STATE_ID_ATTR, STATE_GROUP_ID_ATTR],
                                        msgs=_msgs_for_user)
    switchKeyframes = get_keyframe_lists(AUDIO_NODE_NAME, [],
                                         time_scale=time_scale,
                                         attrs_with_variants_names=[],
                                         variant_suffix_start=VARIANT_ATTR_SUFFIX_START_INDEX,
                                         enum_attrs=[SWITCH_ID_ATTR, SWITCH_GROUP_ID_ATTR],
                                         msgs=_msgs_for_user)

    if audioKeyframes:
        je.load_audio_to_globals()

    if len(cmds.ls(dataNodeName)) == 0:
        msg = "No '%s' available for export (check rig reference)" % dataNodeName
        add_json_node(node_name="Export",
                      fix_function="", status="warning",
                      message=msg)
        return output_files

    # group actions by keyframe, instead of by name

    num_clips = len(clip_info)
    for idx in range(num_clips):
        try:
            json_anim_clip = JsonAnimClip(clip_info[idx], {EVENT_GROUPS_ATTR:audioKeyframes,
                                                           PARAMETERS_ATTR:parameterKeyframes,
                                                           STATES_ATTR:stateKeyframes,
                                                           SWITCHES_ATTR:switchKeyframes},
                                                           eventKeyframes,
                                                           dataNodeName,
                                                           time_scale,
                                                           _msgs_for_user)
            json_filename = json_anim_clip.export(export_path, show_json)
        except:
            if idx < len(clip_info) and CLIP_NAME_KEY in clip_info[idx]:
                clip_name = clip_info[idx][CLIP_NAME_KEY]
                msg = "Failed to export anim clip: %s" % clip_name
            else:
                msg = "Unexpected error: %s" % sys.exc_info()[0]
            add_json_node(node_name="Export",
                          fix_function="", status="error",
                          message=msg)
            if verbose:
                traceback.print_exc(file=sys.stdout)
            continue
        if json_filename:
            output_files.append(json_filename)
        # Warnings that before were displayed in a dialogue box
        if json_anim_clip and json_anim_clip.problem_list:
            add_json_node(node_name="Export Warnings",
                          fix_function="", status="warning",
                          message=json_anim_clip.problem_list)

    tar_file_msg = None
    tar_msg_type = "pass"

    total_clips = get_num_clips()
    if package_output and total_clips and total_clips != num_orig_clips:
        package_output = False
        tar_file_msg  = "Tar file was not created since not all "
        tar_file_msg += "anim clips are enabled in Game Exporter"
        tar_msg_type = "warning"
    if tar_file_msg is None and num_clips != len(output_files):
        package_output = False
        tar_file_msg  = "Tar file was not created since not all anim clips "
        tar_file_msg += "were successfully exported"
        tar_msg_type = "warning"

    if save_maya_file or clip_names_updated:
        # Save the Maya scene file if this is an interactive export or if any of
        # the clip names were updated by get_clip_info().
        cmds.select(clear=True)
        try:
            cmds.file(save=True, type='mayaAscii', prompt=False)
        except (RuntimeError, OSError), e:
            msg = str(e).strip().split(os.linesep)
            add_json_node(node_name="File saving",
                          fix_function="", status="warning",
                          message=msg)
        else:
            add_json_node(node_name="File saving",
                          fix_function="", status="pass",
                          message="File saved successfully")

    if package_output and output_files:
        # Create an export package (.tar file) that contains exported .json files
        # and potentially the .ma scene file and a playblast .mov file.
        create_export_package(output_files)

    if output_files:
        print(os.linesep + "The following files were exported:")
        print(os.linesep.join(output_files) + os.linesep)
        print "Export complete",
    else:
        print os.linesep + "No files were exported",

    if tar_file_msg:
        add_json_node(node_name="Tar file",
                      fix_function="", status=tar_msg_type,
                      message=tar_file_msg)
    return output_files


def exportRobotAnim(menuArg=None, skipErrorChecking=False, nodesToDelete=MENTAL_RAY_NODES,
                    unknownPluginsToRemove=RENDERING_PLUGINS,
                    selectionSetName="selected_controllers_set"):
    """
    By default, this function will delete MentalRay nodes in the
    scene, but that behavior can be disabled by passing in an
    empty list or None for the 'nodesToDelete' argument.
    """

    # delete Mental Ray nodes
    if nodesToDelete:
        for node in nodesToDelete:
            _safeDelete(node)

    # remove dependency on mtor plugin
    if unknownPluginsToRemove:
        for unknownPlugin in unknownPluginsToRemove:
            try:
                cmds.unknownPlugin(unknownPlugin, remove=True)
            except RuntimeError:
                pass

    # lock the selections in the graph editor and make a list of the highlighted ones
    cmds.selectionConnection(GRAPH_EDITOR, e=True, lock=True)
    curvesHighlighted = cmds.selectionConnection(GRAPH_EDITOR, q=True, object=True)

    # make a set to select as a single node later
    _safeDelete(selectionSetName)
    setName = cmds.sets(name=selectionSetName)
    # make a list of all the selected keys
    keysSelected = _getSelectedKeys()

    try:
        if skipErrorChecking:
            export_robot_anim()
        else:
            export_with_error_check(export_robot_anim)
    finally:
        try:
            _restoreSelection(selectionSetName, curvesHighlighted, keysSelected)
        except:
            print("Warning: problem encountered while restoring previous selection set")


def _restoreSelection(selectionSetName, curvesHighlighted, keysSelected):
    # eval deferred because of maya is still doing UI things in the background
    # after this script runs and we need to wait until its done its UI updating
    if cmds.objExists(selectionSetName):
        cmds.evalDeferred("cmds.select('%s', replace=True)" % selectionSetName, lowestPriority=True)

    cmdStr  = "cmds.selectionConnection('%s', e=True, lock=False);" % GRAPH_EDITOR
    cmdStr += "cmds.selectionConnection('%s', e=True, cl=True); " % GRAPH_EDITOR

    if curvesHighlighted:
        for c in curvesHighlighted:
            cmdStr += "cmds.selectionConnection('{1}', e=True, select='{0}'); ".format(str(c), GRAPH_EDITOR)

    cmds.evalDeferred(cmdStr, lowestPriority=True)
    _reselectKeys(keysSelected)
    cmds.evalDeferred("if cmds.objExists('%s'):    cmds.delete('%s')"
                      % (selectionSetName, selectionSetName), lowestPriority=True)


def _getSelectedKeys():
    """
    This function returns a dictionary of selected keys. That dictionary
    can be used to reselect the keys at the end of the export process.
    """
    # TODO the user might be using a graphEditor that doesnt have the standard name
    reselectKeys = []
    for obj in cmds.ls(sl=True):
        nodes = cmds.keyframe(obj, query=True, name=True)
        if nodes:
            for node in nodes:
                keyTimes = cmds.keyframe(node, sl=True, query=True, indexValue=True)
                if keyTimes:
                    data = {"obj": obj, "node": node, "keys": keyTimes}
                    reselectKeys.append(data)
    return reselectKeys


def _reselectKeys(data):
    """
    this reselects the keys (and their curve) that were
    selected when the export_robot_anim script started
    :param data : dictionary with keys called "node" and and array "keys"
    the keys are indices, not time
    """
    if not data:
        return
    allStr = ''
    for o in data:
        for k in o['keys']:
            pstr = "cmds.selectKey(\"{0}\", k=True, index=({1},{1}), add=True); ".format(o['node'], k)
            allStr += pstr
    # maya is still doing something in the background at the end of the export script so we
    # have to make sure it waits til its done
    cmds.evalDeferred(allStr, lowestPriority=True)


def _safeDelete(obj):
    if cmds.objExists(obj):
        cmds.delete(obj)
        print("deleted {0}".format(obj))


