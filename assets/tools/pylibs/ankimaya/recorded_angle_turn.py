# coding=utf-8
"""
In some cases, because of the friction, momentum and related factors Cozmo can end up at the position
not expected from the previous body motion key frames. This can be problematic if, for example, at
the end of animation he needs to face the same direction as where he faced in the beginning.

This script places two new keyframes into the exported file: "RecordHeadingKeyFrame" and
"TurnToRecordedHeadingKeyFrame". The first one records where Cozmo is facing and the second one
adjusts his rotation in order to face the same direction as the one at the recorded time.

Animators set one key of the RECORD_ANGLE_CTR in Maya. The time at which it’s keyed becomes the
trigger time for RecordHeadingKeyFrame. TurnToRecordedHeadingKeyFrame is always placed at the
end, however it’s trigger time differs depending on whether we override the last turn or not.

Animators have control over whether to force overriding the last turn or not, which is being
specified by the OVERWRITE_LAST_ATTR. In case previous keyframe is not TURN_IN_PLACE, last keyframe
is not being overwritten, but rather Cozmo’s position is getting adjusted at the end.
For overriding the last turn, use set_turn_json() function.
For adjusting Cozmo’s rotation at the end, use set_adjust_json() function.
get_return_to_recorded_json() and get_recorded_key_json() are the two public functions which are
being called in export_for_robot.py after Cozmo’s movement is calculated.

In case of the adjusted rotation, we have him follow the shortest distance using the speed and
duration from the turn that is being overwritten. That rotation is always less than 180 deg,
so numHalfRevs is set to 0 in that case.
"""

# daria.jerjomina@anki.com
# May 3, 2017


import math
import maya.cmds as mc
import ankimaya.json_exporter as je
from ankimaya.export_error_check.error_checker_utils import add_json_node

DEFAULT_DURATION = 500

DEFAULT_SPEED = 500

RECORD_FROM_JSON_NODE = {"triggerTime_ms": None,
                         "Name": "RecordHeadingKeyFrame"}

RECORD_TO_JSON_NODE = {"triggerTime_ms": None,
                       "durationTime_ms": DEFAULT_DURATION, # How much time to complete turn. If not given enough turn
                       "offset_deg": 0,  # Offset from recorded value, in our case should always be 0
                       "speed_degPerSec": DEFAULT_SPEED,
                       "accel_degPerSec2": 1000,
                       "decel_degPerSec2": 1000,
                       "tolerance_deg": 2,  # How close to the target should be before gives up turning
                       "numHalfRevs": 0,
                       "useShortestDir": False,
                       "Name": "TurnToRecordedHeadingKeyFrame"}

RECORD_ANGLE_CTR = "x:recorded_angle_ctr"
DURATION_ATTR = "duration_ms"
ACCEL_ATTR = "accel"
DECEL_ATTR = "decel"
OVERWRITE_LAST_ATTR = "overwrite_last"
MIN_DURATION = DEFAULT_DURATION  # In case duration is accidentally set to 0, it will instead use this number
HALF_ROT_DEG = math.degrees(math.pi)


class RecordedAngleTurn(object):

    def __init__(self):
        self.record_to_json_node = dict.copy(RECORD_TO_JSON_NODE)
        self.recorded_frame = 0.0
        self.overwrite_last = False  # Keep track of whether previous movement node
        self.added_message = False

    def find_record_key_frame(self, clip_start, clip_end):
        """
        Finds the frame at which the RECORD_ANGLE_CTR was keyed in the maya scene
        """
        recorded_frames = mc.keyframe(RECORD_ANGLE_CTR,
                                      query=True,
                                      timeChange=True,
                                      time=(clip_start, clip_end))
        if recorded_frames is None:
            if not self.added_message:
                msg = "No keys set on %s, won't be exported" %(RECORD_ANGLE_CTR)
                add_json_node(node_name="Recorded angle",
                              fix_function="", status="pass",
                              message=msg)
                self.added_message = True
            self.recorded_frame = None
            return None
        # if all times are the same, means only one keyed frame
        elif not all(i==recorded_frames[0] for i in recorded_frames) and not self.added_message:
            msg = "There is more than one key set on %s. Will use first key"
            add_json_node(node_name="Recorded angle",
                          fix_function="", status="warning",
                          message=msg)
            self.added_message = True
        self.recorded_frame = recorded_frames[0]

    def get_recorded_key_json(self, clip_start, clip_end):
        """
        Returns RecordHeadingKeyFrame json
        """
        if not mc.objExists(RECORD_ANGLE_CTR):
            return None
        self.find_record_key_frame(clip_start, clip_end)
        if self.recorded_frame is not None:
            trigger_time_ms = je.convert_time(self.recorded_frame, offset=clip_start) * je.HACK_TIMELINE_SCALE
            record_from_json_node = dict.copy(RECORD_FROM_JSON_NODE)
            record_from_json_node["triggerTime_ms"] = int(round(trigger_time_ms))
            return record_from_json_node
        return None

    def get_return_to_recorded_json(self, last_movement_json, clip_start, clip_end):
        """
        Returns TurnToRecordedHeadingKeyFrame json
        """
        if not mc.objExists(RECORD_ANGLE_CTR):
            return None
        self.find_record_key_frame(clip_start, clip_end)
        if self.recorded_frame is None:
            return None

        # Add turn in the end to adjust robot's position
        if (last_movement_json["radius_mm"] != "TURN_IN_PLACE" or
                mc.getAttr(RECORD_ANGLE_CTR + "." + OVERWRITE_LAST_ATTR) != True):
            self.set_adjust_json(last_movement_json)
        else:
            # replace last turn
            self.set_turn_json (last_movement_json)

        return self.record_to_json_node

        # if the last not turn in place

    def set_turn_json(self, last_movement_json):
        """
        Overwrites last turn to be returning to recorded frame turn
        """
        self.overwrite_last = True
        duration_buffer = mc.getAttr(RECORD_ANGLE_CTR + "." + DURATION_ATTR, time=self.recorded_frame)
        if duration_buffer < MIN_DURATION:
            duration_buffer = MIN_DURATION
        self.record_to_json_node["triggerTime_ms"] = int(round(last_movement_json["triggerTime_ms"]))
        self.record_to_json_node["durationTime_ms"] = int(round(last_movement_json["durationTime_ms"]+duration_buffer))
        self.record_to_json_node["speed_degPerSec"] = int(round(last_movement_json["speed"]))
        self.record_to_json_node["accel_degPerSec2"] = int(round(mc.getAttr(RECORD_ANGLE_CTR + "." + ACCEL_ATTR, time=self.recorded_frame)))
        self.record_to_json_node["decel_degPerSec2"] = int(round(mc.getAttr(RECORD_ANGLE_CTR + "." + DECEL_ATTR, time=self.recorded_frame)))
        degrees_turned = last_movement_json["speed"] * (last_movement_json["durationTime_ms"]/1000.0)

        # TODO: int() always rounds down, so should this use int(round(...)) instead?
        self.record_to_json_node["numHalfRevs"] = int(degrees_turned / HALF_ROT_DEG)

        self.record_to_json_node["useShortestDir"] = False

    def set_adjust_json(self, last_movement_json):
        """
        Adds a turn at the end of the last motion
        """
        self.overwrite_last = False
        duration = mc.getAttr(RECORD_ANGLE_CTR + "." + DURATION_ATTR, time=self.recorded_frame)
        if duration < MIN_DURATION:
            duration = MIN_DURATION
        trigger_time_ms = last_movement_json["triggerTime_ms"] + last_movement_json["durationTime_ms"]
        self.record_to_json_node["useShortestDir"] = True
        self.record_to_json_node["triggerTime_ms"] = int(round(trigger_time_ms))
        self.record_to_json_node["durationTime_ms"] = int(round(duration))
        self.record_to_json_node["speed_degPerSec"] = int(round(last_movement_json["speed"]))
        self.record_to_json_node["accel_degPerSec2"] = int(round(mc.getAttr(RECORD_ANGLE_CTR + "." + ACCEL_ATTR, time=self.recorded_frame)))
        self.record_to_json_node["decel_degPerSec2"] = int(round(mc.getAttr(RECORD_ANGLE_CTR + "." + DECEL_ATTR, time=self.recorded_frame)))


