import maya.cmds as mc

"""
This tool is to be used by when there is a need to transfer values from the separate wheel system
to the new visual system that uses one ctrl with two attributes for rotation and ratio

daria@anki.com
June 1 2017 - initial commit
"""


L_WHEEL_CTR = "x:wheel_L_ctrl"
R_WHEEL_CTR = "x:wheel_R_ctrl"
WHEEL_ROT_ATTR = "rotateX"

L_WHEEL_GRP = "x:wheel_L_grp"
R_WHEEL_GRP = "x:wheel_R_grp"
WHEELS_CTR = "x:wheels_ctrl"
BOTH_WHEEL_ROT_ATTR = "wheel_rotation"
BOTH_WHEEL_RATIO_ATTR = "wheel_ratio"


def get_wheel_values_and_times_sep_wheels(time_start, time_end):
    wheel_times_fr = []
    l_wheel_times = mc.keyframe(L_WHEEL_CTR + "." + WHEEL_ROT_ATTR,
                                query=True,
                                timeChange=True,
                                time=(time_start, time_end))
    r_wheel_times = mc.keyframe(R_WHEEL_CTR + "." + WHEEL_ROT_ATTR,
                                query=True,
                                timeChange=True,
                                time=(time_start, time_end))

    l_wheel_values = []
    r_wheel_values = []

    if l_wheel_times is None and r_wheel_times is None:
        print "Wheel ctrs were not keyed and their values will not be copied"
        return [], []

    if l_wheel_times:
        wheel_times_fr += l_wheel_times
    if r_wheel_times:
        wheel_times_fr += r_wheel_times

    if wheel_times_fr!=[]:
        wheel_times_fr = list(set(wheel_times_fr))
        wheel_times_fr.sort()

    for frame_num in wheel_times_fr:
        l_wheel_value = mc.getAttr(L_WHEEL_CTR + "." + WHEEL_ROT_ATTR, time=frame_num)
        l_wheel_values.append(l_wheel_value)
        r_wheel_value = mc.getAttr(R_WHEEL_CTR + "." + WHEEL_ROT_ATTR, time=frame_num)
        r_wheel_values.append(r_wheel_value)

    return [l_wheel_values,r_wheel_values], wheel_times_fr

def get_wheel_values_and_times_vis_wheels(time_start, time_end):
    wheel_times_fr = mc.keyframe(WHEELS_CTR,
                                query=True,
                                timeChange=True,
                                time=(time_start, time_end))

    ratio_values = []
    l_wheel_values = []

    if wheel_times_fr is None:
        print "Wheel ctr is not keyed. Values will not be copied"
        return [], []

    if wheel_times_fr!=[]:
        wheel_times_fr = list(set(wheel_times_fr))
        wheel_times_fr.sort()

    for frame_num in wheel_times_fr:
        l_wheel_value = mc.getAttr(WHEELS_CTR + "." + BOTH_WHEEL_ROT_ATTR, time=frame_num)
        l_wheel_values.append(l_wheel_value)
        ratio_value = mc.getAttr(WHEELS_CTR + "." + BOTH_WHEEL_RATIO_ATTR, time=frame_num)
        ratio_values.append(ratio_value)

    return [l_wheel_values,ratio_values], wheel_times_fr

def get_segment_rotations_sw(l_wheel_values, r_wheel_values):
    l_segment_rotations = []
    r_segment_rotations = []
    for i in range(len(l_wheel_values)-1):
        l_segment_rotations.append(l_wheel_values[i+1]-l_wheel_values[i])
        r_segment_rotations.append(r_wheel_values[i+1]-r_wheel_values[i])

    return l_segment_rotations, r_segment_rotations


# def get_segment_rotations_vw(l_wheel_values, ratio_values):
#     if l_wheel_values != ratio_values:
#         mc.error("Different amount of wheel values and ratios")
#         print ("ratios: %s\nvalues: %s") %(ratio_values, l_wheel_values)
#     l_segment_rotations = []
#     segment_ratios = []
#     for i in range(len(l_wheel_values)-1):
#         l_segment_rotations.append(l_wheel_values[i+1]-l_wheel_values[i])
#         segment_ratios.append(ratio_values[i])

    return l_segment_rotations, segment_ratios

def get_ratios_from_wheel_values(l_segment_rotations, r_segment_rotations):
    ratios = []
    for i in range(len(l_segment_rotations)):
        if r_segment_rotations[i]==0:
            ratio = 0
        else:
            ratio = l_segment_rotations[i]/r_segment_rotations[i]
        ratios.append(ratio)
    return ratios


def set_vis_wheel_ctr(l_values, ratios, wheel_times):
    if len(wheel_times)!=len(l_values):
        print "inconsistency between wheel times and values",
        return []
    if len(ratios)!=len(l_values)-1:
        print "inconsistency between ratios and wheel values",
        return []
    for i in range(len(wheel_times)):
        mc.currentTime(wheel_times[i])
        mc.setAttr(WHEELS_CTR+"."+BOTH_WHEEL_ROT_ATTR, l_values[i])
        if i<len(wheel_times)-1:
            mc.setAttr(WHEELS_CTR + "." + BOTH_WHEEL_RATIO_ATTR, ratios[i])
        mc.setKeyframe(WHEELS_CTR)

def set_sep_wheel_ctrs(l_values, ratios, wheel_times):
    if len(wheel_times)!=len(l_values):
        print "inconsistency between wheel times and values",
        return []
    prev_r_wheel = 0
    for i in range(len(wheel_times)):
        mc.currentTime(wheel_times[i])
        mc.setAttr(L_WHEEL_CTR+"."+WHEEL_ROT_ATTR, l_values[i])
        if i>0:
            mc.setAttr(R_WHEEL_CTR+"."+WHEEL_ROT_ATTR, (l_values[i]-l_values[i-1])*ratios[i-1]+prev_r_wheel)
            prev_r_wheel = (l_values[i]-l_values[i-1])*ratios[i-1]+prev_r_wheel
        elif i==0:
            mc.setAttr(R_WHEEL_CTR + "." + WHEEL_ROT_ATTR, 0)
        mc.setKeyframe(L_WHEEL_CTR)
        mc.setKeyframe(R_WHEEL_CTR)

def clear_visual(time_start, time_end):
    """
    Removes all keys on wheels_ctrl for specified time. For example can use it before need to place new keys
    """
    mc.cutKey(WHEELS_CTR, time=(time_start, time_end), clear=True)


def clear_separate(time_start, time_end):
    """
    Removes all keys on L_WHEEL_CTR and R_WHEEL_CTR for specified time.
    """
    mc.cutKey(L_WHEEL_CTR, time=(time_start, time_end), clear=True)
    mc.cutKey(R_WHEEL_CTR, time=(time_start, time_end), clear=True)


def separate2visual(time_start = 0, time_end = 0, overwrite=False):
    if not (mc.objExists(L_WHEEL_CTR) or mc.objExists(R_WHEEL_CTR)):
        print "You need to use the new version of the rig that has %s and %s" \
              " for animation transfer to work" %(L_WHEEL_CTR, R_WHEEL_CTR)
        return []
    if not mc.objExists(WHEELS_CTR):
        print "You need to use the new version of the rig that has %s" \
              " for animation transfer to work" %(WHEELS_CTR)
        return []

    # if no time parameters are given will use the start and end of timeline
    if time_start == 0 and time_end == 0:
        time_start = mc.playbackOptions(q=True, animationStartTime = True)
        time_end = mc.playbackOptions(q=True, animationEndTime=True)
    clear_visual(time_start, time_end)
    wheel_values, wheel_times = get_wheel_values_and_times_sep_wheels(time_start, time_end)
    l_segment_rotations, r_segment_rotations = get_segment_rotations_sw(wheel_values[0],wheel_values[1])
    ratios = get_ratios_from_wheel_values(l_segment_rotations, r_segment_rotations)
    set_vis_wheel_ctr(wheel_values[0], ratios, wheel_times)
    if overwrite:
        clear_separate()


def visual2separate(time_start = 0, time_end = 0, overwrite=False):
    if not (mc.objExists(L_WHEEL_CTR) or mc.objExists(R_WHEEL_CTR)):
        print "You need to use the version of the rig that has %s and %s" \
              " for animation transfer to work" %(L_WHEEL_CTR, R_WHEEL_CTR)
        return []
    if not mc.objExists(WHEELS_CTR):
        print "You need to use the version of the rig that has %s" \
              " for animation transfer to work" %(WHEELS_CTR),
        return []

    # if no time parameters are given will use the start and end of timeline
    if time_start == 0 and time_end == 0:
        time_start = mc.playbackOptions(q=True, animationStartTime = True)
        time_end = mc.playbackOptions(q=True, animationEndTime=True)
    clear_separate(time_start, time_end)
    wheel_values, wheel_times = get_wheel_values_and_times_vis_wheels(time_start, time_end)
    # l_segment_rotations, segment_ratios = get_segment_rotations_vw(wheel_values[0], wheel_values[1])
    # ratios = get_ratios_from_wheel_values(l_segment_rotations, r_segment_rotations)
    set_sep_wheel_ctrs(wheel_values[0], wheel_values[1], wheel_times)
    if overwrite:
        clear_visual(time_start, time_end)