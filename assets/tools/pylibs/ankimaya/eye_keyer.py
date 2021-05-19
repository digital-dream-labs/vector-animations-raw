import maya.cmds as mc

#todo: remove this list if end up not needing
EYE_CTRS = ["x:eyeCorner_L_OuterBtm_ctrl",
            "x:eyeCorner_L_OuterTop_ctrl",
            "x:eyeCorner_L_innerBtm_ctrl",
            "x:eyeCorner_L_innerTop_ctrl",
            "x:eyeCorner_R_OuterBtm_ctrl",
            "x:eyeCorner_R_OuterTop_ctrl",
            "x:eyeCorner_R_innerBtm_ctrl",
            "x:eyeCorner_R_innerTop_ctrl",
            "x:mech_L_pupil_ctrl",
            "x:mech_R_pupil_ctrl",
            "x:mech_eye_L_ctrl",
            "x:mech_eye_R_ctrl",
            "x:mech_eyes_all_ctrl",
            "x:mech_lwrLid_L_ctrl",
            "x:mech_lwrLid_R_ctrl",
            "x:mech_upperLid_L_ctrl",
            "x:mech_upperLid_R_ctrl"]

EYE_CTR_ATTRS = ["x:eyeCorner_L_OuterBtm_ctrl.scaleX", "x:eyeCorner_L_OuterBtm_ctrl.scaleY",
            "x:eyeCorner_L_OuterTop_ctrl.scaleX", "x:eyeCorner_L_OuterTop_ctrl.scaleY",
            "x:eyeCorner_L_innerBtm_ctrl.scaleX","x:eyeCorner_L_innerBtm_ctrl.scaleY",
            "x:eyeCorner_L_innerTop_ctrl.scaleX", "x:eyeCorner_L_innerTop_ctrl.scaleY",
            "x:eyeCorner_R_OuterBtm_ctrl.scaleX", "x:eyeCorner_R_OuterBtm_ctrl.scaleY",
            "x:eyeCorner_R_OuterTop_ctrl.scaleX", "x:eyeCorner_R_OuterTop_ctrl.scaleY",
            "x:eyeCorner_R_innerBtm_ctrl.scaleX", "x:eyeCorner_R_innerBtm_ctrl.scaleY",
            "x:eyeCorner_R_innerTop_ctrl.scaleX", "x:eyeCorner_R_innerTop_ctrl.scaleY",
            "x:mech_L_pupil_ctrl.translateX", "x:mech_L_pupil_ctrl.translateY",
            "x:mech_R_pupil_ctrl.translateX", "x:mech_R_pupil_ctrl.translateY",
            "x:mech_eye_L_ctrl.translateX", "x:mech_eye_L_ctrl.translateY",
            "x:mech_eye_L_ctrl.scaleX","x:mech_eye_L_ctrl.scaleY", "x:mech_eye_L_ctrl.rotateZ",
            "x:mech_eye_L_ctrl.Lightness", "x:mech_eye_L_ctrl.GlowSize",
            "x:mech_eye_R_ctrl.translateX", "x:mech_eye_R_ctrl.translateY",
            "x:mech_eye_R_ctrl.scaleX","x:mech_eye_R_ctrl.scaleY", "x:mech_eye_R_ctrl.rotateZ",
            "x:mech_eye_R_ctrl.Lightness", "x:mech_eye_R_ctrl.GlowSize",
            "x:mech_eyes_all_ctrl.translateX", "x:mech_eyes_all_ctrl.translateY",
            "x:mech_eyes_all_ctrl.scaleX", "x:mech_eyes_all_ctrl.scaleY",
            "x:mech_eyes_all_ctrl.rotateZ", "x:mech_eyes_all_ctrl.On",
            "x:mech_lwrLid_L_ctrl.translateY", "x:mech_lwrLid_L_ctrl.rotateZ", "x:mech_lwrLid_L_ctrl.scaleY",
            "x:mech_lwrLid_R_ctrl.translateY", "x:mech_lwrLid_R_ctrl.rotateZ", "x:mech_lwrLid_R_ctrl.scaleY",
            "x:mech_upperLid_L_ctrl.translateY", "x:mech_upperLid_L_ctrl.rotateZ", "x:mech_upperLid_L_ctrl.scaleY",
            "x:mech_upperLid_R_ctrl.translateY", "x:mech_upperLid_R_ctrl.rotateZ", "x:mech_upperLid_R_ctrl.scaleY"]


def main():
    """
    Goes through all the frames and keys attributes on the eyes
    """
    # getting the current frame to get back to that time after finish running the tool
    current_frame = mc.currentTime(q=True)
    # Get
    all_keyframes = []
    for ctr_attr in EYE_CTR_ATTRS:
        keyframes = mc.keyframe(ctr_attr, query=True, timeChange=True)
        try:
            all_keyframes.extend(keyframes)
        except TypeError:
            # Means there are no keys on this attribute
            continue

    # Set
    all_keyframes = list(set(all_keyframes))
    all_keyframes.sort()
    for ctr_attr in EYE_CTR_ATTRS:
        # Set key on all ctrs at the first frame of the list (since setKeyframe doesn't key unkeyed attrs with an insert flag)
        mc.currentTime(all_keyframes[0])
        mc.setKeyframe(ctr_attr, time=all_keyframes[0])
        for frame in all_keyframes[1:]:
            mc.setKeyframe(ctr_attr, insert=True, time=frame)

    mc.currentTime(current_frame)
    print "All eye attributes keyed",

def are_eye_attrs_keyed():
    """
    Returns a message based on missing eyes keys
    """
    if not mc.objExists(EYE_CTR_ATTRS[0]):
        return "%s doesn't exist" %(EYE_CTR_ATTRS[0])
    first_attr_keyframes = mc.keyframe(EYE_CTR_ATTRS[0], query=True, timeChange=True)
    if first_attr_keyframes:
        for ctr_attr in EYE_CTR_ATTRS:
            keyframes = mc.keyframe(ctr_attr, query=True, timeChange=True)
            if keyframes != first_attr_keyframes:
                return "%s and %s keyframes don't match" %(EYE_CTR_ATTRS[0], ctr_attr)
    else:
        all_eye_keyframes = []
        for ctr_attr in EYE_CTR_ATTRS:
            first_attr_keyframes = mc.keyframe(ctr_attr, query=True, timeChange=True)
            if first_attr_keyframes:
                all_eye_keyframes.append(first_attr_keyframes)
        if not all_eye_keyframes:
            return "No eye controllers are keyed"
        else:
            return "No keyframes on %s" %(EYE_CTR_ATTRS[0])

    return True