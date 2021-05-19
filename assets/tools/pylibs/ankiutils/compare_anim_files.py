#!/usr/bin/env python
"""
Disclaimer: This is still rough and could use some cleanup.
"""

KEYFRAME_TYPES_CASTING_CHANGES = ["BodyMotionKeyFrame", "HeadAngleKeyFrame", "LiftHeightKeyFrame"]

PROB_ATTR = "probability"


import sys
import os
import json
import copy


def read_anim_file(anim_file):
    """
    Given the path to a .json animation file, this function
    will read the contents of that file and return a 2-item
    tuple of (animation name, list of all keyframes)
    """
    if not os.path.isfile(anim_file):
        raise ValueError("Anim file missing: %s" % anim_file)
    fh = open(anim_file, 'r')
    try:
        contents = json.load(fh)
    except StandardError, e:
        print("Failed to read %s file because: %s" % (anim_file, e))
        raise
    finally:
        fh.close()
    anim_name, all_keyframes = contents.items()[0]
    print("The '%s' animation (%s) has %s total keyframes"
          % (anim_name, anim_file, len(all_keyframes)))
    return (anim_name, all_keyframes)


def convert_vals_to_int(keyframe):
    for key in keyframe.keys():
        val = keyframe[key]
        try:
            val = int(round(val))
        except TypeError:
            pass
        keyframe[key] = val


def convert_all_body_motion_vals_to_int(keyframe_list):
    for keyframe in keyframe_list:
        if keyframe["Name"] in KEYFRAME_TYPES_CASTING_CHANGES:
            # We recently changed the values in some keyframes from floats
            # to integers, so generate an integer-only version of this keyframe
            # for comparison.
            convert_vals_to_int(keyframe)


def main(args):
    print(os.linesep + '-' * 40)

    first_file = args[0]
    second_file = args[1]
    first_name, first_keyframes = read_anim_file(first_file)
    second_name, second_keyframes = read_anim_file(second_file)

    first_keyframes_copy = copy.deepcopy(first_keyframes)
    convert_all_body_motion_vals_to_int(first_keyframes_copy)

    second_keyframes_copy = copy.deepcopy(second_keyframes)
    convert_all_body_motion_vals_to_int(second_keyframes_copy)

    print('-' * 40)
    print("The following keyframes are missing from %s:" % second_file)
    for keyframe in first_keyframes:
        if keyframe not in second_keyframes:
            if PROB_ATTR in keyframe and not isinstance(keyframe[PROB_ATTR], list):
                # We recently changed the "probability" attribute of audio keyframes from
                # a single float value to a list of floats, so check both forms here.
                keyframe_copy = copy.deepcopy(keyframe)
                keyframe_copy[PROB_ATTR] = [keyframe_copy[PROB_ATTR]]
                if keyframe_copy not in second_keyframes:
                    print(keyframe)
            elif keyframe["Name"] in KEYFRAME_TYPES_CASTING_CHANGES:
                keyframe_copy = copy.deepcopy(keyframe)
                convert_vals_to_int(keyframe_copy)
                if keyframe not in second_keyframes_copy and keyframe_copy not in second_keyframes:
                    print(keyframe)
            else:
                print(keyframe)

    print('-' * 40)
    print("The following keyframes are missing from %s:" % first_file)
    for keyframe in second_keyframes:
        if keyframe not in first_keyframes:
            if PROB_ATTR in keyframe and isinstance(keyframe[PROB_ATTR], list):
                # We recently changed the "probability" attribute of audio keyframes from
                # a single float value to a list of floats, so check both forms here.
                keyframe_copy = copy.deepcopy(keyframe)
                try:
                    keyframe_copy[PROB_ATTR] = keyframe_copy[PROB_ATTR][0]
                except IndexError:
                    print(keyframe)
                else:
                    if keyframe_copy not in first_keyframes:
                        print(keyframe)
            elif keyframe["Name"] in KEYFRAME_TYPES_CASTING_CHANGES:
                keyframe_copy = copy.deepcopy(keyframe)
                convert_vals_to_int(keyframe_copy)
                if keyframe not in first_keyframes_copy and keyframe_copy not in first_keyframes:
                    print(keyframe)
            else:
                print(keyframe)

    print('-' * 40 + os.linesep)


if __name__ == "__main__":
    main(sys.argv[1:])


