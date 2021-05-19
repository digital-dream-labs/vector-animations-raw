# This module was written to support animators ability to set wheel rotation
# using two wheel ctrs on the robot.

# We convert those rotation values into wheel speeds based on the frames that
# the wheel ctrs were keyed at. We assume that animators key the wheels based
# on the speed the robot needs to reach within a time period between two
# frames, and we take the rotation value from the second of those frames
# (same as with the regular body movement)

# We then convert that wheel speed to attributes for BodyMotionKeyFrame using
# the differential drive equation.

# daria@anki.com

# Apr 10, 2017 - initial build
# May 15, 2017 - added support for new wheel system and exception for 0ed wheel
#                ctrs
# May 26, 2017 - changed the new wheel system to use non-accumulative ratio
#                change
# July 5, 2017 - added a fix for oposite wheel rotation during a point turn
#                (COZMO-12816)
# July 6, 2017 - added a fix for radius between -0.5 and 0.5 (COZMO-12880)
#                rounding up radius, speed and time
# Sep 19, 2017 - do not round up turns between 0 and 0.5 to point turns,
#                instead to arc turns


import math
import maya.cmds as mc
from ankimaya.constants import ANIM_FPS, HACK_TIMELINE_SCALE, DATA_NODE_NAME
from json_exporter import convert_time, get_movement_json
from ankimaya import exporter_config
from ankimaya import ctrs_manager
from interpolation_manager import find_value_for_frame
from robot_config import MAX_WHEEL_SPEED_MMPS, MAX_BODY_ROTATION_SPEED_DEG_PER_SEC
from robot_config import MIN_RADIUS_MM, MAX_RADIUS_MM, WHEEL_DIAMETER_MM, WHEEL_DIST_MM

from ankimaya.export_error_check.error_checker_utils import add_json_node

SCALED_FPS = 33.0

DEFAULT_WHEEL_VALUE = 360.0
DEFAULT_WHEEL_ADD_VALUE = 5.0
DEFAULT_WHEEL_MINUS_VALUE = -DEFAULT_WHEEL_ADD_VALUE
DEFAULT_WHEEL_MULTIPLY_VALUE = 1.1
DEFAULT_WHEEL_DIVIDE_VALUE = 1 / DEFAULT_WHEEL_MULTIPLY_VALUE

DEFAULT_PLUS_STR = "default_plus"
DEFAULT_MINUS_STR = "default_minus"

EQUALITY_THRESHHOLD = 0.000001

DEFAULT_WHEEL_STR_VALUE = {DEFAULT_PLUS_STR: [DEFAULT_WHEEL_ADD_VALUE,
                                              DEFAULT_WHEEL_MULTIPLY_VALUE,
                                              DEFAULT_WHEEL_VALUE],
                           DEFAULT_MINUS_STR: [DEFAULT_WHEEL_MINUS_VALUE,
                                               DEFAULT_WHEEL_DIVIDE_VALUE,
                                               -DEFAULT_WHEEL_VALUE]}

SEPARATE_WHEEL_NODE_NAME = "Separate wheels"

CLAMP_WHEEL_VAL_UNDO_NAME = "clamp_wheel_values"
PLACE_MISSING_FRMS_UNDO_NAME = "place missing frames"
CHUNK_UNDO_NAME = "chunk undo"
ROT_WHEEL_UNDO_NAME = "rotate_wheels_by"
MOAC_UNDO_NAME = "moac"

L_WHEEL_CTR = "x:wheel_L_ctrl"
R_WHEEL_CTR = "x:wheel_R_ctrl"
MECH_ALL_CTR = "x:mech_all_ctrl"
MOAC_CTR = "x:moac_ctrl"
WHEEL_ROT_ATTR = "rotateX"
L_WHEEL_ROT_ATTR = L_WHEEL_CTR + "." + WHEEL_ROT_ATTR
R_WHEEL_ROT_ATTR = R_WHEEL_CTR + "." + WHEEL_ROT_ATTR

L_WHEEL_GRP = "x:wheel_L_grp"
R_WHEEL_GRP = "x:wheel_R_grp"
WHEELS_CTR = "x:wheels_ctrl"
BOTH_WHEEL_ROT_ATTR = "wheel_rotation"
BOTH_WHEEL_RATIO_ATTR = "wheel_ratio"

STRAIGHT_RADIUS = "STRAIGHT"
TURN_IN_PLACE_RADIUS = "TURN_IN_PLACE"

HALF_ROT_DEG = math.degrees(math.pi)
FULL_ROT_DEG = 2 * HALF_ROT_DEG
FULL_ROT_RAD = 2 * math.pi

MIN_RADIUS_THRESHOLD = 0.1 # if radius is less than that count movement as
                           # turn in place
SPEED_MSG_THRESHOLD = 0.1  # min difference between clamped and non-clamped
                           # speed for clamping msg

ROUND_WHEEL_VALUE = 3
ROUND_SPEED_VALUE = 5

MOVEMENT_BUTTON_BORDER_COLOR_HI = "rgb(206, 206, 206)"

MODIFY_KEYS_WARNING = "Cannot modify keys following the current one becuase the wheels are not in sync"

# if the ratio between wheels is between these values it will export as turn
# and the values of both wheels will be averaged
MIN_WHEEL_RATIO = -1.0444444444444445  # ratio between left & right speeds in
                                       # case of a radius of 0.5
MAX_WHEEL_RATIO = -0.9574468085106383  # ratio between left & right speeds in
                                       # case of a radius of -0.5


# The way ratio values were found:
#
# original formula:
# 1) radius = WHEEL_DIST_MM / 2.0 * ((l_wheel_speed + r_wheel_speed) /
#             (r_wheel_speed - l_wheel_speed))
# finding l_wheel_speed/r_wheel_speed from that
# 2) radius*(r_wheel_speed - l_wheel_speed) = WHEEL_DIST_MM / 2.0 *
#                                             (l_wheel_speed + r_wheel_speed)
# 3) (radius - WHEEL_DIST_MM / 2.0) * r_wheel_speed =
#    (radius + WHEEL_DIST_MM / 2.0) * l_wheel_speed
# 4) l_wheel_speed/r_wheel_speed =
#.   (radius + WHEEL_DIST_MM / 2.0) / (radius - WHEEL_DIST_MM / 2.0)

# Testing ratio values:
#
# WHEEL_DIST_MM / 2.0 * ((1 + (-0.9574468085106383)) / ((-0.9574468085106383) - 1)) = -0.5
# WHEEL_DIST_MM / 2.0 * ((1 + (-1.0444444444444445)) / ((-1.0444444444444445) - 1)) = 0.5


class WheelMovement(object):
    def __init__(self):
        self.clip_end = 0
        self.clip_start = 0
        self.problem_list = []
        self.is_radians = check_rad_or_deg_in_prefs()
        self.max_wheel_speed_mmps = MAX_WHEEL_SPEED_MMPS
        self.max_rotation_speed = MAX_BODY_ROTATION_SPEED_DEG_PER_SEC

        if ctrs_manager.is_ctr_muted(L_WHEEL_CTR) and ctrs_manager.is_ctr_muted(R_WHEEL_CTR):
            # Return true when no rig in the scene, so no warning
            return
        elif ctrs_manager.is_ctr_muted(L_WHEEL_CTR) or ctrs_manager.is_ctr_muted(R_WHEEL_CTR):
            mc.warning(
                "Only one wheel ctr is muted. You might achieve unexpected result during export.")

    def get_wheel_ctr_speeds(self, all_frames=False, ignore_mech_all=False):
        """
        Get wheels rotation values from ctrs and convert them to wheel speed
        At this point reads wheel values from the wheel ctrs themselves.
        Maybe todo: change to analyzing the data node to be more consistent
        with everything else.
        """
        all_wheel_speeds = []

        if not do_wheels_exist():
            return [], []

        if all_frames:
            l_wheel_times = mc.keyframe(L_WHEEL_ROT_ATTR, query=True, timeChange=True)
            r_wheel_times = mc.keyframe(R_WHEEL_ROT_ATTR, query=True, timeChange=True)
        else:
            l_wheel_times = mc.keyframe(L_WHEEL_ROT_ATTR, query=True, timeChange=True,
                                        time=(self.clip_start, self.clip_end))
            r_wheel_times = mc.keyframe(R_WHEEL_ROT_ATTR, query=True, timeChange=True,
                                        time=(self.clip_start, self.clip_end))

        l_wheel_values = []
        r_wheel_values = []

        if l_wheel_times is None and r_wheel_times is None:
            return [], []

        wheel_times_fr = []
        if l_wheel_times:
            wheel_times_fr += l_wheel_times
        if r_wheel_times:
            wheel_times_fr += r_wheel_times

        if wheel_times_fr:
            wheel_times_fr = list(set(wheel_times_fr))
            wheel_times_fr.sort()

        for frame_num in wheel_times_fr:
            # In case there is no frame set on a wheel find what the value
            # should be based on linear interpolation (for right & left wheel)
            l_wheel_value = 0
            r_wheel_value = 0
            if not (l_wheel_times is None or r_wheel_times is None):
                if l_wheel_times is None or frame_num not in l_wheel_times:
                    r_wheel_value = mc.getAttr(R_WHEEL_ROT_ATTR, time=frame_num)
                    l_wheel_value = find_value_for_frame(frame_num, l_wheel_times,
                                                         L_WHEEL_ROT_ATTR)
                elif r_wheel_times is None or frame_num not in r_wheel_times:
                    l_wheel_value = mc.getAttr(L_WHEEL_ROT_ATTR, time=frame_num)
                    r_wheel_value = find_value_for_frame(frame_num, r_wheel_times,
                                                         R_WHEEL_ROT_ATTR)
                # In case there are keyframes on both wheels, get values for both of them
                else:
                    l_wheel_value = mc.getAttr(L_WHEEL_ROT_ATTR, time=frame_num)
                    r_wheel_value = mc.getAttr(R_WHEEL_ROT_ATTR, time=frame_num)


            rounded_l_wheel_value = round(l_wheel_value, ROUND_WHEEL_VALUE)

            rounded_r_wheel_value = round(r_wheel_value, ROUND_WHEEL_VALUE)
            l_wheel_values.append(rounded_l_wheel_value)
            r_wheel_values.append(rounded_r_wheel_value)

        if all(i == 0 for i in r_wheel_values) and all(i == 0 for i in l_wheel_values):
            add_json_node(node_name=SEPARATE_WHEEL_NODE_NAME, tool_tip="Are wheels keyed",
                          fix_function="", status="warning",
                          message="%s and %s are keyed but have a constant value of 0"
                                  ", so they will be ignored"
                                  % (L_WHEEL_CTR, R_WHEEL_CTR))
            return [], []

        self.check_key_placement(l_wheel_times, r_wheel_times)

        all_wheel_speeds = self.get_speeds_from_values(l_wheel_values, r_wheel_values,
                                                       wheel_times_fr, all_frames, ignore_mech_all)

        return (all_wheel_speeds, wheel_times_fr)

    def get_speeds_from_values(self, l_wheel_values, r_wheel_values, wheel_times_fr, all_frames,
                               ignore_mech_all=False):
        all_wheel_speeds = []
        if all_frames:
            mech_all_times = mc.keyframe(MECH_ALL_CTR, query=True, timeChange=True)
            mech_all_values = mc.keyframe(MECH_ALL_CTR, query=True, valueChange=True)
        else:
            mech_all_times = mc.keyframe(MECH_ALL_CTR, query=True, timeChange=True,
                                         time=(self.clip_start, self.clip_end))
            mech_all_values = mc.keyframe(MECH_ALL_CTR, query=True, valueChange=True,
                                          time=(self.clip_start, self.clip_end))

        for i in range(len(wheel_times_fr) - 1):
            # todo: this can maybe be done cleaner without checking every wheel frame
            if (not ignore_mech_all) and mech_all_times and mech_all_values:
                if not all(i == 0 for i in mech_all_values):
                    if are_mech_keys_between_wheel_keys(wheel_times_fr[i], wheel_times_fr[i + 1]):
                        msg = "Wheels need to be keyed before or after any other body movement"
                        add_json_node(node_name="Separate wheels and body animation",
                                      fix_function="", status="error",
                                      message=msg)
                        raise ValueError(msg)
                        return [], []

            time_sec = (wheel_times_fr[i + 1] - wheel_times_fr[i]) / ANIM_FPS
            time_sec *= HACK_TIMELINE_SCALE

            if self.is_radians:
                l_rot_num = (l_wheel_values[i + 1] - l_wheel_values[i]) / FULL_ROT_RAD
                r_rot_num = (r_wheel_values[i + 1] - r_wheel_values[i]) / FULL_ROT_RAD
            else:
                l_rot_num = (l_wheel_values[i + 1] - l_wheel_values[i]) / FULL_ROT_DEG
                r_rot_num = (r_wheel_values[i + 1] - r_wheel_values[i]) / FULL_ROT_DEG
            l_wheel_speed = self.get_single_wheel_speed(time_sec, l_rot_num)
            r_wheel_speed = self.get_single_wheel_speed(time_sec, r_rot_num)
            if exporter_config.get_round_turn_under_point_five():
                # rounding values because otherwise radius math gets off sometimes
                l_wheel_speed, r_wheel_speed = self.average_small_speeds(
                    round(l_wheel_speed, ROUND_SPEED_VALUE),
                    round(r_wheel_speed, ROUND_SPEED_VALUE))
            else:
                l_wheel_speed = round(l_wheel_speed, ROUND_SPEED_VALUE)
                r_wheel_speed = round(r_wheel_speed, ROUND_SPEED_VALUE)
            all_wheel_speeds.append([l_wheel_speed, r_wheel_speed])

        return all_wheel_speeds

    def get_speeds_from_values_and_ratio(self, l_wheel_values, ratios, wheel_times_fr):
        all_wheel_speeds = []
        if len(l_wheel_values) != len(ratios):
            print("Inconsistency between wheel values (%s values) and ratios (%s rations)"
                  % (len(l_wheel_values), len(ratios)))
            return []
        for i in range(len(wheel_times_fr) - 1):
            time_sec = (
                       (wheel_times_fr[i + 1] - wheel_times_fr[i]) / ANIM_FPS) * HACK_TIMELINE_SCALE
            if self.is_radians:
                l_rot_num = (l_wheel_values[i + 1] - l_wheel_values[i]) / FULL_ROT_RAD
            else:
                l_rot_num = (l_wheel_values[i + 1] - l_wheel_values[i]) / FULL_ROT_DEG
            l_wheel_speed = self.get_single_wheel_speed(time_sec, l_rot_num)
            r_wheel_speed = l_wheel_speed * ratios[i]
            # not averaging small speeds in v3 (want turn in place to be more
            # similar to arc turns)
            if exporter_config.get_round_turn_under_point_five():
                l_wheel_speed, r_wheel_speed = self.average_small_speeds(l_wheel_speed,
                                                                         r_wheel_speed)
            all_wheel_speeds.append((l_wheel_speed, r_wheel_speed))
        return all_wheel_speeds

    def average_small_speeds(self, l_wheel_speed, r_wheel_speed):
        if r_wheel_speed != 0 and \
                (MIN_WHEEL_RATIO < (l_wheel_speed / r_wheel_speed) < MAX_WHEEL_RATIO):
            average_value = \
                (l_wheel_speed - r_wheel_speed) / 2.0  # - instead of + because
                                                       # values are opposite
            l_wheel_speed = average_value
            r_wheel_speed = -average_value
        return l_wheel_speed, r_wheel_speed

    def get_wheel_speed(self, all_frames=False, ignore_mech_all=False):
        wheel_ctr_speeds, wheel_ctr_times_fr = self.get_wheel_ctr_speeds(all_frames=all_frames,
                                                                         ignore_mech_all=ignore_mech_all)
        if wheel_ctr_speeds != []:
            return wheel_ctr_speeds, wheel_ctr_times_fr
        else:
            return [], []

    def get_single_wheel_speed(self, time_sec, rot_num):
        wheel_speed = rot_num * WHEEL_DIAMETER_MM * math.pi / time_sec
        return wheel_speed

    def set_move_data_for_frame(self, l_wheel_speed, r_wheel_speed, frame_num, next_frame,
                                clip_start, trigger_times):
        """
        Sets movement data using the same structure as the usual wheel movement
        """
        trigger_time_ms = convert_time(frame_num,
                                       offset=clip_start / HACK_TIMELINE_SCALE) * HACK_TIMELINE_SCALE
        trigger_time_ms = int(round(trigger_time_ms))
        duration_time_ms = convert_time(next_frame, offset=frame_num) * HACK_TIMELINE_SCALE
        duration_time_ms = int(round(duration_time_ms))

        if trigger_time_ms in trigger_times:
            print("Multiple movement keyframes at time %s (only using first one)" % trigger_time_ms)
            return None
        else:
            trigger_times.append(trigger_time_ms)

        unrounded_radius, rounded_radius = find_radius(l_wheel_speed, r_wheel_speed)
        rounded_radius = check_radius(rounded_radius, frame_num, problem_list=self.problem_list)
        if unrounded_radius:
            unrounded_radius = check_radius(unrounded_radius, frame_num,
                                            problem_list=self.problem_list)

        speed = find_speed(l_wheel_speed, r_wheel_speed, rounded_radius, unrounded_radius)
        speed = check_speed(rounded_radius, speed, frame_num, problem_list=self.problem_list)
        if -EQUALITY_THRESHHOLD < speed < EQUALITY_THRESHHOLD:
            # if the speed is zero, then don't bother returning a keyframe
            return None

        curr = {"triggerTime_ms": trigger_time_ms,
                "durationTime_ms": duration_time_ms,
                "Name": "BodyMotionKeyFrame",
                "radius_mm": rounded_radius,
                "speed": int(round(speed))}
        return curr

    def get_json(self, clip_start, clip_end):
        """
        Similar to the usual robot movement
        """
        self.clip_end = clip_end / HACK_TIMELINE_SCALE
        self.clip_start = clip_start / HACK_TIMELINE_SCALE
        all_wheel_speeds, wheel_times_fr = self.get_wheel_speed()
        if not all_wheel_speeds or all_wheel_speeds == ([], []):
            return []
        json_arr = []
        trigger_times = []
        for idx in range(1, len(wheel_times_fr)):
            l_wheel_speed = all_wheel_speeds[idx - 1][0]
            r_wheel_speed = all_wheel_speeds[idx - 1][1]
            if l_wheel_speed == 0 and r_wheel_speed == 0:
                continue
            curr = self.set_move_data_for_frame(l_wheel_speed, r_wheel_speed,
                                                wheel_times_fr[idx - 1], wheel_times_fr[idx],
                                                clip_start, trigger_times)
            if curr:
                json_arr.append(curr)
        return json_arr

    def check_key_placement(self, l_wheel_times, r_wheel_times):
        """
        Error checks.
        Currently can only place wheel keys before or after mech ctr.
        If animators need to use those ctrs differently, then they can change
        the last check.
        """
        msg = None
        msg_suffix = " Exporter will set missing wheel keys based on the linear interpolation."
        no_keys_msg = "There are no keys set on %s. "
        no_keys_msg += msg_suffix
        time_mismatch_msg = "Left and right wheels are not currently keyed at the same frames."
        time_mismatch_msg += msg_suffix

        if l_wheel_times is None:
            msg = no_keys_msg % L_WHEEL_CTR
            return False
        if r_wheel_times is None:
            msg = no_keys_msg % R_WHEEL_CTR
            return False
        if l_wheel_times != r_wheel_times:
            msg = time_mismatch_msg
        if msg:
            add_json_node(node_name=SEPARATE_WHEEL_NODE_NAME,
                          fix_function="", status="warning",
                          message=msg)

        return True

    def clamp_wheel_values(self):
        """
        Find any frames where speeds exceed 220 mm/s for straight or arc
        movement or 300 deg/s for turn-in-place
        """
        frame_nums = []
        new_wheel_values = []
        all_wheel_speeds, wheel_times_fr = self.get_wheel_speed(True, True)
        if not all_wheel_speeds:
            return []
        if all_wheel_speeds == []:
            return []
        mc.undoInfo(openChunk=True, undoName=CLAMP_WHEEL_VAL_UNDO_NAME)
        for i in range(1, len(wheel_times_fr)):
            unrounded_radius, rounded_radius = find_radius(all_wheel_speeds[i - 1][0],
                                                           all_wheel_speeds[i - 1][1])
            rounded_radius = check_radius(rounded_radius, wheel_times_fr[i],
                                          problem_list=self.problem_list)
            if unrounded_radius:
                unrounded_radius = check_radius(unrounded_radius, wheel_times_fr[i],
                                                problem_list=self.problem_list)
            speed = find_speed(all_wheel_speeds[i - 1][0], all_wheel_speeds[i - 1][1],
                               rounded_radius, unrounded_radius)
            new_speed = check_speed(rounded_radius, speed, wheel_times_fr[i],
                                    max_wheel_speed=self.max_wheel_speed_mmps,
                                    max_rotation_speed=self.max_rotation_speed,
                                    problem_list=self.problem_list)
            if (speed != new_speed) and (abs(new_speed - speed) >= SPEED_MSG_THRESHOLD):
                if rounded_radius == STRAIGHT_RADIUS:
                    l_wheel_speed = new_speed
                    r_wheel_speed = l_wheel_speed
                elif rounded_radius == TURN_IN_PLACE_RADIUS:
                    r_wheel_speed = (math.radians(new_speed) * WHEEL_DIST_MM) / 2.0
                    l_wheel_speed = -r_wheel_speed
                else:
                    # Calculating wheel values for ARC TURNS:
                    # speed = (l_wheel_speed + r_wheel_speed) / 2.0
                    # radius = WHEEL_DIST_MM / 2.0 * ((l_wheel_speed + r_wheel_speed) /
                    #          (r_wheel_speed - l_wheel_speed))
                    #
                    # l = 2*s - r
                    # l = -(r(d-2w)/(d+2w))
                    # 2*s - r = -(r(d-2w)/(d+2w))
                    #
                    # r = sd/2w + s
                    # l = 2s - (sd/2w + s)

                    r_wheel_speed = (new_speed * WHEEL_DIST_MM) / (
                        2 * float(rounded_radius)) + new_speed
                    l_wheel_speed = 2 * new_speed - r_wheel_speed

                l_wheel_value = speed_2_wheel_value(l_wheel_speed,
                                                    wheel_times_fr[i - 1],
                                                    wheel_times_fr[i])
                r_wheel_value = speed_2_wheel_value(r_wheel_speed,
                                                    wheel_times_fr[i - 1],
                                                    wheel_times_fr[i])

                l_wheel_value = round(l_wheel_value, ROUND_WHEEL_VALUE)
                r_wheel_value = round(r_wheel_value, ROUND_WHEEL_VALUE)

                l_move_value = clamp_wheel_value(L_WHEEL_CTR, l_wheel_value,
                                                 wheel_times_fr[i - 1], wheel_times_fr[i])
                r_move_value = clamp_wheel_value(R_WHEEL_CTR, r_wheel_value,
                                                 wheel_times_fr[i - 1], wheel_times_fr[i])

                move_keys_by(L_WHEEL_ROT_ATTR,
                             wheel_times_fr[(i + 1):(len(wheel_times_fr))],
                             l_move_value)
                move_keys_by(R_WHEEL_ROT_ATTR,
                             wheel_times_fr[(i + 1):(len(wheel_times_fr))],
                             r_move_value)
        mc.undoInfo(closeChunk=True, undoName=CLAMP_WHEEL_VAL_UNDO_NAME)
        return frame_nums, new_wheel_values

    def do_speeds_exceed_limits(self):
        frame_nums = []
        all_wheel_speeds, wheel_times_fr = self.get_wheel_speed(True, True)
        if not all_wheel_speeds or all_wheel_speeds == []:
            return None
        mc.undoInfo(openChunk=True, undoName=CLAMP_WHEEL_VAL_UNDO_NAME)
        for i in range(1, len(wheel_times_fr)):
            unrounded_radius, rounded_radius = find_radius(all_wheel_speeds[i - 1][0],
                                                           all_wheel_speeds[i - 1][1])
            rounded_radius = check_radius(rounded_radius, wheel_times_fr[i],
                                          problem_list=self.problem_list)
            if unrounded_radius:
                unrounded_radius = check_radius(unrounded_radius, wheel_times_fr[i],
                                                problem_list=self.problem_list)
            speed = find_speed(all_wheel_speeds[i - 1][0], all_wheel_speeds[i - 1][1],
                               rounded_radius, unrounded_radius)
            new_speed = check_speed(rounded_radius, speed, wheel_times_fr[i],
                                    max_wheel_speed=self.max_wheel_speed_mmps,
                                    max_rotation_speed=self.max_rotation_speed,
                                    problem_list=self.problem_list)
            if (speed != new_speed) and (abs(new_speed - speed) >= SPEED_MSG_THRESHOLD):

                frame_nums.append(wheel_times_fr[i])
        return frame_nums


def check_rad_or_deg_in_prefs():
    """
    This function returns True when using radians and returns False for degrees.
    """
    if mc.optionVar(q="workingUnitAngular") == 'deg':
        return False
    else:
        return True


def check_speed(radius_type, speed, frame_num, max_wheel_speed=MAX_WHEEL_SPEED_MMPS,
                max_rotation_speed=MAX_BODY_ROTATION_SPEED_DEG_PER_SEC, problem_list=None):
    msg = "The %s movement at frame %s has been clamped from %s to %s %s"
    new_msg = None
    new_speed = speed
    if radius_type == STRAIGHT_RADIUS or \
            isinstance(radius_type, int) or \
            isinstance(radius_type, float):
        speed_units = "mm/s"
        if speed > max_wheel_speed:
            new_msg = msg % (radius_type, frame_num, speed, max_wheel_speed, speed_units)
            new_speed = max_wheel_speed
        elif speed < -max_wheel_speed:
            new_msg = msg % (radius_type, frame_num, speed, -max_wheel_speed, speed_units)
            new_speed = -max_wheel_speed

    elif radius_type == TURN_IN_PLACE_RADIUS:
        speed_units = "deg/s"
        if speed > max_rotation_speed:
            new_msg = msg % (radius_type, frame_num, speed, max_rotation_speed, speed_units)
            new_speed = max_rotation_speed
        elif speed < -max_rotation_speed:
            new_msg = msg % (radius_type, frame_num, speed, -max_rotation_speed, speed_units)
            new_speed = -max_rotation_speed

    if problem_list is not None and new_msg and (abs(new_speed - speed) >= SPEED_MSG_THRESHOLD):
        problem_list.append(new_msg)

    return new_speed


def check_radius(radius, frame_num, problem_list):
    if isinstance(radius, str) or radius is None:
        return radius
    msg = "The radius at frame %s has been clamped from %s mm to %s"
    new_msg = None
    if (radius > MAX_RADIUS_MM) or (radius < MIN_RADIUS_MM):
        new_msg = msg % (frame_num, radius, STRAIGHT_RADIUS)
        radius = STRAIGHT_RADIUS
    if exporter_config.get_round_turn_under_point_five():
        if -MIN_RADIUS_THRESHOLD < radius < MIN_RADIUS_THRESHOLD:
            new_msg = msg % (frame_num, radius, TURN_IN_PLACE_RADIUS)
            radius = TURN_IN_PLACE_RADIUS
    if new_msg:
        problem_list.append(new_msg)
    return radius


def clamp_wheel_value(ctr, clamped_value, prev_fr, next_fr):
    attr = ctr + "." + WHEEL_ROT_ATTR
    mc.currentTime(next_fr)
    prev_value = mc.getAttr(attr, time=prev_fr)
    original_value = mc.getAttr(attr)
    mc.setAttr(attr, prev_value + clamped_value)
    print("%s has been clamped to %s on frame %s" % (ctr, clamped_value, next_fr))
    return (prev_value + clamped_value - original_value)


def do_wheels_exist():
    if mc.objExists(L_WHEEL_ROT_ATTR) and mc.objExists(R_WHEEL_ROT_ATTR):
        return True
    return False


def are_mech_keys_between_wheel_keys(current_wheel_key, next_wheel_key):
    if mc.objExists(MECH_ALL_CTR):
        mech_all_times = mc.keyframe(MECH_ALL_CTR, query=True, timeChange=True)
        for mech_key in mech_all_times:
            if current_wheel_key <= mech_key <= next_wheel_key:
                print("%s mech key is after %s and before %s"
                      % (mech_key, current_wheel_key, next_wheel_key))
                return True
    return False


def speed_2_wheel_value(wheel_speed, prev_fr, next_fr):
    """
    Returns the value of a wheel based on speed between two frames
    """
    if next_fr <= prev_fr:
        return
    time_sec = ((next_fr - prev_fr) / ANIM_FPS) * HACK_TIMELINE_SCALE
    rot_num = (wheel_speed * time_sec / math.pi) / WHEEL_DIAMETER_MM
    wheel_value_delta = rot_num * FULL_ROT_DEG
    return wheel_value_delta


def move_keys_by(ctr, keyed_frames, move_by):
    new_values = []
    for frame in keyed_frames:
        original_value = mc.getAttr(ctr, time=frame)
        result_value = original_value + move_by
        new_values.append(result_value)
        mc.setKeyframe(ctr, time=frame, value=result_value)


def find_radius(l_wheel_speed, r_wheel_speed):
    """
    Finds type of movement (fwd, turn or arc turn) and radius in case of arc
    turn
    """
    if l_wheel_speed == r_wheel_speed:
        return None, STRAIGHT_RADIUS
    elif l_wheel_speed == -r_wheel_speed:
        return None, TURN_IN_PLACE_RADIUS

    radius = (WHEEL_DIST_MM / 2.0) * (
    (l_wheel_speed + r_wheel_speed) / (r_wheel_speed - l_wheel_speed))

    if -EQUALITY_THRESHHOLD < radius < EQUALITY_THRESHHOLD:
        # a radius of 0 becomes turn in place
        return None, TURN_IN_PLACE_RADIUS

    # The engine handles radius as an int16, so we round the radius here and
    # then return it as an integer.
    # We need to explicitly round() the value first since int() always rounds
    # down.
    rounded_radius = round(radius)

    if not exporter_config.get_round_turn_under_point_five():
        if 0.0 < radius < 0.5:
            rounded_radius = 1
        elif -0.5 < radius < 0.0:
            rounded_radius = -1
    else:
        if -EQUALITY_THRESHHOLD < rounded_radius < EQUALITY_THRESHHOLD:
            # a rounded radius of 0 becomes turn in place
            return None, TURN_IN_PLACE_RADIUS

    return radius, int(rounded_radius)


def find_speed(l_wheel_speed, r_wheel_speed, rounded_radius, unrounded_radius):
    """
    Finds the speed that should be exported (the same as wheel speed in
    case of fwd movement, average of the two wheels during point turn)
    """
    if rounded_radius == TURN_IN_PLACE_RADIUS:
        if exporter_config.get_turn_wrong_direction():
            # Turn robot in the WRONG DIRECTION for backwards compatibility
            # (see COZMO-12816 for some related info)
            speed = math.degrees((l_wheel_speed - r_wheel_speed) / WHEEL_DIST_MM)
        else:
            # Turn robot in the correct direction
            speed = math.degrees((r_wheel_speed - l_wheel_speed) / WHEEL_DIST_MM)

    # straight and arc turns
    else:
        speed = (l_wheel_speed + r_wheel_speed) / 2.0
        if rounded_radius != STRAIGHT_RADIUS and unrounded_radius != STRAIGHT_RADIUS:
            speed = adjust_arc_speed_to_radius(speed, unrounded_radius, rounded_radius)

    return speed


def adjust_arc_speed_to_radius(speed, old_radius, rounded_radius):
    try:
        new_speed = speed / old_radius * rounded_radius
    except TypeError:
        print("Failed to calculate new speed from speed = %s, old_radius = %s, rounded_radius = %s"
              % (speed, old_radius, rounded_radius))
        return speed
    return new_speed


def place_missing_frames():
    if not are_wheels_keyed():
        # To be run separately from exporter, so don't need to add to error
        # check json
        mc.warning("Must have both wheels keyed at least once in the timeline")
        return
    mc.undoInfo(openChunk=True, undoName=PLACE_MISSING_FRMS_UNDO_NAME)
    l_wheel_times = mc.keyframe(L_WHEEL_ROT_ATTR, q=1, timeChange=1)
    r_wheel_times = mc.keyframe(R_WHEEL_ROT_ATTR, q=1, timeChange=1)
    if l_wheel_times:
        for frame in l_wheel_times:
            if frame not in r_wheel_times:
                mc.setKeyframe(R_WHEEL_ROT_ATTR, insert=True, time=frame)
    if r_wheel_times:
        for frame in r_wheel_times:
            if frame not in l_wheel_times:
                mc.setKeyframe(L_WHEEL_ROT_ATTR, insert=True, time=frame)
    mc.undoInfo(closeChunk=True, undoName=PLACE_MISSING_FRMS_UNDO_NAME)


def are_all_frames_on_wheels():
    l_wheel_times = mc.keyframe(L_WHEEL_ROT_ATTR, q=1, timeChange=1)
    r_wheel_times = mc.keyframe(R_WHEEL_ROT_ATTR, q=1, timeChange=1)
    if l_wheel_times:
        for frame in l_wheel_times:
            if frame not in r_wheel_times:
                return False
    if r_wheel_times:
        for frame in r_wheel_times:
            if frame not in l_wheel_times:
                return False
    return True


def rotate_wheels_by(l_wheel_add=DEFAULT_PLUS_STR, r_wheel_add=DEFAULT_PLUS_STR, additive=False,
                     multipliable=False, force_ratio=False, modify_next_keys=False):
    """
    Add specified amount to value of a previous frame
    In case of multiply wheel delta is a wheel multiplier
    """
    mc.undoInfo(openChunk=True, chunkName="im the chunk", undoName=CHUNK_UNDO_NAME,
                redoName="redo chunk")
    execute_rotate_wheels_by(l_wheel_add=l_wheel_add, r_wheel_add=r_wheel_add, additive=additive,
                             multipliable=multipliable,
                             force_ratio=force_ratio, modify_next_keys=modify_next_keys)
    mc.undoInfo(closeChunk=True)


def execute_rotate_wheels_by(l_wheel_add=DEFAULT_PLUS_STR, r_wheel_add=DEFAULT_PLUS_STR,
                             additive=False,
                             multipliable=False, force_ratio=False, modify_next_keys=False):
    if not are_wheels_keyed():
        mc.warning("Must have both wheels keyed at least once in the timeline")

        return
    if additive and multipliable:
        mc.warning(
            "unit test. rotate_wheels_by: cannot be both additive and multipliable, default to additive")
        multipliable = False
    l_wheel_add, r_wheel_add = check_default(l_wheel_add, r_wheel_add, additive, multipliable)

    l_wheel_times = mc.keyframe(L_WHEEL_ROT_ATTR, q=1, timeChange=1)
    r_wheel_times = mc.keyframe(R_WHEEL_ROT_ATTR, q=1, timeChange=1)
    l_wheel_values = mc.keyframe(L_WHEEL_ROT_ATTR, q=1, valueChange=1)
    r_wheel_values = mc.keyframe(R_WHEEL_ROT_ATTR, q=1, valueChange=1)

    if modify_next_keys and l_wheel_times != r_wheel_times:
        mc.warning(MODIFY_KEYS_WARNING)
        return

    mc.undoInfo(openChunk=True, undoName=ROT_WHEEL_UNDO_NAME)

    l_prev_time = mc.findKeyframe(L_WHEEL_ROT_ATTR, which="previous")
    prev_idx = l_wheel_times.index(l_prev_time)
    try:
        current_idx = l_wheel_times.index(mc.currentTime(q=True))
    except ValueError:
        current_idx = None

    l_current_value = mc.getAttr(L_WHEEL_ROT_ATTR)
    r_current_value = mc.getAttr(R_WHEEL_ROT_ATTR)

    if additive:
        l_value = l_current_value + l_wheel_add
        r_value = r_current_value + r_wheel_add

    elif multipliable:
        # We want * button to always move the value up and / button to always
        # move the value down
        # Therefore in a case when value < 0 / button acts like a *
        # and vice versa
        l_prev_value = l_wheel_values[prev_idx]
        r_prev_value = r_wheel_values[prev_idx]

        if l_wheel_add == 0:
            l_value = l_current_value
        else:
            if l_current_value >= 0:
                l_value = l_current_value * l_wheel_add
            else:
                l_value = l_current_value / l_wheel_add

        if r_wheel_add == 0:
            r_value = r_current_value
        else:
            if r_current_value >= 0:
                r_value = r_current_value * r_wheel_add
            else:
                r_value = r_current_value / r_wheel_add

        # Most times we want to preserve the ratio to insure that
        # specific movement remains
        # For example in case of forward movement we want
        # r delta be the same as left

        if force_ratio:
            l_wheel_delta = l_current_value - l_prev_value
            r_wheel_delta = r_current_value - r_prev_value

            if l_current_value < l_prev_value:
                l_wheel_add = 1 / l_wheel_add

            if r_current_value < r_prev_value:
                r_wheel_add = 1 / r_wheel_add

            l_value = l_prev_value + l_wheel_delta * l_wheel_add
            r_value = r_prev_value + r_wheel_delta * r_wheel_add

    else:
        l_prev_value = l_wheel_values[prev_idx]
        r_prev_value = r_wheel_values[prev_idx]
        l_value = l_prev_value + l_wheel_add
        r_value = r_prev_value + r_wheel_add

    # need to find the difference in the values on current frame to change
    # later frames
    l_current_frame_delta = l_value - l_current_value
    r_current_frame_delta = r_value - r_current_value

    mc.setAttr(L_WHEEL_ROT_ATTR, l_value)
    mc.setAttr(R_WHEEL_ROT_ATTR, r_value)
    mc.setKeyframe(L_WHEEL_ROT_ATTR)
    mc.setKeyframe(R_WHEEL_ROT_ATTR)

    # If there was no key on the the current frame need to refill the times
    # and values
    if current_idx is None:
        l_wheel_times = mc.keyframe(L_WHEEL_ROT_ATTR, q=1, timeChange=1)
        r_wheel_times = mc.keyframe(R_WHEEL_ROT_ATTR, q=1, timeChange=1)
        l_wheel_values = mc.keyframe(L_WHEEL_ROT_ATTR, q=1, valueChange=1)
        r_wheel_values = mc.keyframe(R_WHEEL_ROT_ATTR, q=1, valueChange=1)

        current_idx = l_wheel_times.index(mc.currentTime(q=True))

    if modify_next_keys:
        # Move all the keys after the modified one by the same amount
        after_keys_times = l_wheel_times[current_idx:]
        l_after_keys_values = l_wheel_values[current_idx:]
        r_after_keys_values = r_wheel_values[current_idx:]
        for i in range(len(after_keys_times) - 1, 0, -1):
            mc.setKeyframe(L_WHEEL_ROT_ATTR, time=after_keys_times[i],
                           value=l_after_keys_values[i] + l_current_frame_delta)
            mc.setKeyframe(R_WHEEL_ROT_ATTR, time=after_keys_times[i],
                           value=r_after_keys_values[i] + r_current_frame_delta)

    mc.undoInfo(closeChunk=True, undoName=ROT_WHEEL_UNDO_NAME)


def check_default(l_wheel_delta=DEFAULT_PLUS_STR, r_wheel_delta=DEFAULT_PLUS_STR, additive=False,
                  multipliable=False):
    """
    Convert both wheels from strings to default value
    (in case they are strings)
    """
    l_wheel_delta = default_str_2_float(l_wheel_delta, additive, multipliable)
    r_wheel_delta = default_str_2_float(r_wheel_delta, additive, multipliable)

    return l_wheel_delta, r_wheel_delta


def default_str_2_float(value="", additive=True, multipliable=False):
    """
    Convert string to default value using the dict
    So that can put "default_plus" and "default_minus" in json
    instead of values
    """
    if isinstance(value, basestring):
        if additive:
            value = DEFAULT_WHEEL_STR_VALUE[value][0]

        elif multipliable:
            value = DEFAULT_WHEEL_STR_VALUE[value][1]

        else:
            value = DEFAULT_WHEEL_STR_VALUE[value][2]

    return value


def add_to_arc_turn(add_value=5.0, side="left", additive=True, multipliable=False):
    """
    Checks the ratio between wheels at a current segment and adds the value to
    both wheels on a current frame based on that ratio.
    Adds bigger value to the leading wheel.
    """
    mc.undoInfo(openChunk=True, chunkName="im the chunk", undoName=CHUNK_UNDO_NAME,
                redoName="redo chunk")
    execute_add_to_arc_turn(add_value=add_value, side=side, additive=additive,
                            multipliable=multipliable)
    mc.undoInfo(closeChunk=True)


def execute_add_to_arc_turn(add_value=5.0, side="left", additive=True, multipliable=False):
    if not are_wheels_keyed():
        mc.warning("Must have both wheels keyed at least once in the timeline")
        return
    add_value = default_str_2_float(add_value, additive, multipliable)
    if additive and multipliable:
        mc.warning(
            "unit test. add_to_arc_turn: cannot be both additive and multipliable, default to additive")
        multipliable = False
    [l_delta, r_delta], movement_type = get_wheel_values_at_current_segment()
    try:
        ratio = l_delta / r_delta
    except ZeroDivisionError:
        return

    if multipliable:
        l_rot_value = add_value
        r_rot_value = add_value
    else:
        if side == "left":
            l_rot_value = add_value * ratio
            r_rot_value = add_value
        else:
            l_rot_value = add_value
            try:
                r_rot_value = add_value / ratio
            except ZeroDivisionError:
                return

    rotate_wheels_by(l_rot_value, r_rot_value, additive, multipliable, True)


def get_wheel_values_at_current_segment():
    """
    Get wheel values between current and a previous frame and the type
    and side of movement
    """
    if not are_wheels_keyed():
        mc.warning("Must have both wheels keyed at least once in the timeline")
        return

    # Get values at current frame
    current_l_value = round(mc.getAttr(L_WHEEL_ROT_ATTR), ROUND_WHEEL_VALUE)
    current_r_value = round(mc.getAttr(R_WHEEL_ROT_ATTR), ROUND_WHEEL_VALUE)
    # Get values at previous keyed frame
    previous_l_frame = mc.findKeyframe(L_WHEEL_CTR, at="rotateX", which="previous")
    previous_r_frame = mc.findKeyframe(L_WHEEL_CTR, at="rotateX", which="previous")
    if previous_l_frame != previous_r_frame:
        mc.warning("Wheels are not keyed at the same time, values will be based on left wheel")
    previous_l_value = round(mc.getAttr(L_WHEEL_ROT_ATTR, time=previous_l_frame), ROUND_WHEEL_VALUE)
    previous_r_value = round(mc.getAttr(R_WHEEL_ROT_ATTR, time=previous_l_frame), ROUND_WHEEL_VALUE)
    # Find how much does the values change between current and previous frames
    l_delta = current_l_value - previous_l_value
    r_delta = current_r_value - previous_r_value

    # Find turn type and the direction of a turn
    #
    direction = ""

    # Straight
    #
    if l_delta - r_delta == 0 or (math.fabs(l_delta - r_delta) < EQUALITY_THRESHHOLD):
        turn_type = "straight"
        if l_delta > 0:
            direction = "_fwd"
        elif l_delta < 0:
            direction = "_back"
        else:
            mc.warning("There is no wheel movement between current frame and %s" % previous_l_frame)

    # Point turn
    #
    elif l_delta == -r_delta:
        turn_type = "point_turn"
        if l_delta > r_delta:
            direction = "_right"
        else:
            direction = "_left"

    # Arc turn
    #
    else:
        turn_type = "arc_turn"
        if (l_delta + r_delta) > 0:
            direction = "_fwd"
        else:
            direction = "_back"

        if abs(r_delta) > abs(l_delta):
            direction += "_left"
        else:
            direction += "_right"

    movement_type = turn_type + direction
    return [[l_delta, r_delta], movement_type]


def get_bttn_info_at_current_segment():
    """
    For movement_ui.py. Returns dictionary of values of the user defined buttons.
    """
    wheel_data = get_wheel_values_at_current_segment()
    wheel_values = wheel_data[0]
    movement_type = wheel_data[1]
    if movement_type == "straight":
        return None
    bttn_info = {"default_icon": movement_type + ".png",
                 "wheel_rotation_amount": wheel_values,
                 "border_color_hi": MOVEMENT_BUTTON_BORDER_COLOR_HI,
                 "removable": True}
    return bttn_info


def speed_2_sep_speeds(speed, radius):
    if radius == STRAIGHT_RADIUS:
        l_wheel_speed = speed
        r_wheel_speed = l_wheel_speed
    elif radius == TURN_IN_PLACE_RADIUS:
        if exporter_config.get_turn_wrong_direction():
            l_wheel_speed = (math.radians(speed) * WHEEL_DIST_MM) / 2.0
            r_wheel_speed = -l_wheel_speed
        else:
            r_wheel_speed = (math.radians(speed) * WHEEL_DIST_MM) / 2.0
            l_wheel_speed = -r_wheel_speed
    else:
        r_wheel_speed = (speed * WHEEL_DIST_MM) / (2 * float(radius)) + speed
        l_wheel_speed = 2 * speed - r_wheel_speed

    return [l_wheel_speed, r_wheel_speed]
    pass


def moac_2_separate(start=0, end=0, overwrite_mech_all=True):
    mc.undoInfo(openChunk=True, undoName=MOAC_UNDO_NAME)
    key_mech_all()
    if start == 0 and end == 0:
        start = mc.playbackOptions(q=True, minTime=True)
        end = mc.playbackOptions(q=True, maxTime=True)

    mc.currentTime(start)
    mc.setKeyframe(MECH_ALL_CTR, time=start)
    mc.currentTime(end)
    mc.setKeyframe(MECH_ALL_CTR, time=end)

    json_nodes = get_movement_json(start * HACK_TIMELINE_SCALE, end * HACK_TIMELINE_SCALE,
                                   DATA_NODE_NAME,
                                   [])

    # Before going through keys, make sure sep wheels are keyed on the first frame
    mc.currentTime(start)
    mc.setKeyframe(L_WHEEL_ROT_ATTR, time=start)
    mc.currentTime(end)
    mc.setKeyframe(R_WHEEL_ROT_ATTR, time=start)

    wm_i = WheelMovement()
    wm_i.clip_start = start
    wm_i.clip_end = end

    for node in json_nodes:
        prev_fr = time2frame(start, node["triggerTime_ms"])
        current_fr = time2frame(prev_fr, node["durationTime_ms"])
        speed = node["speed"]
        radius = node["radius_mm"]

        speed = check_speed(radius, speed, current_fr, problem_list=wm_i.problem_list)

        l_speed, r_speed = speed_2_sep_speeds(speed, radius)
        l_value = speed_2_wheel_value(l_speed, prev_fr, current_fr)
        r_value = speed_2_wheel_value(r_speed, prev_fr, current_fr)

        # In case there was no movement need to place key on the previous frame
        mc.setKeyframe(L_WHEEL_ROT_ATTR, time=prev_fr)
        mc.setKeyframe(R_WHEEL_ROT_ATTR, time=prev_fr)
        mc.currentTime(current_fr)
        rotate_wheels_by(l_wheel_add=l_value, r_wheel_add=r_value, additive=False)
        mc.setKeyframe(L_WHEEL_ROT_ATTR)
        mc.setKeyframe(R_WHEEL_ROT_ATTR)

    if overwrite_mech_all:
        mc.cutKey(MECH_ALL_CTR, clear=True, time=(start, end))
        mc.cutKey(MOAC_CTR, clear=True, time=(start, end))
        mech_attrs = mc.listAttr(MECH_ALL_CTR, keyable=True)
        moac_attrs = mc.listAttr(MOAC_CTR, keyable=True)
        for attr in mech_attrs:
            mc.setAttr(MECH_ALL_CTR + "." + attr, 0)
        for attr in moac_attrs:
            mc.setAttr(MOAC_CTR + "." + attr, 0)
    mc.undoInfo(closeChunk=True, undoName=MOAC_UNDO_NAME)


def key_mech_all():
    """
    Set keys on mech_all_ctr before converting to sep wheels
    """
    mech_all_times = mc.keyframe(MECH_ALL_CTR, q=1, timeChange=1)
    for frame in mech_all_times:
        mc.currentTime(frame)
        mc.setKeyframe(MECH_ALL_CTR, time=frame)


def time2frame(clip_start, time_to_convert):
    """
    Find time in ms from the frame specified
    """
    frame_num = time_to_convert / SCALED_FPS + clip_start
    return frame_num


def are_wheels_keyed():
    """
    Check if there are keys on left and right wheels
    """
    if not mc.objExists(L_WHEEL_ROT_ATTR) and not mc.objExists(R_WHEEL_ROT_ATTR):
        return False
    l_wheel_values = mc.keyframe(L_WHEEL_ROT_ATTR, q=1, valueChange=1)
    r_wheel_values = mc.keyframe(R_WHEEL_ROT_ATTR, q=1, valueChange=1)
    if l_wheel_values is None or r_wheel_values is None:
        return False
    return True


def do_wheels_start_from_zero():
    l_wheel_values = mc.keyframe(L_WHEEL_ROT_ATTR, q=1, valueChange=1)
    r_wheel_values = mc.keyframe(R_WHEEL_ROT_ATTR, q=1, valueChange=1)
    if not l_wheel_values or not r_wheel_values:
        return False
    if l_wheel_values[0] != 0.0 or r_wheel_values[0] != 0.0:
        return False
    return True


def null_first_wheel_values():
    current_time = mc.currentTime(q=True)
    l_wheel_times = mc.keyframe(L_WHEEL_ROT_ATTR, q=1, timeChange=1)
    r_wheel_times = mc.keyframe(R_WHEEL_ROT_ATTR, q=1, timeChange=1)
    mc.setKeyframe(L_WHEEL_ROT_ATTR, time=l_wheel_times[0], value=0)
    mc.setKeyframe(R_WHEEL_ROT_ATTR, time=r_wheel_times[0], value=0)
    mc.currentTime(current_time) # Need to refresh in order for values to update


