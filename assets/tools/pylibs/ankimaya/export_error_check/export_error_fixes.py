
KEYS_THRESHOLD = 0.1


import maya.cmds as mc
from ankimaya.export_error_check.error_checker_utils import CHARS, get_char_name, get_anim_curves
import ankimaya.wheel_movement as wm
import ankimaya.eye_keyer as ek


def run_fixes(selected_choices=None,name2nodes=None):
    for node_name in selected_choices:
        node = name2nodes[node_name]
        # Find info about fix function from the choice node
        if "fix_function" in name2nodes[node_name] and \
            node["fix_function"] != "" and \
            node["status"] != "pass":
            # For cases when fix function has message as a param (then being evaled so need it as a
            # variable)
            message = node["message"]
            eval(node["fix_function"])


def fix_frame_rate():
    try:
        mc.currentUnit(time="ntsc")
    except StandardError, e:
        print("Could not convert to 30 fps because: %s" % e)
    else:
        print "Frame rate converted to 30 fps",


def fix_rig_reference():
    try:
        char_name = get_char_name()
    except StandardError:
        print "Cannot reference file, since character name cannot be found. Please check env file",
        return
    mc.file(CHARS[char_name][2], type="mayaAscii", r=True, ignoreVersion=True, gl=True,
            mergeNamespacesOnClash=False, namespace="x", options="v=0;")


def fix_wheel_keys(message):
    """
    Depending on the error message either clamps, nulls or keys wheels
    """
    if "Speeds exceed limits" in message:
        wheel_movement = wm.WheelMovement()
        wheel_movement.clamp_wheel_values()
    if "Wheels are not keyed on every frame" in message:
        wm.place_missing_frames()
    if "Wheels don't start from the value of 0" in message:
        wm.null_first_wheel_values()


def fix_threshold():
    """
    Get all the frames that are too close together and remove the second one
    """
    anim_curves = get_anim_curves()
    for anim_curve in anim_curves:
        all_key_times = mc.keyframe(anim_curve, query=True, timeChange=True)
        if all_key_times:
            for i in range(1, len(all_key_times)):
                if all_key_times[i] - all_key_times[i-1] <= KEYS_THRESHOLD:
                    mc.cutKey(anim_curve, time=(all_key_times[i], all_key_times[i]), clear=True)


def fix_eye_keyframes():
    ek.main()


