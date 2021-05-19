

import maya.cmds as mc
import ankimaya.wheel_movement as wm
import math
import ankimaya.json_exporter as je
import export_for_robot as efr
import game_exporter as ge


MIN_RADIUS_THRESHOLD = 0.1


def fix_radius_threshold(clip_start, clip_end):
    wm_i = wm.WheelMovement()
    wm_i.clip_start = clip_start
    wm_i.clip_end = clip_end

    all_wheel_speeds, wheel_times_fr = wm_i.get_wheel_ctr_speeds(place_keyframes=False)

    for idx in range(1, len(wheel_times_fr)):

        l_wheel_speed = all_wheel_speeds[idx - 1][0]
        r_wheel_speed = all_wheel_speeds[idx - 1][1]

        mc.currentTime(wheel_times_fr[idx])  # so that values get updated after setKeyframe

        if l_wheel_speed != 0 and r_wheel_speed != 0:
            radius = wm_i.find_radius(l_wheel_speed, r_wheel_speed)
            speed = wm_i.find_speed(l_wheel_speed, r_wheel_speed)

            if isinstance(radius, float) and radius < wm.MIN_RADIUS_THRESHOLD:
                current_l_wheel_value = mc.getAttr(wm.L_WHEEL_CTR + "." + wm.WHEEL_ROT_ATTR,
                                                   time=wheel_times_fr[idx])
                current_r_wheel_value = mc.getAttr(wm.R_WHEEL_CTR + "." + wm.WHEEL_ROT_ATTR,
                                                   time=wheel_times_fr[idx])

                # find what wheels speeds should be and values from that
                l_wheel_should_be_speed = (math.radians(speed) * wm.WHEEL_DIST_MM) / 2.0
                r_wheel_should_be_speed = -l_wheel_should_be_speed

                l_wheel_value_between_frames = speed_2_wheel_value(l_wheel_should_be_speed,
                                                                   wheel_times_fr[idx - 1],
                                                                   wheel_times_fr[idx])
                r_wheel_value_between_frames = speed_2_wheel_value(r_wheel_should_be_speed,
                                                                   wheel_times_fr[idx - 1],
                                                                   wheel_times_fr[idx])

                l_wheel_value_between_frames = round(l_wheel_value_between_frames, 3)
                r_wheel_value_between_frames = round(r_wheel_value_between_frames, 3)

                prev_l_key_value = mc.getAttr(wm.L_WHEEL_CTR + "." + wm.WHEEL_ROT_ATTR, time = wheel_times_fr[idx - 1])
                prev_r_key_value = mc.getAttr(wm.R_WHEEL_CTR + "." + wm.WHEEL_ROT_ATTR, time = wheel_times_fr[idx - 1])

                new_l_wheel_value = prev_l_key_value + l_wheel_value_between_frames
                new_r_wheel_value = prev_r_key_value + r_wheel_value_between_frames

                l_wheel_value_add = (new_l_wheel_value - current_l_wheel_value)
                r_wheel_value_add = (new_r_wheel_value - current_r_wheel_value)

                mc.currentTime(wheel_times_fr[idx])
                mc.setAttr(wm.L_WHEEL_CTR + "." + wm.WHEEL_ROT_ATTR, new_l_wheel_value)
                mc.setAttr(wm.R_WHEEL_CTR + "." + wm.WHEEL_ROT_ATTR, new_r_wheel_value)
                mc.setKeyframe(wm.L_WHEEL_CTR)
                mc.setKeyframe(wm.R_WHEEL_CTR)

                if wheel_times_fr[idx+1]:
                    move_keys_by(wm.L_WHEEL_CTR + "." + wm.WHEEL_ROT_ATTR,
                                 wheel_times_fr[idx+1:len(wheel_times_fr)],
                                 l_wheel_value_add)
                    move_keys_by(wm.R_WHEEL_CTR + "." + wm.WHEEL_ROT_ATTR,
                                 wheel_times_fr[idx + 1:len(wheel_times_fr)],
                                 r_wheel_value_add)

                if (current_l_wheel_value != new_l_wheel_value and current_r_wheel_value != new_r_wheel_value):
                    print("frame %s - changing l_wheel from %s to %s"
                          % (wheel_times_fr[idx], current_l_wheel_value, new_l_wheel_value))
                    print("frame %s - changing r_wheel from %s to %s"
                          % (wheel_times_fr[idx], current_r_wheel_value, new_r_wheel_value))


def speed_2_wheel_value(wheel_speed, prev_fr, next_fr):
    time_sec = ((next_fr - prev_fr) / je.ANIM_FPS) * je.HACK_TIMELINE_SCALE
    rot_num = (wheel_speed * time_sec / math.pi) / wm.WHEEL_DIAMETER_MM
    wheel_value_delta = rot_num * wm.FULL_ROT_DEG
    return wheel_value_delta


def move_keys_by(ctr, keyed_frames, move_by):
    for frame in keyed_frames:
        original_value = mc.getAttr(ctr, time=frame)
        result_value = original_value + move_by
        mc.setKeyframe(ctr, time=frame, value=result_value)


def main():
    export_subdir, clip_names_updated, clip_infos = ge.get_clip_info(time_scale=je.HACK_TIMELINE_SCALE,
                                                                     default_name=efr.DEFAULT_TAR_FILE.split('.')[0],
                                                                     include_all=False)
    for clip_info in clip_infos:
        fix_radius_threshold(clip_info["clip_start"], clip_info["clip_end"])


