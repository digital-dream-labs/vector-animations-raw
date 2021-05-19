#!/usr/bin/env python

MAX_NUM = 999

KEYFRAME_TYPE_KEY = "Name"
TRIGGER_TIME_KEY = "triggerTime_ms"

PROC_FACE_KEYFRAME = "ProceduralFaceKeyFrame"
LIGHTNESS_IDX = 20

ALERT_FIRST_KEYFRAME_TIME_FLAG = "-check_first_keyframe_time"
SHOW_SINGLE_TRACK_ANIMATIONS_FLAG = "-show_single_track_animations"
LOOK_FOR_SOME_ZERO_LIGHTNESS_FLAG = "-look_for_some_zero_lightness"
LOOK_FOR_SOME_NONFULL_LIGHTNESS_FLAG = "-look_for_some_nonfull_lightness"


import sys
import os
import json
import glob


def get_keyframe_count_by_type(anim_data):
    keyframe_count_by_type = { 'BackpackLightsKeyFrame':0,
                               'BodyMotionKeyFrame':0,
                               'EventKeyFrame':0,
                               'FaceAnimationKeyFrame':0,
                               'HeadAngleKeyFrame':0,
                               'LiftHeightKeyFrame':0,
                               'ProceduralFaceKeyFrame':0,
                               'RecordHeadingKeyFrame':0,
                               'RobotAudioKeyFrame':0,
                               'TurnToRecordedHeadingKeyFrame':0 }
    for anim_name, keyframes in anim_data.items():
        for keyframe in keyframes:
            for key, val in keyframe.items():
                if key == KEYFRAME_TYPE_KEY:
                    keyframe_type = val
                    if keyframe_type in keyframe_count_by_type:
                        keyframe_count_by_type[keyframe_type] += 1
                    else:
                        keyframe_count_by_type[keyframe_type] = 1
    #print(keyframe_count_by_type)
    return keyframe_count_by_type


def get_all_keyframes_of_type(anim_data, keyframe_type):
    all_keyframes_of_type = {}
    for anim_name, keyframes in anim_data.items():
        all_keyframes_of_type[anim_name] = []
        for keyframe in keyframes:
            try:
                this_keyframe_type = keyframe[KEYFRAME_TYPE_KEY]
            except KeyError:
                print("Type of followking keyframe unknown since '%s' is not specified: %s" % (KEYFRAME_TYPE_KEY, keyframe))
                continue
            if this_keyframe_type == keyframe_type:
                all_keyframes_of_type[anim_name].append(keyframe)
    return all_keyframes_of_type


def get_first_keyframe_time_by_type(anim_data):
    first_keyframe_time_by_type = {}
    for anim_name, keyframes in anim_data.items():
        for keyframe in keyframes:
            keyframe_type = keyframe[KEYFRAME_TYPE_KEY]
            keyframe_time = int(keyframe[TRIGGER_TIME_KEY])
            if keyframe_type not in first_keyframe_time_by_type:
                first_keyframe_time_by_type[keyframe_type] = keyframe_time
            elif keyframe_type in first_keyframe_time_by_type:
                if keyframe_time < first_keyframe_time_by_type[keyframe_type]:
                    first_keyframe_time_by_type[keyframe_type] = keyframe_time
    #print(first_keyframe_time_by_type)
    return first_keyframe_time_by_type


def get_eye_lightness(keyframe_list, which_eye, eye_lightness_idx=LIGHTNESS_IDX):
    eye_lightness = []
    for keyframe in keyframe_list:
        try:
            eye_lightness.append(keyframe[which_eye][eye_lightness_idx])
        except IndexError:
            eye_lightness.append(None)
    return eye_lightness


def main(anim_files, max_num=None):
    for anim_file in anim_files:
        #print("-"*40)
        if not os.path.isfile(anim_file):
            print("missing file: %s" % anim_file)
            continue
        if not anim_file.endswith(".json"):
            print("skipping %s" % anim_file)
            continue
        #print(anim_file)
        fh = open(anim_file, 'r')
        try:
            anim_data = json.load(fh)
        except ValueError:
            fh.close()
            print("ERROR: Failed to read %s" % anim_file)
            continue
        fh.close()
        if ALERT_FIRST_KEYFRAME_TIME_FLAG in sys.argv:
            # Display the first keyframe time for each track
            first_keyframe_time_by_type = get_first_keyframe_time_by_type(anim_data)
            for keyframe_type, time in first_keyframe_time_by_type.items():
                print("%s: the first %s has a trigger time of %s ms" % (anim_file, keyframe_type, time))
        elif SHOW_SINGLE_TRACK_ANIMATIONS_FLAG in sys.argv:
            # Display the list of animations that only have a single track animated
            animated_tracks = []
            keyframe_count_by_type = get_keyframe_count_by_type(anim_data)
            for keyframe_type, count in keyframe_count_by_type.items():
                if count > 0:
                    animated_tracks.append(keyframe_type)
            if len(animated_tracks) == 0:
                print("%s as zero animated tracks" % anim_file)
            elif len(animated_tracks) == 1:
                print("%s only has animation on the '%s' track" % (anim_file, animated_tracks[0]))
        elif LOOK_FOR_SOME_ZERO_LIGHTNESS_FLAG in sys.argv or LOOK_FOR_SOME_NONFULL_LIGHTNESS_FLAG in sys.argv:
            # Display the list of animations where every eye keyframe has lightness keyed to zero
            eye_keyframes = get_all_keyframes_of_type(anim_data, PROC_FACE_KEYFRAME)
            for anim_name, keyframe_list in eye_keyframes.items():
                if not keyframe_list:
                    print("%s does not have any %s keyframes" % (anim_name, PROC_FACE_KEYFRAME))
                    continue
                left_eye_lightness_keys = get_eye_lightness(keyframe_list, "leftEye")
                num_keys_left = len(left_eye_lightness_keys)
                num_none_left = left_eye_lightness_keys.count(None)
                right_eye_lightness_keys = get_eye_lightness(keyframe_list, "rightEye")
                num_keys_right = len(right_eye_lightness_keys)
                num_none_right = right_eye_lightness_keys.count(None)
                if num_none_left:
                    print("%s has %s %s keyframes, but left eye lightness is only keyed %s times"
                          % (anim_name, len(keyframe_list), PROC_FACE_KEYFRAME, (num_keys_left-num_none_left)))
                if num_none_right:
                    print("%s has %s %s keyframes, but right eye lightness is only keyed %s times"
                          % (anim_name, len(keyframe_list), PROC_FACE_KEYFRAME, (num_keys_right-num_none_right)))
                if LOOK_FOR_SOME_ZERO_LIGHTNESS_FLAG in sys.argv:
                    num_zero_left = left_eye_lightness_keys.count(0)
                    num_zero_right = right_eye_lightness_keys.count(0)
                    print("%s has %s %s keyframes, left eye lightness is keyed %s times (%s times "
                          "to zero), right eye lightness is keyed %s times (%s times to zero)"
                          % (anim_name, len(keyframe_list), PROC_FACE_KEYFRAME, num_keys_left,
                             num_zero_left, num_keys_right, num_zero_right))
                if LOOK_FOR_SOME_NONFULL_LIGHTNESS_FLAG in sys.argv:
                    num_nonfull_left = len([x for x in left_eye_lightness_keys if x < 1 and x is not None])
                    num_nonfull_right = len([x for x in right_eye_lightness_keys if x < 1 and x is not None])
                    print("%s has %s %s keyframes, left eye lightness is keyed %s times (%s times to less "
                          "than one), right eye lightness is keyed %s times (%s times to less than one)"
                          % (anim_name, len(keyframe_list), PROC_FACE_KEYFRAME, num_keys_left,
                             num_nonfull_left, num_keys_right, num_nonfull_right))
        else:
            # Display the keyframe count for each track
            keyframe_count_by_type = get_keyframe_count_by_type(anim_data)
            for keyframe_type, count in keyframe_count_by_type.items():
                if max_num is None:
                    print("%s has %s %s keyframes" % (anim_file, count, keyframe_type))
                elif count > max_num:
                    print("%s has %s %s keyframes" % (anim_file, count, keyframe_type))


if __name__ == "__main__":
    input_files = sys.argv[1:]
    #main(input_files, MAX_NUM)
    main(input_files)


