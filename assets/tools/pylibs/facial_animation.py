
FACIAL_ANIM_DIR = "sprites/spriteSequences"

KEYFRAME_TYPE_ATTR = "Name"
FACIAL_KEYFRAME_NAME = "FaceAnimationKeyFrame"
FACIAL_ANIM_NAME = "animName"
TRIGGER_TIME_ATTR = "triggerTime_ms"
DURATION_TIME_ATTR = "durationTime_ms"

FACIAL_KEYFRAME = {
  KEYFRAME_TYPE_ATTR : FACIAL_KEYFRAME_NAME,
  TRIGGER_TIME_ATTR  : 0,
  FACIAL_ANIM_NAME   : None
}

RAISE_HEAD_KEYFRAME = {
  KEYFRAME_TYPE_ATTR     : "HeadAngleKeyFrame",
  TRIGGER_TIME_ATTR      : 0,
  "angle_deg"            : 45,
  "angleVariability_deg" : 0,
  DURATION_TIME_ATTR     : 99
}

FRAME_TIME = 33 # ms


import os
import json
import tarfile
import tempfile
import copy


def unpack_tarball(tar_file):
    unpacked_files = []
    dest_dir = tempfile.mkdtemp()
    try:
        tar = tarfile.open(tar_file)
    except tarfile.ReadError as e:
        raise RuntimeError("%s: %s" % (e, tar_file))
    #print("Unpacking %s in %s..." % (tar_file, dest_dir))
    tar.extractall(dest_dir)
    for member in tar:
        member = os.path.join(dest_dir, member.name)
        unpacked_files.append(member)
    tar.close()
    return unpacked_files


def get_facial_png_files(facial_anim, source_dir):
    facial_tar_file = facial_anim + ".tar"
    facial_tar_file = os.path.join(source_dir, facial_tar_file)
    print("Facial tar file = %s" % facial_tar_file)
    if not os.path.isfile(facial_tar_file):
        raise ValueError("Unable to locate '%s' file to send that facial animation to the robot"
                         % facial_tar_file)
    png_files = unpack_tarball(facial_tar_file)
    return png_files


def get_facial_anims(anim_file):
    facial_anims = []
    fh = open(anim_file, 'r')
    try:
        contents = json.load(fh)
    except StandardError as e:
        print("Failed to read %s file because: %s" % (anim_file, e))
        return []
    finally:
        fh.close()
    for anim_clip, keyframes in contents.items():
        anim_clip = str(anim_clip)
        #print("num keyframes = %s" % len(keyframes))
        for keyframe in keyframes:
            try:
                keyframe_type = str(keyframe[KEYFRAME_TYPE_ATTR])
            except KeyError:
                continue
            if keyframe_type != FACIAL_KEYFRAME_NAME:
                continue
            facial_anims.append(str(keyframe[FACIAL_ANIM_NAME]))
    print("Facial animations in %s = %s" % (anim_file, facial_anims))
    return facial_anims


def make_facial_anim(anim_name, anim_file, sprite_asset_name, frame_count, trigger_time=0,
                     raise_head=True, min_length_ms=None):
    """
    Given an animation name, animation file, sprite asset name and
    trigger time, this function can be used to generate a simple test
    animation to trigger that image/sprite asset.
    """
    first_keyframe = copy.copy(FACIAL_KEYFRAME)
    first_keyframe[FACIAL_ANIM_NAME] = sprite_asset_name
    first_keyframe[TRIGGER_TIME_ATTR] = trigger_time

    anim_data = { anim_name : [ first_keyframe ] }

    # Using the provided frame count for the given sprite asset, add enough keyframes
    # to this animation so that sprite asset is looped enough times to satisfy the
    # provided minimum length for the animation.
    if min_length_ms:
        next_trigger_time = trigger_time + (frame_count * FRAME_TIME)
        while next_trigger_time < min_length_ms:
            next_keyframe = copy.copy(FACIAL_KEYFRAME)
            next_keyframe[FACIAL_ANIM_NAME] = sprite_asset_name
            next_keyframe[TRIGGER_TIME_ATTR] = next_trigger_time
            anim_data[anim_name].append(next_keyframe)
            next_trigger_time += (frame_count * FRAME_TIME)

    if raise_head:
        anim_data[anim_name].append(RAISE_HEAD_KEYFRAME)

    output_json = json.dumps(anim_data, sort_keys=False, indent=2, separators=(',', ': '))
    anim_file_dir = os.path.dirname(anim_file)
    if not os.path.exists(anim_file_dir):
        os.makedirs(anim_file_dir)
    try:
        with open(anim_file, 'w') as fh:
            fh.write(output_json)
    except StandardError as e:
        print("Failed to write %s file because: %s" % (anim_file, e))
    finally:
        fh.close()
        print("Wrote %s file with a keyframe for '%s' triggered at time %s ms"
              % (anim_file, sprite_asset_name, trigger_time))


