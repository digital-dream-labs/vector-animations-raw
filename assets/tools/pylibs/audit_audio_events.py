#!/usr/bin/env python
"""
This script can be used to audit what audio events are used in
animations and then present that data in three forms:
    (1) a flat list of all used audio events
    (2) a mapping of audio events to the animations that use them
    (3) a mapping of animations of the audio events that they use
Performance was not a concern when this script was first written.
"""

SVN_REPO_WITH_TAR_FILES  = "victor-animation-assets"

KEYFRAME_TYPE_ATTR = "Name"
AUDIO_KEYFRAME_TYPE = "RobotAudioKeyFrame"
AUDIO_EVENT_NAMES_ATTR = "audioName"
AUDIO_EVENT_GROUPS_ATTR = "eventGroups"
AUDIO_EVENT_IDS_ATTR = "eventIds"

AUDIO_EVENT_FLAG = "-audio_event"
MISSING_FLAG_ARG_MSG  = "When the %s flag is provided, it must be immediately "
MISSING_FLAG_ARG_MSG += "followed by the %s name"


import sys
import os
import pprint
import tempfile
import tarfile
import json
import xml.etree.ElementTree as ET

from audit_anim_clips import unpack_tarball


# Animators typically have tar files exported to the directory defined by TAR_FILE_DIR1, but Ben
# uses the directory defined by TAR_FILE_DIR2 instead, so we use the second in main() if the first
# doesn't exist.
HOME = os.getenv("HOME")
TAR_FILE_DIR1 = os.path.join(HOME, 'workspace', SVN_REPO_WITH_TAR_FILES, 'animations')
TAR_FILE_DIR2 = os.path.join(HOME, 'Documents', 'VictorSVN', SVN_REPO_WITH_TAR_FILES, 'animations')


def get_tar_files(root_dir):
    all_tar_files = []
    for dir_name, subdir_list, file_list in os.walk(root_dir):
        tar_files = [x for x in file_list if x.endswith(".tar")]
        all_tar_files.extend([os.path.join(dir_name, x) for x in tar_files])
    return all_tar_files


def fill_file_dict(file_list):
    file_dict = {}
    for file in file_list:
        file_name = os.path.basename(file)
        if file_name in file_dict:
            print("%sCONFLICT: Found more than one '%s' file: '%s' and '%s'"
                  % (os.linesep, file_name, file, file_dict[file_name]))
            file_dict[file_name].append(file)
        else:
            file_dict[file_name] = [file]
    return file_dict


def get_audio_events_in_soundbanks_info_xml_file(xml_file, sound_banks_attr='SoundBanks',
                                                 included_events_attr='IncludedEvents',
                                                 audio_event_name_attr='Name'):
    all_audio_events = []

    if not xml_file or not os.path.isfile(xml_file):
        raise ValueError("Invalid XML file provided: %s" % xml_file)
    fh = open(xml_file, 'r')
    xml_data = fh.read()
    fh.close()
    xml_data = xml_data.strip()

    root = ET.fromstring(xml_data)
    for sound_banks in root.iter(sound_banks_attr):
        for all_events in sound_banks.iter(included_events_attr):
            for event in all_events:
                event_name = event.get(audio_event_name_attr)
                all_audio_events.append(event_name)

    return all_audio_events


def get_audio_event_of_interest():
    audio_event = None
    if AUDIO_EVENT_FLAG in sys.argv:
        idx = sys.argv.index(AUDIO_EVENT_FLAG)
        try:
            audio_event = sys.argv[idx+1]
        except IndexError:
            raise ValueError(MISSING_FLAG_ARG_MSG % (AUDIO_EVENT_FLAG, "audio event"))
    return audio_event


def get_audio_event_usage(tar_file_dict, audio_event):
    events_by_anim_clip = {}
    anim_clips_by_event = {}
    for file_name, file_paths in tar_file_dict.items():
        file_path = file_paths[0]
        unpacked_files = unpack_tarball(file_path)
        for json_file in unpacked_files:
            events_by_anim_clip_in_anim, anim_clips_by_event_in_anim = get_audio_event_usage_in_anim(json_file)
            events_by_anim_clip.update(events_by_anim_clip_in_anim)
            for event, anim_clips in anim_clips_by_event_in_anim.items():
                if event not in anim_clips_by_event:
                    anim_clips_by_event[event] = []
                anim_clips_by_event[event].extend(anim_clips)
    return (events_by_anim_clip, anim_clips_by_event)


def get_audio_event_usage_in_anim(json_file):
    events_by_anim_clip = {}
    anim_clips_by_event = {}
    fh = open(json_file, 'r')
    try:
        contents = json.load(fh)
    except StandardError, e:
        print("Failed to read %s file because: %s" % (json_file, e))
        return (events_by_anim_clip, anim_clips_by_event)
    finally:
        fh.close()
    for anim_clip, keyframes in contents.items():
        anim_clip = str(anim_clip)
        if anim_clip not in events_by_anim_clip:
            events_by_anim_clip[anim_clip] = []
        #print("num keyframes = %s" % len(keyframes))
        for keyframe in keyframes:
            try:
                keyframe_type = str(keyframe[KEYFRAME_TYPE_ATTR])
            except KeyError:
                continue
            if keyframe_type == AUDIO_KEYFRAME_TYPE:
                #print(keyframe)
                try:
                    audio_events = keyframe[AUDIO_EVENT_NAMES_ATTR]
                except KeyError:
                    audio_events = []
                    try:
                        event_groups = keyframe[AUDIO_EVENT_GROUPS_ATTR]
                    except KeyError:
                        event_groups = []
                    for event_group in event_groups:
                        try:
                            audio_events.extend(event_group[AUDIO_EVENT_NAMES_ATTR])
                        except KeyError:
                            audio_events.extend(event_group[AUDIO_EVENT_IDS_ATTR])
                for audio_event in audio_events:
                    audio_event = str(audio_event)
                    if audio_event not in anim_clips_by_event:
                        anim_clips_by_event[audio_event] = []
                    if anim_clip not in anim_clips_by_event[audio_event]:
                        anim_clips_by_event[audio_event].append(anim_clip)
                    if audio_event not in events_by_anim_clip[anim_clip]:
                        events_by_anim_clip[anim_clip].append(audio_event)
    return (events_by_anim_clip, anim_clips_by_event)


def test_get_audio_events_in_soundbanks_info_xml_file(xml_file="SoundbanksInfo.xml"):
    audio_events = get_audio_events_in_soundbanks_info_xml_file(xml_file)
    print("There are %s audio events in the %s file" % (len(audio_events), xml_file))
    print(audio_events)


def main():
    audio_event = get_audio_event_of_interest()

    if os.path.isdir(TAR_FILE_DIR1):
        tar_file_dir = TAR_FILE_DIR1
    else:
        tar_file_dir = TAR_FILE_DIR2
    tar_files = get_tar_files(tar_file_dir)
    tar_file_dict = fill_file_dict(tar_files)
    #pprint.pprint(tar_file_dict)

    events_by_anim_clip, anim_clips_by_event = get_audio_event_usage(tar_file_dict, audio_event)
    all_audio_events_in_use = anim_clips_by_event.keys()
    all_audio_events_in_use.sort()
    print("---------------------------------------------------------")
    print("all audio events in use = %s" % len(all_audio_events_in_use))
    pprint.pprint(all_audio_events_in_use)
    print("---------------------------------------------------------")
    print("events by anim clip = %s" % len(events_by_anim_clip))
    pprint.pprint(events_by_anim_clip)
    print("---------------------------------------------------------")
    print("anim clips by event = %s" % len(anim_clips_by_event))
    pprint.pprint(anim_clips_by_event)
    print("---------------------------------------------------------")


if __name__ == "__main__":
    main()


