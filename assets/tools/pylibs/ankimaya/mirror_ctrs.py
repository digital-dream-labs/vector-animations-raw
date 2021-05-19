"""
Takes values from one side of the robot and places them on the other
And vice versa
"""

import maya.cmds as mc


L_WHEEL = "x:wheel_L_ctrl"
R_WHEEL = "x:wheel_R_ctrl"

EYE_CTRS_HORIZONTAL_PAIRS = {
                            "x:mech_eye_L_ctrl.translateX":"x:mech_eye_R_ctrl.translateX",
                            "x:mech_L_pupil_ctrl.tx":"x:mech_R_pupil_ctrl.tx",
                            "x:mech_eyes_all_ctrl.tx":"x:mech_eyes_all_ctrl.tx"
                            }

EYE_CTRS_VERTICAL_PAIRS = {
                            "x:mech_upperLid_L_ctrl.rotateZ": "x:mech_upperLid_R_ctrl.rotateZ",
                            "x:mech_lwrLid_L_ctrl.rotateZ": "x:mech_lwrLid_R_ctrl.rotateZ",
                            "x:mech_eye_L_ctrl.rotateZ": "x:mech_eye_R_ctrl.rotateZ",
                            "x:mech_L_pupil_ctrl.ty":"x:mech_R_pupil_ctrl.ty",
                            "x:mech_upperLid_L_ctrl.translateY":"x:mech_upperLid_R_ctrl.translateY",
                            "x:mech_upperLid_L_ctrl.scaleY":"x:mech_upperLid_R_ctrl.scaleY",

                            "x:mech_lwrLid_L_ctrl.translateY": "x:mech_lwrLid_R_ctrl.translateY",
                            "x:mech_lwrLid_L_ctrl.scaleY": "x:mech_lwrLid_R_ctrl.scaleY",

                            "x:mech_eye_L_ctrl.translateY":"x:mech_eye_R_ctrl.translateY",
                            "x:mech_eye_L_ctrl.scaleY":"x:mech_eye_R_ctrl.scaleY",

                            "x:eyeCorner_L_innerTop_ctrl.sx": "x:eyeCorner_R_OuterTop_ctrl.sx",
                            "x:eyeCorner_L_innerBtm_ctrl.sx": "x:eyeCorner_R_OuterBtm_ctrl.sx",
                            "x:eyeCorner_L_OuterBtm_ctrl.sx": "x:eyeCorner_R_innerBtm_ctrl.sx",
                            "x:eyeCorner_L_OuterTop_ctrl.sx": "x:eyeCorner_R_innerTop_ctrl.sx",
                            "x:mech_eye_L_ctrl.sx":"x:mech_eye_R_ctrl.sx",

                            "x:eyeCorner_L_innerTop_ctrl.sy": "x:eyeCorner_R_OuterTop_ctrl.sy",
                            "x:eyeCorner_L_innerBtm_ctrl.sy": "x:eyeCorner_R_OuterBtm_ctrl.sy",
                            "x:eyeCorner_L_OuterBtm_ctrl.sy": "x:eyeCorner_R_innerBtm_ctrl.sy",
                            "x:eyeCorner_L_OuterTop_ctrl.sy": "x:eyeCorner_R_innerTop_ctrl.sy"
                        }


def mirror_eyes(r2l=True,l2r=True):
    mc.undoInfo(openChunk=True)
    for l_attr, r_attr in EYE_CTRS_HORIZONTAL_PAIRS.iteritems():
        r_h_value = mc.getAttr(r_attr)
        l_h_value = mc.getAttr(l_attr)
        if r2l:
            mc.setAttr(l_attr, -r_h_value)
        if l2r:
            mc.setAttr(r_attr, -l_h_value)

    for l_attr, r_attr in EYE_CTRS_VERTICAL_PAIRS.iteritems():
        r_v_value = mc.getAttr(r_attr)
        l_v_value = mc.getAttr(l_attr)
        if r2l:
            mc.setAttr(l_attr, r_v_value)
        if l2r:
            mc.setAttr(r_attr, l_v_value)
    mc.undoInfo(closeChunk=True)


def mirror_movement():
    #get all times and values
    #get values on current frame
    #get values on previous frame
    #difference_between_l_wheel = current_frame_l_value-previous_frame_l_value
    # r_weel_value = previous_frame_r_wheel+difference_between_l_wheel

    # difference_between_r_wheel = current_frame_l_value-previous_frame_l_value
    #l_weel_value = previous_frame_l_wheel+difference_between_r_wheel

    # mc.setAttr(L_WHEEL, l_weel_value)
    # mc.setAttr(R_WHEEL, r_weel_value)
    pass


