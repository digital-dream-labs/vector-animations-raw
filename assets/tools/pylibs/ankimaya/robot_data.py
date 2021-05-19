
EYES_CTRL = "x:eyes_all_ctrl"

NUM_PROCEDURAL_FRAMES = 25

FRAME_TYPE_KEY = "Name"
FACE_ANGLE_KEY = "faceAngle"
FACE_CENTER_X_KEY = "faceCenterX"
FACE_CENTER_Y_KEY = "faceCenterY"
FACE_SCALE_X_KEY = "faceScaleX"
FACE_SCALE_Y_KEY = "faceScaleY"
SCANLINE_OPACITY_KEY = "scanlineOpacity"
LEFT_EYE_KEY = "leftEye"
RIGHT_EYE_KEY = "rightEye"
TRIGGER_TIME_KEY = "triggerTime_ms"
DURATION_TIME_KEY = "durationTime_ms"

EMPTY_PROC_FACE_KEYFRAME = {
    FRAME_TYPE_KEY    : "ProceduralFaceKeyFrame",
    FACE_ANGLE_KEY    : 0.0,
    FACE_CENTER_X_KEY : 0.0,
    FACE_CENTER_Y_KEY : 0.0,
    FACE_SCALE_X_KEY  : 1.0,
    FACE_SCALE_Y_KEY  : 1.0,
    SCANLINE_OPACITY_KEY : 1.0,
    LEFT_EYE_KEY      : ([0] * NUM_PROCEDURAL_FRAMES),
    RIGHT_EYE_KEY     : ([0] * NUM_PROCEDURAL_FRAMES),
    TRIGGER_TIME_KEY  : None,
    DURATION_TIME_KEY : 0
}

# The EMPTY_PROC_FACE_KEYFRAME dictionary defined above includes some default values, eg. the
# face center coordinates are (0,0) and the default scale values are 1.0, but it initializes
# all 24 per-eye attributes with a default value of 0. The get_default_procedural_face_keyframe()
# function below will correct those for the attributes that correspond to these indicies into
# that list of 24 per-eye attributes...

CENTER_X_IDX = 0
SCALE_X_IDX = 2
SCALE_Y_IDX = 3
EYE_CORNER_RADIUS_IDXS = range(5, 13) # this gives us 5 to 12 (does NOT include 13)
SATURATION_IDX = 19
LIGHTNESS_IDX = 20


# Mapping from  cozmo-game/unity/cozmo/assets/scripts/generated/clad/types/proceduraleyeparameters.cs,
# which could have probably been included, but we'd still need a way to map those to the maya names.

# WARNING!!!
# In vision engineering "left" means screen left, but in animation it is the character's
# left, so we flip left and right in this suite of scripts (and any baked transforms).
# END HACK WARNING

# The format for the values in this dictionary are (clad attribute name, clad attribute index).
# The index is only used for the "leftEye" and "rightEye" attributes, which use 24 values each.
# For all other attributes, which use a single value, the index is simply set to -1
PROC_FACE_DATA = {
    "FaceCenterX" : (FACE_CENTER_X_KEY, -1),
    "FaceCenterY" : (FACE_CENTER_Y_KEY, -1),
    "FaceScaleX"  : (FACE_SCALE_X_KEY, -1),
    "FaceScaleY"  : (FACE_SCALE_Y_KEY, -1),
    "FaceAngle"   : (FACE_ANGLE_KEY,   -1),
    "ScanlineOpacity" : (SCANLINE_OPACITY_KEY,   -1),

    "LeftEyeCenterX" : (RIGHT_EYE_KEY, CENTER_X_IDX),
    "LeftEyeCenterY" : (RIGHT_EYE_KEY, 1),
    "LeftEyeScaleX"  : (RIGHT_EYE_KEY, SCALE_X_IDX),
    "LeftEyeScaleY"  : (RIGHT_EYE_KEY, SCALE_Y_IDX),
    "LeftEyeAngle"   : (RIGHT_EYE_KEY, 4),
    "Eye_Corner_L_Inner_Lower_X" : (RIGHT_EYE_KEY, 5),
    "Eye_Corner_L_Inner_Lower_Y" : (RIGHT_EYE_KEY, 6),
    "Eye_Corner_L_Inner_Upper_X" : (RIGHT_EYE_KEY, 7),
    "Eye_Corner_L_Inner_Upper_Y" : (RIGHT_EYE_KEY, 8),
    "Eye_Corner_L_Outer_Upper_X" : (RIGHT_EYE_KEY, 9),
    "Eye_Corner_L_Outer_Upper_Y" : (RIGHT_EYE_KEY, 10),
    "Eye_Corner_L_Outer_Lower_X" : (RIGHT_EYE_KEY, 11),
    "Eye_Corner_L_Outer_Lower_Y" : (RIGHT_EYE_KEY, 12),
    "LeftEyeUpperLidY"        : (RIGHT_EYE_KEY, 13),
    "LeftEyeUpperLidAngle"    : (RIGHT_EYE_KEY, 14),
    "Left_Eye_Upper_Lid_Bend" : (RIGHT_EYE_KEY, 15),
    "LeftEyeLowerLidY"        : (RIGHT_EYE_KEY, 16),
    "LeftEyeLowerLidAngle"    : (RIGHT_EYE_KEY, 17),
    "Left_Eye_Lower_Lid_Bend" : (RIGHT_EYE_KEY, 18),
    "LeftEyeSaturation" : (RIGHT_EYE_KEY, SATURATION_IDX),
    "LeftEyeLightness" : (RIGHT_EYE_KEY, LIGHTNESS_IDX),
    "LeftEyeGlowSize" : (RIGHT_EYE_KEY, 21),
    "LeftHotSpotCenterX": (RIGHT_EYE_KEY, 22),
    "LeftHotSpotCenterY": (RIGHT_EYE_KEY, 23),
    "LeftGlowLightness": (RIGHT_EYE_KEY, 24),

    "RightEyeCenterX" : (LEFT_EYE_KEY, CENTER_X_IDX),
    "RightEyeCenterY" : (LEFT_EYE_KEY, 1),
    "RightEyeScaleX"  : (LEFT_EYE_KEY, SCALE_X_IDX),
    "RightEyeScaleY"  : (LEFT_EYE_KEY, SCALE_Y_IDX),
    "RightEyeAngle"   : (LEFT_EYE_KEY, 4),
    "Eye_Corner_R_Inner_Lower_X" : (LEFT_EYE_KEY, 5),
    "Eye_Corner_R_Inner_Lower_Y" : (LEFT_EYE_KEY, 6),
    "Eye_Corner_R_Inner_Upper_X" : (LEFT_EYE_KEY, 7),
    "Eye_Corner_R_Inner_Upper_Y" : (LEFT_EYE_KEY, 8),
    "Eye_Corner_R_Outer_Upper_X"   : (LEFT_EYE_KEY, 9),
    "Eye_Corner_R_Outer_Upper_Y" : (LEFT_EYE_KEY, 10),
    "Eye_Corner_R_Outer_Lower_X" : (LEFT_EYE_KEY, 11),
    "Eye_Corner_R_Outer_Lower_Y" : (LEFT_EYE_KEY, 12),
    "RightEyeUpperLidY"        : (LEFT_EYE_KEY, 13),
    "RightEyeUpperLidAngle"    : (LEFT_EYE_KEY, 14),
    "Right_Eye_Upper_Lid_Bend" : (LEFT_EYE_KEY, 15),
    "RightEyeLowerLidY"        : (LEFT_EYE_KEY, 16),
    "RightEyeLowerLidAngle"    : (LEFT_EYE_KEY, 17),
    "Right_Eye_Lower_Lid_Bend" : (LEFT_EYE_KEY, 18),
    "RightEyeSaturation" : (LEFT_EYE_KEY, SATURATION_IDX),
    "RightEyeLightness" : (LEFT_EYE_KEY, LIGHTNESS_IDX),
    "RightEyeGlowSize" : (LEFT_EYE_KEY, 21),
    "RightHotSpotCenterX": (LEFT_EYE_KEY, 22),
    "RightHotSpotCenterY": (LEFT_EYE_KEY, 23),
    "RightGlowLightness": (LEFT_EYE_KEY, 24)
}

PROC_FACE_ATTRS = PROC_FACE_DATA.keys()


import copy
import maya.cmds as cmds
from interpolation_manager import find_value_for_frame

_node_children_cache = {}


def reset_children_cache():
    global _node_children_cache
    _node_children_cache = {}


# function that determines if strings match of a procedural string
def is_procedural_face_attr(curr_attr):
    if curr_attr in PROC_FACE_ATTRS:
        return True
    return False


def get_default_procedural_face_keyframe():
    """
    The EMPTY_PROC_FACE_KEYFRAME dictionary defined above includes
    some default values, eg. the face center coordinates are (0,0)
    and the default scale values are 1.0, but it initializes all
    24 per-eye attributes with a default value of 0. This function
    will correct those, eg. set default saturation and lightness to 1

    This function currently sets the right eye's center X value
    to -7.316 and the left eye's center X value to 8.107

    This function currently sets these default values for BOTH eyes:
     - scale X = 1.517
     - scale Y = 1.145
     - eye corner radius values = 0.6
     - saturation = 1
     - lightness = 1
    """
    keyframe = copy.deepcopy(EMPTY_PROC_FACE_KEYFRAME)
    keyframe[RIGHT_EYE_KEY][CENTER_X_IDX] = -7.316
    keyframe[LEFT_EYE_KEY][CENTER_X_IDX] = 8.107
    keyframe[LEFT_EYE_KEY][SCALE_X_IDX] = keyframe[RIGHT_EYE_KEY][SCALE_X_IDX] = 1.517
    keyframe[LEFT_EYE_KEY][SCALE_Y_IDX] = keyframe[RIGHT_EYE_KEY][SCALE_Y_IDX] = 1.145
    for idx in EYE_CORNER_RADIUS_IDXS:
        keyframe[LEFT_EYE_KEY][idx] = keyframe[RIGHT_EYE_KEY][idx] = 0.6
    keyframe[LEFT_EYE_KEY][SATURATION_IDX] = keyframe[RIGHT_EYE_KEY][SATURATION_IDX] = 1
    keyframe[LEFT_EYE_KEY][LIGHTNESS_IDX] = keyframe[RIGHT_EYE_KEY][LIGHTNESS_IDX] = 1
    return keyframe


# function that adds (creates new or modifies existing keyframe)
def add_procedural_face_keyframe(curr_attr, trigger_time_ms, duration_time_ms, value,
                                 frame_number, data_node_name, proc_face_keyframes,
                                 fill_new_frame_with_interpolated_values=True, frame_nums=None):
    # search and see if we have something at that time
    # if exists just modify curr_attr value else insert a blank one.
    try:
        frame = proc_face_keyframes[trigger_time_ms]
    except KeyError:
        # Add a completely empty one with logical defaults...
        frame = get_default_procedural_face_keyframe()

        frame[TRIGGER_TIME_KEY] = trigger_time_ms
        if duration_time_ms:
            frame[DURATION_TIME_KEY] = duration_time_ms

        if fill_new_frame_with_interpolated_values:
            # Add the interpolated values for what maya thinks it is at,
            # that way not every attribute needs to be keyed in maya.
            for key, val in PROC_FACE_DATA.iteritems():
                if key == curr_attr:
                    # this attribute will be updated below
                    continue
                fq_key = data_node_name + '.' + key
                connection = cmds.listConnections(fq_key, d=False, s=True, p=True)[0]
                while connection and connection.endswith(".output"):
                    connection = connection.split('.')[0]
                    connection = cmds.listConnections(connection, d=False, s=True, p=True)[0]
                if connection:
                    ctr = connection.split(".")[0]
                    attr_name = connection.split(".")[1]
                    frame_nums = cmds.keyframe(ctr, attribute=attr_name, query=True, timeChange=True)

                # Previously used to check for keyframe on the data node first, but that is
                # unnecessary, since animator would never need to place a key on it.
                if frame_nums:
                    # Query and use the value of this attribute IF it has at least one
                    # keyframe set. If not, stick with the default value that comes
                    # from the get_default_procedural_face_keyframe() function.
                    if frame_number in frame_nums:
                        interp_value = cmds.getAttr(fq_key, time=frame_number)
                    else:
                        interp_value = find_value_for_frame(frame_number, frame_nums, fq_key)
                    _update_proc_face_keyframe(frame, val, interp_value)

        proc_face_keyframes[trigger_time_ms] = frame

    # Modify the current attribute that is being processed...
    _update_proc_face_keyframe(frame, PROC_FACE_DATA[curr_attr], value)


def _update_proc_face_keyframe(frame, clad_attr, value):
    if clad_attr[1] >= 0:
        frame[clad_attr[0]][clad_attr[1]] = value
    else:
        frame[clad_attr[0]] = value


def get_facial_keyframes(clip_start, clip_end, timeline_scale=1.0, node=EYES_CTRL):
    face_keyframes = []
    children = _get_children(node, recursive=True)
    if children:
        ts = cmds.keyframe(children, query=True, timeChange=True, time=(clip_start, clip_end))
        if ts:
            ts = list(set(ts))
            ts.sort()
            face_keyframes = [(x - clip_start) * timeline_scale for x in ts]
    return face_keyframes


def _get_children(node, recursive=False):
    global _node_children_cache

    if (node, recursive) in _node_children_cache:
        return _node_children_cache[(node, recursive)]
    try:
        children = cmds.listRelatives(node, children=True)
    except ValueError:
        children = None
    if not children:
        _node_children_cache[(node, recursive)] = []
        return []
    if not recursive:
        _node_children_cache[(node, recursive)] = children
        return children
    all_children = children[:]
    for child in children:
        grand_children = _get_children(child, recursive)
        if grand_children:
            all_children.extend(grand_children)
    _node_children_cache[(node, recursive)] = all_children
    return all_children


