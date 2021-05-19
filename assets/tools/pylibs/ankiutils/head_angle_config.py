

# This dictionary maps: { num_head_angle_variations : { head_angle_offset : (min_head_angle_for_this_variation,
#                                                                            max_head_angle_for_this_variation) } }

DEFAULT_HEAD_ANGLE_CONFIG = {
    0 : {},
    3 : { -20 : (-25, -10),
            0 : (-10, +10),
          +20 : (+10, +30),
          +40 : (+30, +45) },
    6 : { -20 : (-25, -15),
          -10 : (-15,  -5),
            0 : ( -5,  +5),
          +10 : ( +5, +15),
          +20 : (+15, +25),
          +30 : (+25, +35),
          +40 : (+35, +45) },
}


# These constants are set to strings that match the input arguments to
# the add_head_lift_keyframe() method in ankimaya/export_for_robot.py

FIRST_KEYFRAME = "first_head_angle_keyframe_offset"
LAST_KEYFRAME  = "last_head_angle_keyframe_offset"
ALL_KEYFRAMES  = "all_head_angle_keyframes_offset"

# As defined in the dictionary below:
# use 0 to only offset the first head angle keyframe
# use 1 to offset the first and last head angle keyframes
# use 2 to only offset the last head angle keyframe
# use 3 to offset all head angle keyframes

DEFAULT_WHICH_KEYFRAMES_CONFIG = {
    0 : ((FIRST_KEYFRAME,), "first keyframe only"),
    1 : ((FIRST_KEYFRAME, LAST_KEYFRAME), "first & last keyframes only"),
    2 : ((LAST_KEYFRAME,), "last keyframe only"),
    3 : ((ALL_KEYFRAMES,), "all keyframes")
}

DEFAULT_WHICH_KEYFRAME = 0


INVALID_SETTING_MSG = "WARNING: No setting found for %s head angle variations"

ANIM_VARIATION_SUFFIX = "_head_angle_%s"

MIN_HEAD_ANGLE_DEG = -22
MAX_HEAD_ANGLE_DEG = +45


class HeadAngleConfig(object):

    no_variations = [0, "0", None, "None", "No"]

    def __init__(self, head_angle_config=None, which_keyframes_config=None):
        if head_angle_config is None:
            self.head_angle_config = DEFAULT_HEAD_ANGLE_CONFIG
        else:
            self.head_angle_config = head_angle_config
        if which_keyframes_config is None:
            self.which_keyframes_config = DEFAULT_WHICH_KEYFRAMES_CONFIG
        else:
            self.which_keyframes_config = which_keyframes_config

    def get_which_keyframe_params(self, which_keyframe_code):
        try:
            return self.which_keyframes_config[which_keyframe_code][0]
        except KeyError, e:
            print(e)
            return self.which_keyframes_config[DEFAULT_WHICH_KEYFRAME][0]

    def get_offsets(self, num_variations, remove_zero_offset=True):
        if num_variations in self.no_variations:
            return []
        num_variations = int(num_variations)
        if num_variations not in self.head_angle_config:
            msg = INVALID_SETTING_MSG % num_variations
            msg += ", so no offsets will be returned"
            print(msg)
            return []
        offsets = self.head_angle_config[num_variations].keys()
        if remove_zero_offset:
            try:
                offsets.remove(0)
            except ValueError:
                pass
        offsets.sort()
        return offsets

    def get_which_keyframes_display_string(self, dict_key):
        try:
            return self.which_keyframes_config[dict_key][1]
        except KeyError, e:
            print(e)
            return ''

    def get_which_keyframes_display_strings(self):
        display_strings = [which_keyframes[1] for which_keyframes in self.which_keyframes_config.values()]
        return display_strings

    def get_num_variations_display_string(self, num_variations):
        if num_variations in self.no_variations:
            return "No"
        num_variations = int(num_variations)
        disp_string = "%s variations %s" % (num_variations, self.get_offsets(num_variations))
        return disp_string

    def get_num_variations_display_strings(self):
        display_strings = []
        num_variations_options = self.head_angle_config.keys()
        num_variations_options.sort()
        for num_variations in num_variations_options:
            display_strings.append(self.get_num_variations_display_string(num_variations))
        return display_strings

    def get_num_variations_from_display(self, disp_string):
        if disp_string in self.no_variations:
            return 0
        num_variations = disp_string.split()[0]
        num_variations = int(num_variations)
        return num_variations

    def get_info_from_display(self, disp_string):
        num_variations = self.get_num_variations_from_display(disp_string)
        return self.head_angle_config[num_variations]

    def get_which_keyframes_from_display(self, disp_string):
        for code, which_keyframes in self.which_keyframes_config.items():
            input_args, description = which_keyframes[:]
            if disp_string == description:
                return (code, input_args)
        return (None, None)

    def get_anim_variation_to_range_mapping(self, anim_clip, num_variations):
        default_mapping = { anim_clip : (MIN_HEAD_ANGLE_DEG, MAX_HEAD_ANGLE_DEG) }
        if num_variations in self.no_variations:
            return default_mapping
        num_variations = int(num_variations)
        if num_variations not in self.head_angle_config:
            msg = INVALID_SETTING_MSG % num_variations
            msg += ", so the original animation will be used for entire head angle range"
            print(msg)
            return default_mapping
        mapping = {}
        for offset, range in self.head_angle_config[num_variations].items():
            if offset == 0:
                anim_name = anim_clip
            else:
                anim_name = anim_clip + ANIM_VARIATION_SUFFIX % offset
            mapping[anim_name] = range
        return mapping


