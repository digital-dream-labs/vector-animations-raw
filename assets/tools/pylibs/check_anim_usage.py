#!/usr/bin/env python
"""
By default, this script will report any animations that are NOT
in use in at least one animation group. Based on that lack of
usage, this script reports what tar files can be safely removed.

When the "-groups" argument is provided, this script will report
any animation groups that are NOT in use in for at least one clad
event trigger.

In addition to running this script, we should also run:

$ grep -r -e "ag_" -e "anim_" engine/aiComponent/behaviorComponent/ test/engine/behaviorComponent/ resources/config/engine/behaviorComponent/ clad/src/clad/types/behaviorComponent/ animProcess/ cannedAnimLib/ engine/

to search for animations (since some behaviors now hard-code
animation names).
"""

SVN_REPO_WITH_ANIM_DATA = "victor-animation-assets"
GIT_REPO_WITH_TRIGGER_MAP = "victor"

#BRANCH_NAME = "release_1.5.0"
BRANCH_NAME = None

#ANIM_GROUPS_TO_IGNORE_FILE = "/tmp/unused_anim_groups.txt"
ANIM_GROUPS_TO_IGNORE_FILE = None

SDK_DO_NOT_DELETE = [ "anim_eyepose_furious",
                      "anim_turn_left_01",
                      "anim_blackjack_victorwin_01",
                      "anim_pounce_success_02",
                      "anim_feedback_shutup_01",
                      "anim_knowledgegraph_success_01",
                      "anim_wakeword_groggyeyes_listenloop_01",
                      "anim_fistbump_success_01",
                      "anim_reacttoface_unidentified_01",
                      "anim_rtpickup_loop_10",
                      "anim_volume_stage_05" ]

# The following animations as well as several "anim_dancebeat" animations are hard-coded
# somewhere and thus cannot be removed (even if they are not used in animation groups)
HARD_CODED_ANIMS = [ "anim_blackjack_deal_01",
                     "anim_blackjack_swipe_01",
                     "anim_onboarding_cube_psychic_01",
                     "anim_power_offon_01",
                     "anim_power_onoff_01",
                     "anim_qa_head_updown",
                     "anim_qa_lift_updown",
                     "anim_spinner_tap_01",
                     "anim_triple_backup",
                     "anim_weather_cloud_01",
                     "anim_weather_cold_01",
                     "anim_weather_rain_01",
                     "anim_weather_snow_01",
                     "anim_weather_stars_01",
                     "anim_weather_sunny_01",
                     "anim_weather_thunderstorm_01",
                     "anim_weather_windy_01" ]

HARD_CODED_ANIM_FILES = [ "anim_dancebeat_01.tar",
                          "anim_dancebeat_02.tar",
                          "anim_dancebeat_getin_01.tar",
                          "anim_dancebeat_getout_01.tar",
                          "anim_weather_cloud_01.tar",
                          "anim_weather_snow_01.tar",
                          "anim_weather_rain_01.tar",
                          "anim_weather_sunny_01.tar",
                          "anim_weather_stars_01.tar",
                          "anim_weather_cold_01.tar",
                          "anim_weather_windy_01.tar",
                          "anim_weather_thunderstorm_01.tar",
                          "anim_blackjack_gameplay_01.tar",
                          "anim_spinner_tap_01.tar",
                          "anim_onboarding_cube_reacttocube.tar",
                          "anim_power_offon_01.tar",
                          "anim_power_onoff_01.tar" ]


import sys
import os
import json
from anim_groups import get_anim_groups, get_clips_in_anim_group
from audit_anim_clips import unpack_tarball
from audit_audio_events import get_audio_event_usage_in_anim


USER_HOME = os.getenv("HOME")

if BRANCH_NAME:
    ASSETS_DIR = "%s/workspace/%s-branches/%s" % (USER_HOME, SVN_REPO_WITH_ANIM_DATA, BRANCH_NAME)
else:
    ASSETS_DIR = "%s/workspace/%s" % (USER_HOME, SVN_REPO_WITH_ANIM_DATA)

MAPPING_JSON_FILE = "%s/workspace/%s/resources/assets/cladToFileMaps/AnimationTriggerMap.json" % (USER_HOME, GIT_REPO_WITH_TRIGGER_MAP)

#DEPRECATED_CLAD_EVENT_PREFIX = "DEPRECATED_"
DEPRECATED_CLAD_EVENT_PREFIX = None

ANIM_GROUP_DIR = os.path.join(ASSETS_DIR, "animationGroups")

ANIMS_DIR = os.path.join(ASSETS_DIR, "animations")

CHECK_GROUP_USAGE_FLAG = "-groups"

EVENT_KEY = "CladEvent"
ANIM_GROUP_KEY = "AnimName"


def get_clad_to_anim_group_mapping(mapping_file=MAPPING_JSON_FILE):
    fh = open(mapping_file)
    mappings = json.load(fh)
    fh.close()
    print("There are %s animation groups in the mapping" % len(mappings))
    #print(mappings)
    return mappings


def report_missing_anim_groups_in_mapping(anim_groups, deprecated_prefix=DEPRECATED_CLAD_EVENT_PREFIX):
    mappings = get_clad_to_anim_group_mapping()
    if deprecated_prefix:
        used_anim_groups = [mapping[ANIM_GROUP_KEY] for mapping in mappings
                            if not mapping[EVENT_KEY].startswith(deprecated_prefix)]
        used_anim_groups = list(set(used_anim_groups))
        print("There are %s undeprecated animation groups in the mapping" % len(used_anim_groups))
    else:
        used_anim_groups = [mapping[ANIM_GROUP_KEY] for mapping in mappings]
    print("There are %s animation groups in the mapping" % len(used_anim_groups))
    used_anim_groups = list(set(used_anim_groups))
    print("There are %s unique animation groups in the mapping" % len(used_anim_groups))
    used_anim_groups.sort()
    for anim_group in anim_groups:
        if anim_group not in used_anim_groups:
            print("%s is not used in the mapping" % anim_group)
    for used_anim_group in used_anim_groups:
        if used_anim_group not in anim_groups:
            print("%s is used in the mapping but the json file appears to be missing" % used_anim_group)


def report_unused_anims_in_anim_groups(anims, anim_groups):
    used_anims = []
    for anim_group in anim_groups:
        try:
            anim_group_name, anim_clips = get_clips_in_anim_group(anim_group)
        except ValueError:
            print("WARNING: Unable to parse %s" % anim_group)
            continue
        used_anims.extend(anim_clips)
    all_anims = {}
    tar_file_usage_counter = {}
    anim_to_tar_file_mapping = {}
    tar_file_to_anim_mapping = {}
    for anim_file in anims:
        if anim_file not in tar_file_usage_counter:
            tar_file_usage_counter[anim_file] = 0
        if anim_file not in tar_file_to_anim_mapping:
            tar_file_to_anim_mapping[anim_file] = []
        if os.path.splitext(anim_file)[1] == ".tar":
            unpacked_files = unpack_tarball(anim_file)
        else:
            unpacked_files = [anim_file]
        for json_file in unpacked_files:
            anim_name = os.path.splitext(os.path.basename(json_file))[0]
            all_anims[anim_name] = json_file
            tar_file_usage_counter[anim_file] += 1
            tar_file_to_anim_mapping[anim_file].append(anim_name)
            if anim_name in anim_to_tar_file_mapping:
                print("ALERT: Multiple definitions for the '%s' animation (in %s and %s)"
                      % (anim_name, anim_to_tar_file_mapping[anim_name], anim_file))
            else:
                anim_to_tar_file_mapping[anim_name] = anim_file
    for anim in all_anims.keys():
        if anim in SDK_DO_NOT_DELETE:
            print("%s is in the do-not-delete list" % anim)
        elif anim in HARD_CODED_ANIMS:
            print("%s is hard-coded somewhere" % anim)
        elif anim not in used_anims:
            print("%s is not used in any animation groups" % anim)
            tar_file = anim_to_tar_file_mapping[anim]
            tar_file_usage_counter[tar_file] -= 1
        else:
            try:
                audio_events = get_audio_event_usage_in_anim(all_anims[anim])[0][anim]
            except KeyError:
                audio_events = []
            print("%s is used in at least one animation group and it triggers %s" % (anim, audio_events))
        #print(get_audio_event_usage_in_anim(all_anims[anim])[0][anim])
    for tar_file, usage_count in tar_file_usage_counter.items():
        if usage_count < 1 and os.path.basename(tar_file) not in HARD_CODED_ANIM_FILES:
            print("%s can be safely removed (for animations: %s)"
                  % (tar_file, tar_file_to_anim_mapping[tar_file]))
    for used_anim in used_anims:
        if used_anim not in all_anims.keys():
            print("%s is used in at least one animation group but that animation appears to be missing" % used_anim)


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


def get_anim_groups_to_ignore(file_with_list=ANIM_GROUPS_TO_IGNORE_FILE):
    if file_with_list and os.path.isfile(file_with_list):
        fh = open(file_with_list, 'r')
        anim_groups_to_ignore = map(lambda x: x.rstrip(os.linesep), fh.readlines())
        print("There are %s animation groups to ignore (based on %s)" % (len(anim_groups_to_ignore), file_with_list))
        #print(anim_groups_to_ignore)
    else:
        anim_groups_to_ignore = []
    return anim_groups_to_ignore


def main(args):
    check_groups = CHECK_GROUP_USAGE_FLAG in args
    if check_groups:
        strip_ext = True
        return_full_paths = False
    else:
        strip_ext = False
        return_full_paths = True
    anim_groups = get_anim_groups(ANIM_GROUP_DIR, strip_ext, return_full_paths)
    print("There are %s total animation groups" % len(anim_groups))
    #print(anim_groups)
    if check_groups:
        report_missing_anim_groups_in_mapping(anim_groups)
    else:
        anims = get_animations(ANIMS_DIR, return_full_paths=True)
        anim_groups_to_ignore = get_anim_groups_to_ignore()
        naked_anim_groups = get_anim_groups(ANIM_GROUP_DIR, True, False)
        if anim_groups_to_ignore:
            for anim_group_to_ignore in anim_groups_to_ignore:
                try:
                    idx = naked_anim_groups.index(anim_group_to_ignore)
                except ValueError:
                    pass
                else:
                    print("Ignoring animation group: %s" % anim_groups[idx])
                    anim_groups[idx] = None
            while None in anim_groups:
                anim_groups.remove(None)
            print("There are %s animation groups after ignoring some" % len(anim_groups))
            #print(anim_groups)
        report_unused_anims_in_anim_groups(anims, anim_groups)


if __name__ == "__main__":
    main(sys.argv[1:])


