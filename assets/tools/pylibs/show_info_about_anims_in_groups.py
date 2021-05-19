#!/usr/bin/env python
"""
Given a list of animation groups, this script will parse that list
and display info about the animations in each of those animation
groups, querying Shotgun for some of that info.
"""

SVN_REPO_WITH_ANIM_DATA = "victor-animation-assets"
GIT_REPO_WITH_TRIGGER_MAP = "victor"


import sys
import os
import json
from anim_groups import get_anim_groups, get_clips_in_anim_group
from ankishotgun.anim_data import ShotgunAssets, SG_PROJECTS


USER_HOME = os.getenv("HOME")

ASSETS_DIR = "%s/workspace/%s" % (USER_HOME, SVN_REPO_WITH_ANIM_DATA)

MAPPING_JSON_FILE = "%s/workspace/%s/resources/assets/animationGroupMaps/AnimationTriggerMap.json" % (USER_HOME, GIT_REPO_WITH_TRIGGER_MAP)

ANIM_GROUP_DIR = os.path.join(ASSETS_DIR, "animationGroups")

ANIMS_DIR = os.path.join(ASSETS_DIR, "animations")

MAPPING_DATA_KEY = "Pairs"
EVENT_KEY = "CladEvent"
ANIM_GROUP_KEY = "AnimName"


def report_missing_anim_groups_in_mapping(anim_groups, mapping_file=MAPPING_JSON_FILE):
    fh = open(mapping_file)
    mapping_data = json.load(fh)
    fh.close()
    #print(mapping_data)
    mappings = mapping_data[MAPPING_DATA_KEY]
    used_anim_groups = [mapping[ANIM_GROUP_KEY] for mapping in mappings]
    used_anim_groups.sort()
    for anim_group in anim_groups:
        if anim_group not in used_anim_groups:
            print("%s is not used in the mapping" % anim_group)
    for used_anim_group in used_anim_groups:
        if used_anim_group not in anim_groups:
            print("%s is used in the mapping but the json file appears to be missing" % used_anim_group)


def get_animations(anims_dir, return_full_paths=False):
    dir_contents = os.listdir(anims_dir)
    anims = []
    for anim in dir_contents:
        if anim.startswith(os.extsep):
            continue
        full_path = os.path.join(anims_dir, anim)
        if os.path.isdir(full_path):
            anims.extend(get_animations(full_path, return_full_paths))
        else:
            if return_full_paths:
                anims.append(full_path)
            else:
                anims.append(anim)
    return anims


def main(args):
    anim_group_list_file = args[0]
    fh = open(anim_group_list_file, 'r')
    anim_groups_of_interest = fh.read().split(os.linesep)
    fh.close()

    sg_assets = ShotgunAssets()
    all_assets = sg_assets.get_all_assets(SG_PROJECTS)

    anim_groups = get_anim_groups(ANIM_GROUP_DIR, strip_ext=False, return_full_paths=True)
    anim_groups.sort()
    for anim_group in anim_groups:
        try:
            anim_group_name, anim_clips = get_clips_in_anim_group(anim_group)
        except ValueError:
            print("WARNING: Unable to parse %s" % anim_group)
            continue
        if anim_group_name not in anim_groups_of_interest:
            continue
        #print("%s uses these animations: %s" % (anim_group_name, anim_clips))
        for anim in anim_clips:
            for proj in SG_PROJECTS:
                for asset in all_assets[proj]:
                    if anim == asset[sg_assets.asset_name_attr]:
                        print("%s from %s is %s in %s" % (anim, anim_group_name, asset[sg_assets.asset_type_attr], proj))
                        break
                else:
                    print("%s is not available in %s" % (anim, proj))
        print("-"*40)


if __name__ == "__main__":
    main(sys.argv[1:])


