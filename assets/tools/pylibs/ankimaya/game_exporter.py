

GAME_EXPORTER_PRESET = "gameExporterPreset2"

GAME_EXPORTER_PLUGIN = "gameFbxExporter"


import sys
import os
from maya import cmds
from ankimaya.robot_data import get_facial_keyframes
from ankimaya.export_error_check.error_checker_utils import add_json_node


def strip_out_bad_chars(the_string, max_ordinal=128):
    new_string = ''.join([char for char in the_string if ord(char) < max_ordinal])
    new_string = new_string.strip()
    return new_string


def load_plugin(plugin=GAME_EXPORTER_PLUGIN):
    if not cmds.pluginInfo(plugin, query=True, loaded=True):
        cmds.loadPlugin(plugin)


def get_clip_info(default_name, time_scale=1.0, include_all=False, lowercase_names=True,
                  include_face_keyframes=True):

    # By default, this function will convert clip names to lowercase to avoid potential case
    # sensitivity problems (MacOS is case-insensitive for filenames but iOS is case-sensitive)

    export_subdir = None
    clip_names_updated = False
    clip_info = []

    load_plugin()
    if cmds.objExists(GAME_EXPORTER_PRESET):
        #Export directory.
        if cmds.attributeQuery('exp', n=GAME_EXPORTER_PRESET, exists=True):
            export_subdir = cmds.getAttr(GAME_EXPORTER_PRESET + '.exp')
        # ac = array size of num clips
        if cmds.attributeQuery('ac', n=GAME_EXPORTER_PRESET, exists=True):
            anim_clips = GAME_EXPORTER_PRESET + '.ac'
            num_clips = cmds.getAttr(anim_clips, size=True)
            for i in range(num_clips):
                # Name and End are required, start is assumed 0.
                if include_all:
                    is_included = True
                else:
                    is_included = cmds.getAttr('%s[%s].eac' % (anim_clips, i))
                if is_included:
                    clip_name = cmds.getAttr('%s[%s].acn' % (anim_clips, i))
                    if clip_name:
                        try:
                            clip_name = clip_name.strip()
                        except AttributeError:
                            msg = "Invalid clip name: %s" % clip_name
                            add_json_node(node_name="Invalid clip name",
                                          fix_function="", status="error",
                                          message=msg)
                            raise ValueError("Invalid clip name: %s" % clip_name)

                        # If any clip names have unicode characters that break ASCII, then strip them out
                        clip_name_len = len(clip_name)
                        clip_name = strip_out_bad_chars(clip_name)
                        if len(clip_name) != clip_name_len:
                            cmds.setAttr('%s[%s].acn' % (anim_clips, i), clip_name, type="string")
                            clip_names_updated = True

                        if lowercase_names and clip_name != clip_name.lower():
                            clip_name = clip_name.lower()
                            cmds.setAttr('%s[%s].acn' % (anim_clips, i), clip_name, type="string")
                            clip_names_updated = True
                    if clip_name == "":
                        clip_name = None
                    clip_start = cmds.getAttr('%s[%s].acs' % (anim_clips, i))
                    clip_end = cmds.getAttr('%s[%s].ace' % (anim_clips, i))
                    if clip_name != "" and clip_start < clip_end and clip_start >= 0:
                        clip_info.append(get_clip_dict(clip_name, clip_start, clip_end, time_scale,
                                         include_face_keyframes))

    if len(clip_info) == 0 and not get_num_clips():
        # Export entire frame range if no clips defined in Game Exporter.
        # For the clip name, use scene name with stripped off .ma extension.
        scene_name = cmds.file(query=True, sceneName=True, shortName=True).split('.')[0]
        if not scene_name:
            scene_name = default_name
        scene_name = scene_name.strip()
        if lowercase_names and scene_name != scene_name.lower():
            scene_name = scene_name.lower()
        clip_start = 0  # TODO: should this be "cmds.playbackOptions(query=True, min=True)" instead?
        clip_end = cmds.playbackOptions(query=True, max=True)
        clip_info.append(get_clip_dict(scene_name, clip_start, clip_end, time_scale,
                         include_face_keyframes))

    return (export_subdir, clip_names_updated, clip_info)


def get_clip_dict(clip_name, clip_start, clip_end, time_scale=1.0, include_face_keyframes=True):
    face_keyframes = None
    if include_face_keyframes:
        try:
            face_keyframes = get_facial_keyframes(clip_start, clip_end, time_scale)
        except ValueError:
            face_keyframes = None
    clip_dict = {"clip_name"  : clip_name,
                 "clip_start" : clip_start * time_scale,
                 "clip_end"   : clip_end * time_scale,
                 "face_keyframes" : face_keyframes}
    return clip_dict


def get_num_clips():
    num_clips = None
    load_plugin()
    if cmds.objExists(GAME_EXPORTER_PRESET):
        if cmds.attributeQuery('ac', n=GAME_EXPORTER_PRESET, exists=True):
            num_clips = cmds.getAttr(GAME_EXPORTER_PRESET+'.ac', size=True)
    return num_clips


def open_json(export_path):

    # This function converts clip names to lowercase to avoid potential case sensitivity
    # problems (MacOS is case-insensitive for filenames but iOS is case-sensitive).

    scene_name = cmds.file(query=True, sceneName=True, shortName=True).split('.')[0]
    scene_name = scene_name.strip()
    scene_name = scene_name.lower()
    load_plugin()
    if cmds.objExists(GAME_EXPORTER_PRESET):
        # Not sure what this should do if multiple ones are present without
        # more user input, so just open the first one found...
        clip_name = cmds.getAttr(GAME_EXPORTER_PRESET+'.ac[0].acn')
        if clip_name:
            clip_name = clip_name.strip()
            clip_name = clip_name.lower()
        else:
            clip_name = scene_name
        export_subdir = None
        if cmds.attributeQuery('exp', n=GAME_EXPORTER_PRESET, exists=True):
            export_subdir = cmds.getAttr(GAME_EXPORTER_PRESET+'.exp')
        if export_subdir:
            json_filename = os.path.join(export_path, export_subdir, clip_name+".json")
        else:
            json_filename = os.path.join(export_path, clip_name+".json")
    else:
        json_filename = os.path.join(export_path, scene_name+".json")
    if os.path.isfile(json_filename):
        print("Attempting to open: " + json_filename)
        os.system("open " + json_filename)
    else:
        cmds.warning("File not available: %s" % json_filename)


def rename_clips_exact_match(rename_mapping):
    num_clips_updated = 0
    load_plugin()
    if cmds.objExists(GAME_EXPORTER_PRESET):
        if cmds.attributeQuery('ac', n=GAME_EXPORTER_PRESET, exists=True):
            anim_clips = GAME_EXPORTER_PRESET + '.ac'
            num_clips = cmds.getAttr(anim_clips, size=True)
            rename_from_list = rename_mapping.keys()
            for idx in range(num_clips):
                clip_name = cmds.getAttr('%s[%s].acn' % (anim_clips, idx))
                clip_name = clip_name.strip()
                if clip_name in rename_from_list:
                    rename_to = rename_mapping[clip_name]
                    if clip_name == rename_to:
                        continue
                    cmds.setAttr('%s[%s].acn' % (anim_clips, idx), rename_to, type="string")
                    print("Renamed '%s' to '%s'" % (clip_name, rename_to))
                    num_clips_updated += 1
    return num_clips_updated


def rename_clips_lowercase():
    num_clips_updated = 0
    load_plugin()
    if cmds.objExists(GAME_EXPORTER_PRESET):
        if cmds.attributeQuery('ac', n=GAME_EXPORTER_PRESET, exists=True):
            anim_clips = GAME_EXPORTER_PRESET + '.ac'
            num_clips = cmds.getAttr(anim_clips, size=True)
            for idx in range(num_clips):
                clip_name = cmds.getAttr('%s[%s].acn' % (anim_clips, idx))
                clip_name = clip_name.strip()
                lowercase_name = clip_name.lower()
                if clip_name != lowercase_name:
                    cmds.setAttr('%s[%s].acn' % (anim_clips, idx), lowercase_name, type="string")
                    print("Renamed '%s' to '%s'" % (clip_name, lowercase_name))
                    num_clips_updated += 1
    return num_clips_updated


def rename_clips(rename_from, rename_to):
    if not rename_from:
        raise ValueError("Provide a valid string to rename from")
    if not rename_to:
        raise ValueError("Provide a valid string to rename to")
    num_clips_updated = 0
    if rename_from == rename_to:
        return num_clips_updated
    load_plugin()
    if cmds.objExists(GAME_EXPORTER_PRESET):
        if cmds.attributeQuery('ac', n=GAME_EXPORTER_PRESET, exists=True):
            anim_clips = GAME_EXPORTER_PRESET + '.ac'
            num_clips = cmds.getAttr(anim_clips, size=True)
            for idx in range(num_clips):
                clip_name = cmds.getAttr('%s[%s].acn' % (anim_clips, idx))
                clip_name = clip_name.strip()
                if rename_from in clip_name:
                    old_clip_name = clip_name
                    clip_name = clip_name.replace(rename_from, rename_to)
                    cmds.setAttr('%s[%s].acn' % (anim_clips, idx), clip_name, type="string")
                    print("Renamed '%s' to '%s'" % (old_clip_name, clip_name))
                    num_clips_updated += 1
    return num_clips_updated


def add_anim_clip(clip_name, start_frame, end_frame, clip_num=None):
    """
    Create new animation clip with specified parameters, unless it already exists
    """
    if clip_num is None:
        clip_num = cmds.getAttr(GAME_EXPORTER_PRESET + '.ac', size=True)
    if cmds.getAttr("%s.ac[%s].acn" % (GAME_EXPORTER_PRESET, clip_num)) == clip_name:
        msg = "Invalid clip name: %s" % clip_name
        add_json_node(node_name="Invalid clip name",
                      fix_function="", status="error",
                      message=msg)
        print("%s already exists at clip_num %s" % (clip_name, clip_num))
        return
    cmds.setAttr("%s.ac[%s].acn" % (GAME_EXPORTER_PRESET, clip_num), clip_name, type="string")
    cmds.setAttr("%s.ac[%s].acs" % (GAME_EXPORTER_PRESET, clip_num), start_frame)
    cmds.setAttr("%s.ac[%s].ace" % (GAME_EXPORTER_PRESET, clip_num), end_frame)
    print("Created '%s' animation clip (frame range = %s to %s)"
          % (clip_name, start_frame, end_frame)),


