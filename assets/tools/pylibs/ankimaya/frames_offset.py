"""
The purpose of this tool is to give an animator ability to preserve
the value of the keys following the key they are changing.

The animator would run the record_start() method first to record
the value of the frame that they are going to change. That saves the
value of the selected keys and information about the animation curve
they are on.  Animator would then run offset_keys() method. That
gets the delta values based on the change that happened since running
the record_start() and applies that delta to all the keys in the
timeline that follow selected frame (for it's anim curve)
"""

import maya.cmds as mc
import copy


CURRENT_IDX = "current_idx"
START_VALUE = "start_value"
END_VALUE = "end_value"
ALL_TIMES = "all_times"
ALL_VALUES = "all_values"

# This information is being stored for each anim curve that has selected
# keys on the moment of record_start()
ANIM_CURVE_INFO = { CURRENT_IDX : None,
                    START_VALUE : None,
                    END_VALUE   : None,
                    ALL_TIMES   : None,
                    ALL_VALUES  : None }


class FramesOffset(object):
    def __init__(self):
        # Main dictionary that is going to be populated with all the info needed for the ofset
        self.keys_info = {} # {anim_curve: [current_key_idx, value_delta, all_times, all_values]}
        self.anim_curves = []

    def record_start(self):
        """
        This method is to be run by an animator. It stores information about selected keyframes.
        """
        self.anim_curves = mc.keyframe(q=True, name=True)
        if self.anim_curves is None:
            print "Please select keyframes which should be taken into account for update",
            return
        self.populate_anim_curves_start_info()

    def populate_anim_curves_start_info(self):
        """
        Populate anim curve data to later use it for changing values of the following keys
        """
        for anim_curve in self.anim_curves:
            all_key_values = mc.keyframe(anim_curve, query=True, valueChange=True)
            all_key_times = mc.keyframe(anim_curve, query=True, timeChange=True)
            # Get selected keys for only this particular anim curve, since will be modifying keys
            # per each recorded anim curve
            selected_key_indexes = mc.keyframe(anim_curve, q=True, selected=True, indexValue=True)

            if selected_key_indexes:
                if len(selected_key_indexes) > 1:
                    print "Only supports single frame per anim curve, the first of the selected keys"\
                          " on %s will be used" % anim_curve,
            else:
                continue

            current_idx = selected_key_indexes[0]
            start_value = all_key_values[current_idx]

            self.keys_info[anim_curve] = copy.deepcopy(ANIM_CURVE_INFO)
            self.keys_info[anim_curve][CURRENT_IDX] = current_idx
            self.keys_info[anim_curve][ALL_TIMES] = all_key_times
            self.keys_info[anim_curve][ALL_VALUES] = all_key_values
            self.keys_info[anim_curve][START_VALUE] = start_value

    def populate_anim_curves_end_info(self):
        """
        Add end value that will be accounted for during the calculation of a delta between keys
        """
        for anim_curve in self.anim_curves:
            new_key_values = mc.keyframe(anim_curve, query=True, valueChange=True)
            self.keys_info[anim_curve][END_VALUE] =\
                new_key_values[self.keys_info[anim_curve][CURRENT_IDX]]

    def offset_keys_for_anim_curve(self, anim_curve, current_idx, key_times, key_values, value_delta):
        """
        Offset keys that go after the selected ones for a specific anim curve
        """
        after_key_times = key_times[current_idx:]
        after_key_values = key_values[current_idx:]
        for i in range(len(after_key_times)-1, 0, -1):
            mc.setKeyframe(anim_curve, time=after_key_times[i],
                           value=after_key_values[i] + value_delta)

    def offset_keys(self):
        """
        This method is to be run by an animator.
        It modifies the keys after the selected ones per each of the anim curves
        """
        self.populate_anim_curves_end_info()
        for anim_curve, anim_curve_info in self.keys_info.iteritems():
            after_keys_times = anim_curve_info[ALL_TIMES][anim_curve_info[CURRENT_IDX]:]
            after_keys_values = anim_curve_info[ALL_VALUES][anim_curve_info[CURRENT_IDX]:]
            value_delta = anim_curve_info[END_VALUE] - anim_curve_info[START_VALUE]
            # Move all the keys after the modified one by the same amount
            for i in range(len(after_keys_times)-1, 0, -1):
                mc.setKeyframe(anim_curve, time=after_keys_times[i],
                               value=after_keys_values[i] + value_delta)


