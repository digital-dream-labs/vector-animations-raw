#!/usr/bin/env python

# 33ms per frame multiplied by the max number of frames
MAX_END_TIME = (33 * 990)

KEYFRAME_TYPE_KEY = "Name"
TRIGGER_TIME_KEY = "triggerTime_ms"
DURATION_TIME_KEY = "durationTime_ms"

SHOW_LONGEST_TRACKS_FLAG = "-longest_tracks"


import sys
import os
import json
import glob


def get_anim_end_by_type(anim_data):
    anim_end_by_type = {}
    for anim_name, keyframes in anim_data.items():
        for keyframe in keyframes:
            type = keyframe[KEYFRAME_TYPE_KEY]
            trigger_time = keyframe[TRIGGER_TIME_KEY]
            try:
                duration_time = keyframe[DURATION_TIME_KEY]
            except KeyError:
                duration_time = 0
            end_time = trigger_time + duration_time
            if type in anim_end_by_type:
                if end_time > anim_end_by_type[type]:
                    anim_end_by_type[type] = end_time
            else:
                anim_end_by_type[type] = end_time
    #print(anim_end_by_type)
    return anim_end_by_type


def get_clip_length(keyframe_list):
    clip_length = 0
    for keyframe in keyframe_list:
        try:
            trigger_time_ms = keyframe[TRIGGER_TIME_KEY]
        except KeyError:
            continue
        try:
            duration_time_ms = keyframe[DURATION_TIME_KEY]
        except KeyError:
            duration_time_ms = 0
        keyframe_length_ms = trigger_time_ms + duration_time_ms
        clip_length = max(clip_length, keyframe_length_ms)
    return clip_length


def main(anim_files, max_end_time=None):
    msg = "The last %s keyframe in %s ends at %s ms"

    show_longest_tracks = False
    while SHOW_LONGEST_TRACKS_FLAG in anim_files:
        show_longest_tracks = True
        anim_files.remove(SHOW_LONGEST_TRACKS_FLAG)

    for anim_file in anim_files:
        if not anim_file.endswith(".json"):
            continue
        #print(anim_file)
        fh = open(anim_file, 'r')
        anim_data = json.load(fh)
        fh.close()
        anim_end_by_type = get_anim_end_by_type(anim_data)

        last_end_time = None
        longest_tracks = []
        if show_longest_tracks:
            end_times = anim_end_by_type.values()
            last_end_time = max(end_times)

        for keyframe_type, end_time in anim_end_by_type.items():
            if (max_end_time is None) or (end_time > max_end_time):
                msg = "WARNING: " + msg
            if last_end_time is None:
                print(msg % (keyframe_type, os.path.basename(anim_file), end_time))
            elif last_end_time == end_time:
                #print(msg % (keyframe_type, os.path.basename(anim_file), end_time))
                longest_tracks.append(str(keyframe_type))

        if longest_tracks:
            print(msg % (', '.join(longest_tracks), os.path.basename(anim_file), last_end_time))


if __name__ == "__main__":
    input_files = sys.argv[1:]
    main(input_files, MAX_END_TIME)


