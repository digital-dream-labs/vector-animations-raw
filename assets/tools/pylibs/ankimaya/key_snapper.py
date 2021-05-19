import maya.cmds as mc

# Purpose of this script is to copy keyframe values to selected keys from either previous or next
# keyframe as well as averaging between them

# June 27, 2016
# daria.jerjomina@anki.com

# June 28, 2016
# Added copying of tangents
# daria.jerjomina@anki.com

# October 4, 2016
# Supports working with multiple curves

# January 27, 2017
# Copies tangent type, but keeps tangent weight

# Sept 10, 2018
# Added function to split a list of key indices into separate lists if there are gaps in the sequence of indices

MODE_STR = "mode"
HALF_STR = "half"
ANIM_CURVE_STR = "anim_curve"
ALL_KEY_VALUES_STR = "all_key_values"
ALL_KEY_TIMES_STR = "all_key_times"
SELECTED_KEY_INDICES_STR = "selected_key_indices"

NEXT_STR = "next"
PREVIOUS_STR = "previous"

class KeySeq(object):
    def __init__(self, *args, **kwargs):
        #[daria] I would make these strings constants
        # Also, is there a reason for making these optional? If these kwargs are always being passed
        # in copyKeys, maybe should specify them as parameters to a function?
        self.mode = kwargs.get(MODE_STR, HALF_STR)
        self.anim_curve = kwargs.get(ANIM_CURVE_STR, None)
        self.all_key_values = kwargs.get(ALL_KEY_VALUES_STR, [])
        self.all_key_times = kwargs.get(ALL_KEY_TIMES_STR, [])
        self.selected_key_indices = kwargs.get(SELECTED_KEY_INDICES_STR, [])

    def do_copy_keys(self):
        last_key_index = max(self.selected_key_indices)
        first_key_index = min(self.selected_key_indices)
        from_index = 0.5
        if self.mode == NEXT_STR:
            from_index = last_key_index + 1
        elif self.mode == PREVIOUS_STR:
            from_index = first_key_index - 1

        if from_index >= len(self.all_key_values) or from_index < 0:
            print "Please make sure there is a keyframe to copy from on " + self.anim_curve
            return

        if from_index != 0.5:
            tangent_info = mc.keyTangent(self.anim_curve,
                                         index=(from_index, from_index),
                                         query=True,
                                         inAngle=True,
                                         outAngle=True,
                                         inWeight=True,
                                         outWeight=True,
                                         inTangentType=True,
                                         outTangentType=True
                                         )

        key_times = []
        for index in self.selected_key_indices:
            key_times.append(self.all_key_times[index])
            if from_index != 0.5:
                # Get original tangent values so that can maintain tangent values, but copy the type
                original_tangent_info = mc.keyTangent(self.anim_curve,
                                                      index=(index, index),
                                                      query=True,
                                                      inAngle=True,
                                                      outAngle=True,
                                                      inWeight=True,
                                                      outWeight=True,
                                                      inTangentType=True,
                                                      outTangentType=True
                                                      )
                mc.keyTangent(self.anim_curve,
                              index=(index, index),
                              inAngle=original_tangent_info[0],
                              outAngle=original_tangent_info[1],
                              inWeight=original_tangent_info[2],
                              outWeight=original_tangent_info[3],
                              inTangentType=tangent_info[4],
                              outTangentType=tangent_info[5]
                              )
        try:
            # Half way copying does not copy tangents (since don't know which key to copy from)
            if from_index == 0.5:
                result_value = (self.all_key_values[last_key_index + 1] + self.all_key_values[
                    first_key_index - 1]) / 2
            else:
                result_value = self.all_key_values[from_index]
        except IndexError:
            print "Please make sure there are keyframes to copy from on " + self.anim_curve
            return

        mc.setKeyframe(self.anim_curve, time=key_times, value=result_value)


def split_index_list(main_list):
    """
    This function takes a list that may or may not have gaps in the sequences
    and returns a list of lists, where each child list is contiguous.
    """
    all_lists = []
    new_list = []
    for i in range(len(main_list) - 1):
        new_list.append(main_list[i])
        if main_list[i] + 1 != main_list[i + 1]:
            all_lists.append(new_list)
            new_list = []
    new_list.append(main_list[-1])
    all_lists.append(new_list)
    return all_lists


# [daria] This script might have been originaly written before we agreed to use pep8, but now that we
# did, it's probably a good idea to rename this function to copy_keys both here and on the shelf
def copyKeys(mode=NEXT_STR):
    anim_curves = mc.keyframe(q=1, name=1)
    if anim_curves is None:
        print "Please select keyframes which values to change"
        return

    key_seqs = []
    for anim_curve in anim_curves:
        all_key_values = mc.keyframe(anim_curve, query=True, valueChange=True)
        all_key_times = mc.keyframe(anim_curve, query=True, timeChange=True)
        selected_key_indices = mc.keyframe(anim_curve, query=True, selected=True, indexValue=True)

        new_index_list = split_index_list(selected_key_indices)
        for l in new_index_list:
            key_seqs.append(KeySeq(mode=mode, anim_curve=anim_curve, all_key_values=all_key_values,
                                   selected_key_indices=l,
                                   all_key_times=all_key_times))

    for ks in key_seqs:
        ks.do_copy_keys()