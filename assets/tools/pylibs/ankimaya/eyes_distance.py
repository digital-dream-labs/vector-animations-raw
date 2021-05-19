
import maya.cmds as mc


VIC_EYES_TX_OFFSET = 0.005
VIC_PUPIL_TX_OFFSET = 0.01

R_EYE_TX = "x:mech_eye_R_ctrl.tx"
L_EYE_TX = "x:mech_eye_L_ctrl.tx"
R_PUPIL_TX = "x:mech_R_pupil_ctrl.tx"
L_PUPIL_TX = "x:mech_L_pupil_ctrl.tx"


def eyes_closer():
    # Get the eyes closer
    vic_r_eye_value = mc.getAttr(R_EYE_TX)
    vic_l_eye_value = mc.getAttr(L_EYE_TX)
    mc.setAttr(R_EYE_TX, vic_r_eye_value + VIC_EYES_TX_OFFSET)
    mc.setAttr(L_EYE_TX, vic_l_eye_value - VIC_EYES_TX_OFFSET)


def eyes_apart():
    # Get the eyes further apart
    vic_r_eye_value = mc.getAttr(R_EYE_TX)
    vic_l_eye_value = mc.getAttr(L_EYE_TX)
    mc.setAttr(R_EYE_TX, vic_r_eye_value - VIC_EYES_TX_OFFSET)
    mc.setAttr(L_EYE_TX, vic_l_eye_value + VIC_EYES_TX_OFFSET)


def pupils_closer():
    # Get the hotspots closer
    vic_r_ht_value = mc.getAttr(R_PUPIL_TX)
    vic_l_ht_value = mc.getAttr(L_PUPIL_TX)
    mc.setAttr(R_PUPIL_TX, vic_r_ht_value + VIC_PUPIL_TX_OFFSET)
    mc.setAttr(L_PUPIL_TX, vic_l_ht_value - VIC_PUPIL_TX_OFFSET)


def pupils_apart():
    # Get the hotspots further apart
    vic_r_ht_value = mc.getAttr(R_PUPIL_TX)
    vic_l_ht_value = mc.getAttr(L_PUPIL_TX)
    mc.setAttr(R_PUPIL_TX, vic_r_ht_value - VIC_PUPIL_TX_OFFSET)
    mc.setAttr(L_PUPIL_TX, vic_l_ht_value + VIC_PUPIL_TX_OFFSET)


