import maya.cmds as mc
import ankimaya.game_exporter as ge
import os
import stat

HACK_TIMELINE_SCALE = 0.99
DEFAULT_SHIFTED_ATTRS = ["x:mech_eye_L_ctrl.Lightness", "x:mech_eye_R_ctrl.Lightness",
                         "x:mech_eye_L_ctrl.GlowSize", "x:mech_eye_R_ctrl.GlowSize"]

# get all clips
def adjust_values(shifted_attrs=DEFAULT_SHIFTED_ATTRS):
    game_exporter_anims = ge.get_clip_info('', include_all=True)[2]
    for anim_clip in game_exporter_anims:
        face_keys = anim_clip["face_keyframes"]
        for i in range(len(face_keys)-1,0,-1):
            print i
            key = face_keys[i]
            scaled_key = scale_frame(anim_clip["clip_start"])+scale_frame(key)
            key += anim_clip["clip_start"]
            mc.currentTime(key)
            for attr in shifted_attrs:
                value_at_scaled_key = mc.getAttr(attr, time=scaled_key)
                mc.setAttr(attr, value_at_scaled_key)
                mc.setKeyframe(attr, time=key)

def scale_frame(frame_num):
    return frame_num * HACK_TIMELINE_SCALE

def set_to_linear(ma_files):
    for ma_file in ma_files:
        mc.file(ma_file, froce=True, open=True)
        mc.keyTangent("x:mech_eye_L_ctrl", itt="linear", ott="linear")
        mc.keyTangent("x:mech_eye_R_ctrl", itt="linear", ott="linear")
        mc.file(save=True)

def main(ma_files):
    for ma_file in ma_files:
        mc.file(ma_file, froce=True, open=True)
        #adjust_values()
        #export for test
        #mc.file(save=True)