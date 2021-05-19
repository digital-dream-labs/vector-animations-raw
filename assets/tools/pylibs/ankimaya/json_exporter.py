
# This module should eventually have all the different JSON exporting functions.
# Most of that functionality is here now, but it could be organized better, so this should be refactored.
# When this is refactored, we should consider moving this code into the "ankimaya.robot_data" module.

import os
import copy
import math
import re
import maya.cmds as cmds
from ankimaya import ctrs_manager
from ankimaya.anim_data_manager import AnimDataManager, FLOAT_EQUALITY_TOLERANCE
from ankimaya.audio_core import loadAudioAttrsFromPy, getDefaultAudioJson, balanceLoopingEvents
from ankimaya.audio_core import DEFAULT_PARAMS_DICT, DEFAULT_EMPTY_AUDIO_JSON
from ankimaya.audio_core import AUDIO_NODE_NAME, AUDIO_ENUM_ATTR, EVENT_NAME_ATTR, EVENT_IDS_ATTR
from ankimaya.audio_core import AUDIO_PARAMETER_TYPES, AUDIO_STATE_TYPES, AUDIO_SWITCH_TYPES
from ankimaya.audio_core import TRIGGER_TIME_ATTR, VOLUME_ATTR, PROB_ATTR, CURVE_TYPES, TIME_MS_ATTR
from ankimaya.audio_core import DEFAULT_AUDIO_EVENT, AUDIO_ATTR_CONVERSION, STATES_ATTR, EVENT_GROUPS_ATTR
from ankimaya.audio_core import PARAMETERS_ATTR, PARAMETER_ID_ATTR, CURVE_ATTR, SWITCHES_ATTR, INT_ATTRS
from ankimaya.audio_core import SWITCH_GROUP_ID_ATTR, STATE_ID_ATTR, STATE_GROUP_ID_ATTR, STATE_ID_ATTR
from ankimaya.audio_core import VOLUMES_ATTR, PROBABILITIES_ATTR, TOP_LEVEL_ENUM_ATTRS, SUB_LEVEL_ENUM_ATTRS
from ankimaya.audio_core import AUDIO_ACTION_TO_GROUP_DICT, DEFAULT_VOLUME, DEFAULT_PROBABILITY
from robot_config import MAX_WHEEL_SPEED_MMPS, MAX_BODY_ROTATION_SPEED_DEG_PER_SEC, MIN_RADIUS_MM, MAX_RADIUS_MM
from ankimaya import exporter_config
from ankimaya.constants import DATA_NODE_NAME, HACK_TIMELINE_SCALE, ANIM_FPS, EVENT_CTRL, EVENT_ENUM_ATTR
from ankimaya.export_error_check.error_checker_utils import add_json_node

BACKPACK_LIGHT_JSON_NODE = {"Name": "BackpackLightsKeyFrame",
                            "Back": [0.0, 0.0, 0.0, 0.0],
                            "Front": [0.0, 0.0, 0.0, 0.0],
                            "Middle": [0.0, 0.0, 0.0, 0.0],
                            "Left": [0.0, 0.0, 0.0, 0.0],
                            "Right": [0.0, 0.0, 0.0, 0.0],
                            "durationTime_ms": 0,
                            "triggerTime_ms": 0}

AUDIO_ATTR_TO_JSON_ATTR = {"volume": "volumes",
                           "timeMs": "time_ms",
                           "probability": "probabilities",
                           "WwiseIdEnum": "eventIds",
                           "curveType": "curveType",
                           "parameterName": "parameterID",
                           "value": "value",
                           "stateName": "stateName",
                           "switchName": "stateName",
                           "stateGroupId": "stateGroupId",
                           "switchGroupId": "switchGroupId"}

AUDIO_ACTION_DEFAULT_DICT = {"parameters": {"curveType": 0,
                                            "time_ms": 0,
                                            "parameterID": 0,
                                            "value": 0.0},
                             "switches": {"switchGroupId": 0,
                                          "stateName": 0},
                             "states": {"stateName": 0,
                                        "stateGroupId": 0}
                             }

ROBOT_RIG_FILE = "assets/rigs/Victor_rig_01.ma"

EVENT_ENUM_PROB_MSG = "Check the '%s' enum attribute on " % EVENT_ENUM_ATTR
EVENT_ENUM_PROB_MSG += "the '%s' node in " % EVENT_CTRL.lstrip("x:")
EVENT_ENUM_PROB_MSG += "%s (in the '<project>-animation' SVN repo). " % ROBOT_RIG_FILE
EVENT_ENUM_PROB_MSG += "Make sure that nothing has been deleted from the enum "
EVENT_ENUM_PROB_MSG += "list and that it hasn't been reordered."

FACIAL_ANIMATION_EVENT = "facial_animation"
FACIAL_ANIMATION_ATTR = "pngSequence"


g_AudioIDs = {}
g_AudioEventNamesSorted = []
g_allAudioActionIds = {} #{"action":["name":id]}


def get_straight_movement_speed(fwd_distance, time_in_seconds):
    """
    Given the distance and time of a straight forward/backward
    body movement, this function should return the speed of that
    movement. This function primarily exists for querying the
    desired exporter version for the Maya scene and providing an
    incorrect result for an old version of the exporter, where
    the distance rather than the speed is returned.
    See COZMO-1582 for some additional info.
    """
    # In the Cozmo rig (Cozmo_midRes_rig.ma), the "Forward" attribute is hooked up
    # to a 'unitConversion' node with a conversion factor of 10 - that converts
    # centimeters to millimeters and we are using millimeters here.

    if exporter_config.get_use_distance_for_speed():
        # In this version, the "speed" value holds the DISTANCE for a STRAIGHT movement! This
        # code is storing the distance in the "speed" value, but the robot engine is (correctly)
        # interpreting it as speed, not distance. This sort of "works" since distance and speed
        # are proportionate over a fixed time, but we should be setting the speed in
        # millimeters/second instead of the distance in millimeters, so that was eventually fixed
        # per COZMO-1582 (see the following 'else' clause).
        speed = fwd_distance
    else:
        # For backwards compatibility, we only want to use this correct speed calculation
        # for new Maya files, NOT for any old legacy Maya files (COZMO-1582)
        speed = fwd_distance / time_in_seconds
    return int(round(speed))


def convert_time(time, offset=0):
    # Does this function belong in a separate util module?
    time -= offset
    time = time * 1000 / ANIM_FPS
    time = int(round(time, 0))
    return time


def scale_frame(frame_num, start_frame):
    return (frame_num - start_frame) * HACK_TIMELINE_SCALE


def unscale_frame(frame):
    unscaled = frame / HACK_TIMELINE_SCALE
    return unscaled


def is_equal(float1, float2, float_equality_tolerance=FLOAT_EQUALITY_TOLERANCE):
    """
    Python does a poor job of comparing floating point numbers
    because of precision.  Therefore, we use this function when
    comparing floating point values and checking for "equality".
    If the delta between two numbers is less than a small value,
    then we consider them to be equal.
    """
    if abs(float2 - float1) < float_equality_tolerance:
        # these two float values are the "same"
        return True
    return False


class JsonExporter(object):
    def __init__(self, clip_start, clip_end, data_node_name=DATA_NODE_NAME):
        self.clip_start = clip_start
        self.clip_end = clip_end
        anim_data_manager = AnimDataManager(data_node_name, unscale_frame(clip_start), unscale_frame(clip_end))
        self.lights_data = anim_data_manager.get_lights_data()

    def get_backpack_lights_json(self):
        """
        Returns a list of json nodes with lights RGB and duration values
        ignores last frame
        """
        json_nodes = []
        frame_nums = self.lights_data.keys()
        frame_nums.sort()
        for idx in range(len(frame_nums) - 1):
            json_node = self.generate_backpack_json_node(frame_nums[idx], frame_nums[idx + 1])
            if json_node is not None:
                json_nodes.append(json_node)
        return json_nodes

    def generate_backpack_json_node(self, current_frame, next_frame):
        """
        Converts lights_data dictionary taken from anim_data_manager
        into a json node needed for export
        """
        duration = convert_time(next_frame, offset=current_frame)
        if duration < FLOAT_EQUALITY_TOLERANCE:
            return None
        frame_num_ms = convert_time(current_frame)

        json_node = copy.copy(BACKPACK_LIGHT_JSON_NODE)
        json_node["durationTime_ms"] = duration
        json_node["triggerTime_ms"] = frame_num_ms

        for side, rgb_values in self.lights_data[current_frame].iteritems():
            json_node[side.capitalize()] = rgb_values

        return json_node


def clamp_body_motion_keyframe(body_motion_keyframe, frame_num,
                               max_wheel_speed=MAX_WHEEL_SPEED_MMPS,
                               max_rotation_speed=MAX_BODY_ROTATION_SPEED_DEG_PER_SEC,
                               min_radius=MIN_RADIUS_MM, max_radius=MAX_RADIUS_MM):
    """
    Given a body motion keyframe, this function will clamp the
    movement and return a corresponding message if the movement
    exceeds the physical limitations of the robot.
    """
    if not "speed" in body_motion_keyframe:
        msg = "Can't clamp wheel values because speed is not specified in body_motion_keyframe %s"\
              %(body_motion_keyframe)
        add_json_node(node_name="Clamp wheel values",
                      fix_function="", status="error",
                      message=msg)
        return

    orig_speed = body_motion_keyframe["speed"]

    try:
        radius = float(body_motion_keyframe["radius_mm"])
    except (TypeError, ValueError):
        # this is a turn-in-place or straight movement
        movement_type = body_motion_keyframe["radius_mm"].lower().replace("_", " ")
    else:
        # this is an arc turn with a numeric radius
        movement_type = "turn (radius=%s)" % radius
        if body_motion_keyframe["radius_mm"] > max_radius:
            body_motion_keyframe["radius_mm"] = max_radius
        elif body_motion_keyframe["radius_mm"] < min_radius:
            body_motion_keyframe["radius_mm"] = min_radius

    if body_motion_keyframe["radius_mm"] == "TURN_IN_PLACE":
        if body_motion_keyframe["speed"] > max_rotation_speed:
            body_motion_keyframe["speed"] = max_rotation_speed
        elif body_motion_keyframe["speed"] < -max_rotation_speed:
            body_motion_keyframe["speed"] = -max_rotation_speed
        speed_units = "deg/sec"
    elif body_motion_keyframe["speed"] > max_wheel_speed:
        body_motion_keyframe["speed"] = max_wheel_speed
        speed_units = "mm/sec"
    elif body_motion_keyframe["speed"] < -max_wheel_speed:
        body_motion_keyframe["speed"] = -max_wheel_speed
        speed_units = "mm/sec"

    if body_motion_keyframe["speed"] != orig_speed:
        # The movement was clamped, so return a message to indicate that
        msg = "The %s movement at frame %s has been clamped from %s to %s %s"
        msg = msg % (movement_type, frame_num, orig_speed, body_motion_keyframe["speed"], speed_units)
        add_json_node(node_name="Clamp wheel values",
                      fix_function="", status="pass",
                      message=msg)
        return msg


def get_movement_json(clip_start, clip_end, dataNodeName):
    json_arr = []
    anim_data_manager = AnimDataManager(dataNodeName, unscale_frame(clip_start), unscale_frame(clip_end))
    move_data_combined = anim_data_manager.get_move_data()

    # TODO: error message if all are not keyed (?)
    if len(move_data_combined) == 0:
        return None

    # Loop through all keyframes
    trigger_times = []
    keyframe_count = len(move_data_combined)
    body_msgs = []
    for idx in range(keyframe_count):
        curr, msg = set_move_data_for_frame(move_data_combined, idx, clip_start, trigger_times)
        if msg:
            body_msgs.append(msg)

        if curr:
            json_arr.append(curr)
    add_json_node(node_name="Body animation",
                  fix_function="", status="warning",
                  message=body_msgs)
    return json_arr


def set_move_data_for_frame(move_data_combined, idx, clip_start, trigger_times):
    this_frame = move_data_combined[idx]

    try:
        next_frame = move_data_combined[idx+1]
    except IndexError:
        msg  = "keyframe %s - end frame, so all movement has been " % idx
        msg += "processed up until that time (frame = %s)" % unscale_frame(this_frame["Time"])
        return (None, msg)

    fwd_delta = next_frame["Forward"] - this_frame["Forward"]
    turn_delta = next_frame["Turn"] - this_frame["Turn"]
    triggerTime_ms = convert_time(this_frame["Time"])
    durationTime_ms = convert_time(next_frame["Time"], offset=this_frame["Time"])
    time_in_seconds = durationTime_ms / 1000.0

    if triggerTime_ms in trigger_times:
        return (None, "Multiple movement keyframes at time %s (only using first one)" % triggerTime_ms)
    else:
        trigger_times.append(triggerTime_ms)

    curr = { "triggerTime_ms" : triggerTime_ms,
             "durationTime_ms" : durationTime_ms,
             "Name" : "BodyMotionKeyFrame" }

    if next_frame["Reset"] == True:
        # Just an empty reset frame.
        msg = ("keyframe %s - empty reset (frame = %s)" % ((idx+1), unscale_frame(next_frame["Time"])))
        return (None, msg)

    if fwd_delta != 0 and next_frame["Radius"] == 0 and turn_delta == 0:
        curr["radius_mm"] = "STRAIGHT"
        curr["speed"] = get_straight_movement_speed(fwd_delta, time_in_seconds)

    elif fwd_delta == 0 and next_frame["Radius"] == 0 and turn_delta != 0:
        curr["radius_mm"] = "TURN_IN_PLACE"
        # whereas in maya the turn values are in degrees. The one robot Mooly
        # tested on turned about 360 degrees in 1.25 seconds
        # but in theory the max is 8 radians per second
        rot_degrees_wanted = turn_delta
        curr["speed"] = int(round(rot_degrees_wanted / time_in_seconds))

    elif fwd_delta == 0 and next_frame["Radius"] != 0 and turn_delta != 0:
        # Radius and turn are non-zero and forward is 0, so it's an ARC
        curr["radius_mm"] = int(round(next_frame["Radius"]))
        rot_radians = math.radians(turn_delta)
        arc_length = curr["radius_mm"] * rot_radians
        curr["speed"] = int(round(arc_length / time_in_seconds))

    elif fwd_delta == 0 and turn_delta == 0:
        msg  = "keyframe %s - there is no body movement starting at " % idx
        msg += "time %s for %s ms " % (triggerTime_ms, durationTime_ms)
        msg += "(from frame %s to %s)" % (unscale_frame(this_frame["Time"]), unscale_frame(next_frame["Time"]))
        return (None, msg)

    else:
        msg  = "keyframe %s - undefined movement with " % idx
        msg += "[fwd_delta = %s], " % fwd_delta
        msg += "[turn_delta = %s] and " % turn_delta
        msg += "[next frame radius = %s] " % next_frame["Radius"]
        msg += "(starting at frame = %s)" % unscale_frame(this_frame["Time"])
        # In all the other body movement cases messages can get added after all frames are analyzed.
        # Here are not returning a message, so want to add it before raing an error
        add_json_node(node_name="Body animation",
                        fix_function="", status="error",
                        message=msg)
        raise ValueError(msg)

    msg = clamp_body_motion_keyframe(curr, unscale_frame(clip_start + next_frame["Time"]))
    if not exporter_config.get_clamp_body_motion():
        # Only display the clamping messages for body motion keyframes for newer Maya files
        # since the scale/proportions were off before the work for COZMO-1582
        msg = None

    return (curr, msg)


def load_audio_to_globals():
    global g_AudioEventNamesSorted
    global g_AudioIDs
    global g_allAudioActionIds

    g_AudioEventNamesSorted, g_AudioIDs, groupedAudioNames = loadAudioAttrsFromPy()

    allAudioStates, audioStateIds, subAudioStateIds = \
        loadAudioAttrsFromPy(audioTypes=AUDIO_STATE_TYPES, audioGroups=[], recursive=True)

    allAudioSwitches, audioSwitchIds, subAudioSwitchIds = \
        loadAudioAttrsFromPy(audioTypes=AUDIO_SWITCH_TYPES, audioGroups=[], recursive=True)

    allAudioParameters, audioParameterIds, groupedParameterNames = \
        loadAudioAttrsFromPy(audioTypes=AUDIO_PARAMETER_TYPES)

    g_allAudioActionIds[PARAMETERS_ATTR] = {PARAMETER_ID_ATTR:audioParameterIds, CURVE_ATTR:CURVE_TYPES}
    g_allAudioActionIds[SWITCHES_ATTR] = {SWITCH_GROUP_ID_ATTR:audioSwitchIds,STATE_ID_ATTR:subAudioSwitchIds}
    g_allAudioActionIds[STATES_ATTR] = {STATE_GROUP_ID_ATTR:audioStateIds, STATE_ID_ATTR:subAudioStateIds}


def _get_audio_event_id_from_name(audio_string_name, error_msgs,
                                  default_audio_event=DEFAULT_AUDIO_EVENT):
    try:
        audio_event_id = int(g_AudioIDs[audio_string_name])
    except KeyError:
        error_msg = "Unknown audio event '%s'" % audio_string_name
        try:
            audio_event_id = int(g_AudioIDs[default_audio_event])
        except KeyError:
            error_msg += " (so any keyframes for that will be lost)"
            error_msgs.append(error_msg)
            audio_event_id = None
        else:
            audio_string_name = default_audio_event
            error_msg += " (so that was replaced with '%s')" % default_audio_event
            error_msgs.append(error_msg)
    return (audio_event_id, audio_string_name)


def _val_in_range(val, min, max):
    if (val >= min and val <= max) or is_equal(val, min) or is_equal(val, max):
        return True
    return False


def group_audio_by_frame_num(groupedAudioKeyframes):
    all_frames = []
    actions_by_frame = {}
    for action, keyframes in groupedAudioKeyframes.iteritems():
        for attr, values in keyframes.iteritems():
            if values[1]:
                all_frames.extend(values[1])
    all_frames = list(set(all_frames))
    for frame in all_frames:
        actions_by_frame[frame] = {}
        for action, keyframes in groupedAudioKeyframes.iteritems():
            actions_by_frame[frame][action] = {}
            for attr, values in keyframes.iteritems():
                if values[1] and frame in values[1]:
                    frame_idx = values[1].index(frame)
                    actions_by_frame[frame][action][attr] = values[0][frame_idx]
    return actions_by_frame


def get_audio_json(grouped_audio_keyframes, clip_name, clip_start, clip_end,
                   audio_event_enum_attr=AUDIO_ENUM_ATTR, trigger_time_attr=TRIGGER_TIME_ATTR,
                   prob_attr=PROB_ATTR, volume_attr=VOLUME_ATTR, attrs_with_variants_names=None,
                   variant_suffix_start=2):
    audio_keyframes_by_frame = group_audio_by_frame_num(grouped_audio_keyframes)

    clip_start = unscale_frame(clip_start)
    clip_end = unscale_frame(clip_end)

    json_arr = []
    error_msgs = []
    audio_event_times = []

    if cmds.attributeQuery(audio_event_enum_attr, node=AUDIO_NODE_NAME, exists=True):
        event_enum_str = cmds.attributeQuery(audio_event_enum_attr, node=AUDIO_NODE_NAME, listEnum=True)
        if event_enum_str:
            enum_list = event_enum_str[0].split(':')

    param_frame_num = 0
    looping_event_tracker = []
    for frame, grouped_actions in audio_keyframes_by_frame.iteritems():
        if clip_start <= frame <= clip_end:
            # no default audio json, because some actions might not be a part of the json audio node
            if EVENT_GROUPS_ATTR in grouped_actions.keys() and grouped_actions[EVENT_GROUPS_ATTR] != {}:
                audio_json = getDefaultAudioJson()
            else:
                audio_json = copy.deepcopy(DEFAULT_EMPTY_AUDIO_JSON)
            trigger_time = convert_time(scale_frame(frame, clip_start))
            audio_json[trigger_time_attr] = trigger_time
            for action, action_values in grouped_actions.iteritems():
                if action_values != {}:
                    if action == EVENT_GROUPS_ATTR:
                        audio_keyframes = grouped_audio_keyframes[action]
                        if not event_enum_str:
                            error_msg = "eventGroups need to have event_enum_str"
                            error_msgs.append(error_msg)
                            return (json_arr, error_msgs)

                        event_enum_idxs = get_audio_variant_attr_values(action_values, audio_event_enum_attr)
                        probability_values = get_audio_variant_attr_values(action_values, prob_attr)
                        volume_values = get_audio_variant_attr_values(action_values, volume_attr)

                        # get value attrs, so that can use them in get_audio_event_json (accepts attr names for )
                        for i, event_enum_idx in enumerate(event_enum_idxs):
                            # to protect from legacy animations, which may have only one volume per multiple events
                            if len(volume_values) > 1:
                                volume_value = volume_values[i]
                            elif len(volume_values) == 1:
                                volume_value = volume_values[0]
                            else:
                                # TODO: make this part of pre-export check
                                # Most likely occures when there is a keyframe on event name but not on the volume attr
                                volume_value = DEFAULT_VOLUME

                            if len(probability_values) > 1:
                                probability_value = probability_values[i]
                            elif len(probability_values) == 1:
                                probability_value = probability_values[0]
                            else:
                                # TODO: make this part of pre-export check
                                # Most likely occures when there is a keyframe on event name but not on the probability attr
                                probability_value = DEFAULT_PROBABILITY

                            audio_enum_value = int(event_enum_idx)
                            audio_keyframes = grouped_audio_keyframes[action]
                            audio_event_id = _append_event_data(audio_json, error_msgs, action,
                                                                enum_list, audio_enum_value,
                                                                probability_value, volume_value,
                                                                looping_event_tracker)
                    else:
                        get_non_event_actions_json(audio_json, action, action_values,
                                                   param_frame_num, error_msgs)
            json_arr.append(audio_json)
            if PARAMETERS_ATTR in audio_json.keys():
                param_frame_num += 1

    if looping_event_tracker:
        error_msg = os.linesep
        error_msg += "%s: these looping audio events are not stopped: " % clip_name
        error_msg += ', '.join(looping_event_tracker)
        error_msgs.append(error_msg)
    if error_msgs:
        add_json_node(export_type="On Export", group_name="Audio",
                      node_name="Audio export",
                      fix_function="", status="warning",
                      message=error_msgs)

    return (json_arr, error_msgs)


def _get_converted_value(value, conversion_attr=None):
    if value is None:
        return None
    if conversion_attr:
        try:
            conversion = AUDIO_ATTR_CONVERSION[conversion_attr]
        except KeyError:
            return value
        else:
            return conversion(value)
    else:
        return value


def get_non_event_actions_json(audio_json, action, action_values, param_frame_num, error_msgs):
    audio_json[action] = []
    all_sorted_values = {}
    action_node_num = 0

    # find original attributes (that don't have numbers at the end of the name)
    # the variants are added to their lists
    for attr, value in action_values.iteritems():
        if re.search(r'\d+$', attr) is None:
            sorted_values = get_audio_variant_attr_values(action_values, attr)
            all_sorted_values[attr] = sorted_values
            action_node_num = len(sorted_values)

    for i in range(action_node_num):
        audio_json[action].append(copy.deepcopy(AUDIO_ACTION_DEFAULT_DICT[action]))

    for attr, values in all_sorted_values.iteritems():
        for i in range(len(values)):
            json_attr = AUDIO_ATTR_TO_JSON_ATTR[attr]
            if attr in TOP_LEVEL_ENUM_ATTRS:
                if attr in g_allAudioActionIds[action][json_attr].keys():
                    error_msg = "%s is not in the list of ids" % (attr)
                    error_msgs.append(error_msg)
                else:
                    id = g_allAudioActionIds[action][json_attr][values[i]]
                    audio_json[action][i][json_attr] = id
            elif attr in SUB_LEVEL_ENUM_ATTRS:
                group_name = all_sorted_values[AUDIO_ACTION_TO_GROUP_DICT[action]][i]
                if AUDIO_ACTION_TO_GROUP_DICT[action] not in g_allAudioActionIds[action].keys():
                    error_msg = "%s needs to have %s" % (action, AUDIO_ACTION_TO_GROUP_DICT[action])
                    error_msgs.append(error_msg)
                else:
                    sub_enums = g_allAudioActionIds[action][json_attr][group_name]
                    audio_json[action][i][json_attr] = sub_enums[values[i]]
            elif attr in INT_ATTRS:
                audio_json[action][i][json_attr] = int(round(values[i]))
            else:
                audio_json[action][i][json_attr] = values[i]

    if error_msgs:
        add_json_node(node_name="Non event actions",
                      fix_function="", status="warning",
                      message=error_msg)


def get_audio_variant_attr_values(values, original_attr):
    attr_values = []
    variant_attrs = []
    for attr, value in values.iteritems():
        if (attr[:len(original_attr)] == original_attr):
            variant_attrs.append(attr)
    variant_attrs.sort()

    for variant_attr in variant_attrs:
        attr_values.append(values[variant_attr])

    return attr_values


def _append_event_data(audio_json, error_msgs, group_name, enum_list, audio_enum_value,
                       probability_value, volume_value, looping_event_tracker):
    audio_string_name = enum_list[audio_enum_value]
    audio_event_id, audio_string_name = _get_audio_event_id_from_name(audio_string_name, error_msgs)
    audio_json[group_name][0][EVENT_IDS_ATTR].append(audio_event_id)
    audio_json[group_name][0][EVENT_NAME_ATTR].append(audio_string_name)

    # dividing by 100 to convert to an exporter value
    audio_json[group_name][0][PROBABILITIES_ATTR].append(_get_converted_value(probability_value, PROB_ATTR))
    audio_json[group_name][0][VOLUMES_ATTR].append(_get_converted_value(volume_value, VOLUME_ATTR))

    balanceLoopingEvents(audio_string_name, looping_event_tracker)

    return audio_event_id


def get_event_json(eventKeyframes, clip_start, clip_end, problem_list):

    # The 'event_trigger' enum attribute on the 'x:event_ctrl' node is populated
    # in the Cozmo rig for Maya (in assets/rigs/Cozmo_midRes_rig.ma in the
    # cozmo-animation SVN repo). To be safe, make sure that nothing is deleted
    # from that enum list and that its order does not change or else we could
    # have problems in existing Maya scenes that use that rig and have event
    # trigger keyframes. The events in that enum list are mapped to clad events
    # in the game, which can be found in the 'AnimEvent' enum in
    # robot/clad/src/clad/types/animationEvents.clad in the products-cozmo Git repo.

    clip_start = unscale_frame(clip_start)
    clip_end = unscale_frame(clip_end)

    json_arr = []
    Event_Vs, Event_Ts = eventKeyframes[EVENT_ENUM_ATTR]
    if not cmds.objExists(EVENT_CTRL) or Event_Vs is None or Event_Ts is None \
            or ctrs_manager.is_ctr_muted(EVENT_CTRL):
        return json_arr
    enum_str = cmds.attributeQuery(EVENT_ENUM_ATTR, node=EVENT_CTRL, listEnum=True)
    if not enum_str or not enum_str[0]:
        return json_arr
    enum_list = enum_str[0].split(':')
    for idx in range(len(Event_Ts)):
        if Event_Ts[idx] < clip_start or Event_Ts[idx] > clip_end:
            continue
        value = int(Event_Vs[idx])
        time = convert_time(scale_frame(Event_Ts[idx], clip_start))
        try:
            value = enum_list[value].upper()
        except IndexError:
            msg  = "Found event trigger at time %s for event %s " % (time, value)
            msg += "but that event was not found in the enum list. "
            msg += EVENT_ENUM_PROB_MSG
            problem_list.append(msg)
            continue
        if value and value != "NONE":
            print("event at offset time %s = %s" % (time, value))
        if value and value.lower() == FACIAL_ANIMATION_EVENT:
            # "facial_animation" events are special and used differently from other events.
            facial_anim_name = cmds.getAttr("%s.%s" % (EVENT_CTRL, FACIAL_ANIMATION_ATTR))
            if not facial_anim_name:
                msg = "Found facial animation event trigger at time %s " % time
                msg += "but the facial animation to use was not specified"
                problem_list.append(msg)
                continue
            event_json = { "triggerTime_ms" : time,
                           "animName" : facial_anim_name,
                           "Name" : "FaceAnimationKeyFrame" }
            json_arr.append(event_json)
        elif value and value != "NONE":
            # Standard events
            event_json = { "triggerTime_ms" : time,
                           "event_id" : value,
                           "Name" : "EventKeyFrame" }
            json_arr.append(event_json)
    return json_arr


