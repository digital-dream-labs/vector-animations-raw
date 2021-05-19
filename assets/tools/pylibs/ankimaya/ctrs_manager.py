# To get information about controllers and their attributes

import maya.cmds as mc

GAME_EXPORTER_PRESET = "gameExporterPreset2"
DATA_NODE = "x:data_node"
HEAD_CTR = "x:mech_head_ctrl"
EVENT_CTR = "x:event_ctrl"

def get_all_connected_ctrs():
    if len(mc.ls(DATA_NODE)) == 0:
        print("WARNING: no '%s' node available" % DATA_NODE)
        return []
    data_attributes = mc.listAttr(DATA_NODE, userDefined=True, k=True)
    connected_ctrs = mc.listConnections(DATA_NODE, destination=True,
                                        skipConversionNodes=True, type="transform")
    if connected_ctrs is None:
        connected_ctrs = []
    for attr in data_attributes:
        driver = mc.setDrivenKeyframe(DATA_NODE + "." + attr, driver=1, q=1)
        if driver[0] == "No drivers.":
            continue
        ctr_name = driver[0].split(".")[0]
        connected_ctrs.append(ctr_name)
    return list(set(connected_ctrs))


def get_keyed_ctrs(skip_muted=True):
    all_ctrs = get_all_connected_ctrs()
    ctrs = []
    for ctr in all_ctrs:
        if mc.keyframe(ctr, query=True, keyframeCount=True) > 0:
            if skip_muted:
                if is_ctr_muted(ctr):
                    continue
            ctrs.append(ctr)
    return ctrs


def get_keyed_attrs(skip_muted=True):
    all_attrs = []
    all_ctrs = get_all_connected_ctrs()
    for ctr in all_ctrs:
        attrs = mc.listAttr(ctr, k=True)
        if attrs is not None:
            for attr in attrs:
                keyed_frames = mc.keyframe(ctr + "." + attr, q=True, tc=True)
                if keyed_frames:
                    if not mc.mute(ctr + "." + attr, q=True):
                        all_attrs.append(ctr + "." + attr)
    return all_attrs


def is_ctr_muted(ctr):
    """
    Returns True if controller has muted attributes or has no attributes.
    """
    try:
        ctr_attrs = mc.listAttr(ctr, k=True)
    except ValueError:
        ctr_attrs = None
    if ctr_attrs is None:
        return True
    for attr in ctr_attrs:
        if mc.keyframe(ctr + "." + attr, query=True, timeChange=True):
            if mc.mute(ctr + "." + attr, q=True):
                return True
    return False

def get_muted_attrs(ctr):
    """
    Returns True if controller has muted attributes or has no attributes.
    """
    muted_attrs = []
    try:
        ctr_attrs = mc.listAttr(ctr, k=True)
    except ValueError:
        ctr_attrs = None
    if ctr_attrs is None:
        return []
    for attr in ctr_attrs:
        if mc.keyframe(ctr + "." + attr, query=True, timeChange=True):
            if mc.mute(ctr + "." + attr, q=True):
                muted_attrs.append(ctr + "." + attr)
    return muted_attrs

