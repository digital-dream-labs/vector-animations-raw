#!/usr/bin/env python

MOODS = ["Default", "LowStim", "MedStim", "HighStim", "Frustrated"]
DEFAULT_WEIGHT = "1.0"
DEFAULT_COOLDOWN_TIME = "0.0"

ANIM_TRIGGER_MAP_FILES = ['$HOME/workspace/victor/resources/assets/cladToFileMaps/AnimationTriggerMap.json']

ANIM_GROUP_NAME_KEY = "AnimName"

CRITICAL_ANIM_GROUP_DIRS = ["engine"]

# The following attributes are also used in the Animation Group editor UI and in
# the .json files that are written out by these tools.  If any of these attributes
# are ever changed, they also need to be changed in AddAnimWidget.initUI() in
# ag_editor.py and in the corresponding UI layout file (ag_editor.ui).

NAME_ATTR = "Name"
WEIGHT_ATTR = "Weight"
COOLDOWN_ATTR = "CooldownTime_Sec"
MOOD_ATTR = "Mood"
USE_HEAD_ANGLE_ATTR = "UseHeadAngle"
HEAD_ANGLE_MIN_ATTR = "HeadAngleMin_Deg"
HEAD_ANGLE_MAX_ATTR = "HeadAngleMax_Deg"
HEAD_ANGLE_ATTRS_SORTED = [USE_HEAD_ANGLE_ATTR, HEAD_ANGLE_MIN_ATTR, HEAD_ANGLE_MAX_ATTR]
ALL_ATTRS_SORTED = [NAME_ATTR, WEIGHT_ATTR, COOLDOWN_ATTR, MOOD_ATTR] + HEAD_ANGLE_ATTRS_SORTED
NUMERICAL_ATTRS = [WEIGHT_ATTR, COOLDOWN_ATTR, HEAD_ANGLE_MIN_ATTR, HEAD_ANGLE_MAX_ATTR]
JSON_TOP_KEY = "Animations"


import sys
import os
import re
import json
import stat
import pprint
from collections import OrderedDict
from ankiutils import mail_tools, svn_tools


def get_anim_groups(anim_group_dir, strip_ext=True, return_full_paths=False):
    """
    Given a directory path, eg. "~/workspace/cozmo-assets/animationGroups",
    this function will recursively search that directory and return a list
    of all animation groups (.json files) that it finds.
    """
    #print("Checking %s..." % anim_group_dir)
    dir_contents = os.listdir(anim_group_dir)
    anim_groups = []
    for anim_group in dir_contents:
        if anim_group.startswith(os.extsep):
            continue
        full_path = os.path.join(anim_group_dir, anim_group)
        if os.path.isdir(full_path):
            anim_groups.extend(get_anim_groups(full_path, False, return_full_paths))
        else:
            if return_full_paths:
                anim_groups.append(full_path)
            else:
                anim_groups.append(anim_group)
    if strip_ext and not return_full_paths:
        anim_groups = map(lambda x: os.path.splitext(x)[0], anim_groups)
    return anim_groups


def get_clips_in_anim_group(json_file):
    with open(json_file, 'r') as fh:
        json_data = fh.read()
        json_data = re.sub(r'//.*\n', os.linesep, json_data) # remove C-style comments
        json_data = re.sub(r'#.*\n', os.linesep, json_data) # remove Python-style comments
        anim_group = json.loads(json_data)
    anim_clips = anim_group[JSON_TOP_KEY]
    anim_clips = [x[NAME_ATTR] for x in anim_clips]
    anim_group_name = os.path.basename(json_file)
    anim_group_name = os.path.splitext(anim_group_name)[0]
    return (anim_group_name, anim_clips)


def rename_anim_clips(name_mapping, json_file, sort_order=ALL_ATTRS_SORTED):
    num_anim_clips_renamed = 0

    with open(json_file, 'r') as fh:
        json_data = fh.read()
        json_data = re.sub(r'//.*\n', os.linesep, json_data) # remove C-style comments
        json_data = re.sub(r'#.*\n', os.linesep, json_data) # remove Python-style comments
        anim_group_data = json.loads(json_data)

    rename_from_list = name_mapping.keys()
    num_anim_clips = len(anim_group_data[JSON_TOP_KEY])
    for idx in range(num_anim_clips):
        anim_clip = anim_group_data[JSON_TOP_KEY][idx]
        anim_clip_name = anim_clip[NAME_ATTR]
        #print("Checking '%s' to see if it should be renamed..." % anim_clip_name)
        if anim_clip_name in rename_from_list:
            rename_to = name_mapping[anim_clip_name]
            if anim_clip_name == rename_to:
                continue
            anim_group_data[JSON_TOP_KEY][idx][NAME_ATTR] = rename_to
            print("Renamed '%s' to '%s'" % (anim_clip_name, rename_to))
            num_anim_clips_renamed += 1

    if num_anim_clips_renamed > 0:
        ordered = [OrderedDict(sorted(item.iteritems(), key=lambda (k, v): sort_order.index(k)))
                                      for item in anim_group_data[JSON_TOP_KEY]]
        anim_group = {JSON_TOP_KEY : ordered}
        try:
            json_file_stat = os.stat(json_file)
            os.chmod(json_file, json_file_stat.st_mode | stat.S_IWUSR)
            with open(json_file, 'w') as fh:
                json.dump(anim_group, fh, indent=2, separators=(',', ': '))
        except (OSError, IOError), e:
            msg = "Failed to write '%s' file because: %s" % (json_file, e)
            print(msg)
        else:
            print("Wrote updates to %s file" % json_file)

    return num_anim_clips_renamed


def rename_anim_group(rename_mapping, json_file, files_to_commit,
                      trigger_map_files=ANIM_TRIGGER_MAP_FILES):
    file_name = os.path.basename(json_file)
    file_name = os.path.splitext(file_name)[0]
    new_name = rename_mapping[file_name]
    try:
        svn_tools.rename_svn_file(json_file, new_name)
    except RuntimeError, e:
        print("Failed to rename '%s' to '%s' because: %s" % (file_name, new_name, e))
    else:
        for trigger_map_file in trigger_map_files:
            trigger_map_file = os.path.expandvars(trigger_map_file)
            try:
                update_anim_group_reference(trigger_map_file, rename_mapping)
            except BaseException, e:
                print("ERROR: %s" % e)
        print("Successfully renamed '%s' to '%s'" % (file_name, new_name))


def update_anim_group_reference(trigger_map_file, rename_mapping,
                                anim_group_name_key=ANIM_GROUP_NAME_KEY):
    print("Renaming animation groups in %s using: %s" % (trigger_map_file, rename_mapping))
    fh = open(trigger_map_file, 'r')
    orig_contents = fh.read()
    fh.close()
    new_contents = []
    for one_line in orig_contents.split(os.linesep):
        if anim_group_name_key in one_line:
            for before, after in rename_mapping.iteritems():
                if before in one_line:
                    one_line = one_line.replace(before, after)
        new_contents.append(one_line)
    new_contents = os.linesep.join(new_contents)
    if new_contents != orig_contents:
        fh = open(trigger_map_file, 'w')
        fh.write(new_contents)
        fh.close()
        print("Updated %s" % trigger_map_file)


def alert_anim_group_updated(anim_group, file_path, file_ver, cc_emails=[], user_name_mapping={}):
    # When certain animation groups are updated an alert/notification should be sent.
    dir_name = os.path.basename(os.path.dirname(file_path))
    if dir_name in CRITICAL_ANIM_GROUP_DIRS:
        subject = "animation group update (%s)" % anim_group
        msgs = ["The '%s' animation group has been updated." % anim_group, '',
                "Version %s of %s was just committed." % (file_ver, file_path)]
        if file_ver:
            diff_lines = svn_tools.get_svn_diff(file_path, file_ver)
            if diff_lines:
                msgs.extend(['', ''])
                msgs.extend(diff_lines)
        try:
            mail_tools.send_msgs(msgs, subject, cc_emails=cc_emails,
                                 user_name_mapping=user_name_mapping)
        except ValueError, e:
            print(e)


def test_rename_anim_clips():
    name_mapping = {'foo':'bar', 'anim_speedTap_winGame_intensity02_02':'anim_foobar'}
    json_file = sys.argv[1]
    rename_anim_clips(name_mapping, json_file)


if __name__ == "__main__":
    test_rename_anim_clips()


