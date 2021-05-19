#!/usr/bin/env python
"""
This script can be used to audit animation assets and see if any
Maya scene files are missing the corresponding tar file (and vice
versa) or if any Maya scene anim clips are missing from the
corresponding tar file (and vice versa).  Performance was not a
concern when this script was first written.
"""

SVN_REPO_WITH_MAYA_FILES = "victor-animation"
SVN_REPO_WITH_TAR_FILES  = "victor-animation-assets"

ANIM_CLIP_FLAG = "-anim_clip"
AUDIO_EVENT_FLAG = "-audio_event"
MISSING_FLAG_ARG_MSG  = "When the %s flag is provided, it must be immediately "
MISSING_FLAG_ARG_MSG += "followed by the %s name"

KEYFRAME_TYPE_KEY = "Name"
TRIGGER_TIME_KEY = "triggerTime_ms"
DURATION_TIME_KEY = "durationTime_ms"

BACKPACK_KEYFRAME_TYPE = "BackpackLightsKeyFrame"

BODY_MOTION_KEYFRAME_TYPE = "BodyMotionKeyFrame"
RADIUS_ATTR = "radius_mm"

AUDIO_KEYFRAME_TYPE = "RobotAudioKeyFrame"


import sys
import os
import pprint
import tempfile
import tarfile
import json
import subprocess

from ankishotgun.anim_data import get_files_in_tarball, get_clips_in_maya_scene
from ankishotgun.anim_data import ShotgunAssets, SG_PROJECTS
from robot_config import MIN_RADIUS_MM, MAX_RADIUS_MM


HOME = os.getenv("HOME")
TAR_FILE_DIR  = os.path.join(HOME, 'workspace', SVN_REPO_WITH_TAR_FILES, 'animations')
MAYA_FILE_DIR = os.path.join(HOME, 'workspace', SVN_REPO_WITH_MAYA_FILES, 'scenes', 'anim')


def get_maya_files(root_dir):
    all_maya_files = []
    for dir_name, subdir_list, file_list in os.walk(root_dir):
        maya_files = [x for x in file_list if x.endswith(".ma")]
        all_maya_files.extend([os.path.join(dir_name, x) for x in maya_files])
    return all_maya_files


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


def unpack_tarball(tar_file):
    unpacked_files = []
    dest_dir = tempfile.mkdtemp()
    try:
        tar = tarfile.open(tar_file)
    except tarfile.ReadError, e:
        raise RuntimeError("%s: %s" % (e, tar_file))
    #print("Unpacking %s in %s..." % (tar_file, dest_dir))
    tar.extractall(dest_dir)
    for member in tar:
        member = os.path.join(dest_dir, member.name)
        unpacked_files.append(member)
    tar.close()
    return unpacked_files


def check_probabilities_and_volume(json_file):
    fh = open(json_file, 'r')
    contents = fh.read()
    fh.close()
    keyframes = json.loads(contents)
    for key, value in keyframes.items():
        for keyframe in value:
            if keyframe[KEYFRAME_TYPE_KEY] == AUDIO_KEYFRAME_TYPE:
                if "eventGroups" in keyframe:
                    all_probs = []
                    for probability in keyframe["eventGroups"][0]["probabilities"]:
                        all_probs.append(probability)
                    if sum(all_probs) > 1.0:
                        return True
                    for volume in keyframe["eventGroups"][0]["volumes"]:
                        if volume > 1.0:
                            return True


def check_light_color_values(json_file, tar_file):
    msg = "One of the RGBA values at time %s in %s (%s) has a value of %s"
    fh = open(json_file, 'r')
    contents = fh.read()
    fh.close()
    keyframes = json.loads(contents)
    for key, value in keyframes.items():
        for keyframe in value:
            if keyframe[KEYFRAME_TYPE_KEY] == BACKPACK_KEYFRAME_TYPE:
                for light, rgba in keyframe.items():
                    if light in [KEYFRAME_TYPE_KEY, TRIGGER_TIME_KEY, DURATION_TIME_KEY]:
                        continue
                    for val in rgba:
                        if val < 0.0 or val > 1.0:
                            print(msg % (keyframe[TRIGGER_TIME_KEY], key, os.path.basename(tar_file), val))


def check_radius_values(json_file, tar_file):
    msg = "One of the radius values at time %s in %s (%s) has a value of %s"
    fh = open(json_file, 'r')
    contents = fh.read()
    fh.close()
    keyframes = json.loads(contents)
    for key, value in keyframes.items():
        for keyframe in value:
            if keyframe[KEYFRAME_TYPE_KEY] == BODY_MOTION_KEYFRAME_TYPE:
                try:
                    radius = keyframe[RADIUS_ATTR]
                except KeyError:
                    continue
                if isinstance(radius, basestring):
                    continue
                if radius < MIN_RADIUS_MM or radius > MAX_RADIUS_MM:
                    print(msg % (keyframe[TRIGGER_TIME_KEY], key, os.path.basename(tar_file), radius))


def check_probabilities_in_tars():
    problem_jsons = []
    problem_tars = []
    tar_files = get_tar_files(TAR_FILE_DIR)
    for tar_file in tar_files:
        anim_files = unpack_tarball(tar_file)
        for anim_file in anim_files:
            if check_probabilities_and_volume(anim_file):
                problem_jsons.append(anim_file)
                if tar_file not in problem_tars:
                    problem_tars.append(tar_file)
    print "problem_jsons = ", problem_jsons
    print "problem_tars = ", problem_tars


def check_keyframes(lights=True, radius=True):
    tar_files = get_tar_files(TAR_FILE_DIR)
    for tar_file in tar_files:
        anim_files = unpack_tarball(tar_file)
        for anim_file in anim_files:
            if lights:
                check_light_color_values(anim_file, tar_file)
            if radius:
                check_radius_values(anim_file, tar_file)


def summarize_keyframes(json_file):
    keyframe_summary = {}
    fh = open(json_file, 'r')
    contents = fh.read()
    fh.close()
    keyframes = json.loads(contents)
    for key, value in keyframes.items():
        if key not in keyframe_summary:
            keyframe_summary[key] = {}
        for v in value:
            type = v[KEYFRAME_TYPE_KEY]
            if type not in keyframe_summary[key]:
                keyframe_summary[key][type] = tuple()
            keyframe_summary[key][type] += (int(v[TRIGGER_TIME_KEY]),)
    return keyframe_summary


def compare_anim_files(f1, f2):
    f1keyframes = summarize_keyframes(f1)
    f2keyframes = summarize_keyframes(f2)
    if f1keyframes != f2keyframes:
        f1name = f1keyframes.keys()[0]
        f2name = f2keyframes.keys()[0]
        f1keyframes = f1keyframes[f1name]
        f2keyframes = f2keyframes[f2name]
        keyframe_diffs = set(f1keyframes.items()) ^ set(f2keyframes.items())
        if keyframe_diffs:
            print("The differences between '%s' and '%s' are:" % (f1name, f2name))
            for keyframe_diff in keyframe_diffs:
                print("    %s: %s" % keyframe_diff)


def compare_all_head_angle_variations(headAngleFileToken="_head_angle_"):
    tar_files = get_tar_files(TAR_FILE_DIR)
    for tar_file in tar_files:
        anim_files = unpack_tarball(tar_file)
        for anim_file in anim_files:
            if headAngleFileToken in anim_file:
                orig_file = anim_file.split(headAngleFileToken)[0]
                orig_file += os.path.splitext(anim_file)[1]
                #print("Need to compare [%s] to [%s]" % (os.path.basename(anim_file), os.path.basename(orig_file)))
                compare_anim_files(anim_file, orig_file)


def get_anim_clip_of_interest():
    anim_clip = None
    if ANIM_CLIP_FLAG in sys.argv:
        idx = sys.argv.index(ANIM_CLIP_FLAG)
        try:
            anim_clip = sys.argv[idx+1]
        except IndexError:
            raise ValueError(MISSING_FLAG_ARG_MSG % (ANIM_CLIP_FLAG, "anim clip"))
    return anim_clip


def get_audio_event_of_interest():
    audio_event = None
    if AUDIO_EVENT_FLAG in sys.argv:
        idx = sys.argv.index(AUDIO_EVENT_FLAG)
        try:
            audio_event = sys.argv[idx+1]
        except IndexError:
            raise ValueError(MISSING_FLAG_ARG_MSG % (AUDIO_EVENT_FLAG, "audio event"))
    return audio_event


def check_for_missing_maya_data(tar_file_dict, maya_file_dict, anim_clip, audio_event):
    missing_maya_clips = []
    missing_maya_files = []
    for file_name, file_paths in tar_file_dict.items():
        file_path = file_paths[0]
        maya_file = os.path.splitext(file_name)[0] + '.ma'
        if maya_file in maya_file_dict:
            for maya_file_path in maya_file_dict[maya_file]:
                maya_clips = get_clips_in_maya_scene(maya_file_path)
                if not maya_clips:
                    maya_clips = [os.path.splitext(maya_file)[0]]
                tar_clips = get_files_in_tarball(file_path, ['.json'])
                if audio_event:
                    unpacked_files = unpack_tarball(file_path)
                    audio_event_usage = []
                    for json_file in unpacked_files:
                        fh = open(json_file, 'r')
                        contents = fh.read()
                        fh.close()
                        if audio_event in contents:
                            audio_event_usage.append(os.path.basename(json_file))
                    if audio_event_usage:
                        print("%sALERT: The audio event of interest (%s) is used in %s (in %s)"
                              % (os.linesep, audio_event, file_name, audio_event_usage))
                for tar_clip in tar_clips:
                    if tar_clip != tar_clip.lower():
                        print("%sALERT: The '%s' file/asset is NOT strictly lowercase"
                              % (os.linesep, tar_clip))
                    maya_clip = os.path.splitext(tar_clip)[0]
                    if maya_clip not in maya_clips:
                        try:
                            maya_file_rel_path = maya_file_path.split(MAYA_FILE_DIR)[1][1:]
                        except IndexError:
                            maya_file_rel_path = maya_file_path
                        if "_head_angle_" not in maya_clip:
                            missing_maya_clips.append((maya_clip, maya_file_rel_path))
                    if anim_clip and anim_clip == maya_clip:
                        print("%sALERT: The anim clip of interest (%s) comes from %s"
                              % (os.linesep, anim_clip, file_path))
        else:
            missing_maya_files.append(maya_file)
    return (missing_maya_files, missing_maya_clips)


def check_for_missing_tar_data(tar_file_dict, maya_file_dict, anim_clip):
    missing_tar_clips = []
    missing_tar_files = []
    for file_name, file_paths in maya_file_dict.items():
        tar_file = os.path.splitext(file_name)[0] + '.tar'
        if tar_file in tar_file_dict:
            for file_path in file_paths:
                maya_clips = get_clips_in_maya_scene(file_path)
                if not maya_clips:
                    maya_clips = [os.path.splitext(file_name)[0]]
                tar_clips = get_files_in_tarball(tar_file_dict[tar_file][0], ['.json'])
                for maya_clip in maya_clips:
                    if maya_clip != maya_clip.lower():
                        print("%sALERT: The '%s' asset (from %s) is NOT strictly lowercase"
                              % (os.linesep, maya_clip, file_path))
                    tar_clip = maya_clip + '.json'
                    if tar_clip not in tar_clips:
                        missing_tar_clips.append((tar_clip, tar_file))
                    if anim_clip and anim_clip == maya_clip:
                        print("%sALERT: The anim clip of interest (%s) comes from %s"
                              % (os.linesep, anim_clip, file_path))
        else:
            missing_tar_files.append(tar_file)
    return (missing_tar_files, missing_tar_clips)


def check_asset_tasks(sg_assets, asset, asset_name, proj):
    tasks = sg_assets.get_tasks(asset, proj)
    missing_tasks = 0
    for task in tasks:
        if not task:
            missing_tasks += 1
    if missing_tasks > 0:
        print("%sALERT: The '%s' asset in the '%s' project is missing %s task(s)"
              % (os.linesep, asset_name, proj, missing_tasks))


def compare_assets_to_files(assets, file_name, tar_file_dict, proj):
    assets = map(lambda x: x["code"], assets)
    assets.sort()
    anim_files = unpack_tarball(tar_file_dict[file_name][0])
    anim_files = map(os.path.basename, anim_files)
    anim_files = map(lambda x: os.path.splitext(x)[0], anim_files)
    anim_files.sort()
    if assets != anim_files:
        print("%sALERT: The %s file contains %s but the corresponding asset list in '%s' is %s"
              % (os.linesep, file_name, anim_files, proj, assets))


def check_for_duplicate_or_missing_assets_in_sg(tar_file_dict):
    audit_sg_assets = {}
    proj = SG_PROJECTS[0]
    sg_assets = ShotgunAssets()
    all_assets = sg_assets.get_all_assets(proj)
    all_tar_files = tar_file_dict.keys()
    tar_file_tracker = tar_file_dict.keys()
    for file_name in all_tar_files:
        assets = sg_assets.get_assets_by_output_file(file_name, proj, all_assets)
        if not assets:
            print("%sALERT: There are no assets in the '%s' project for the '%s' output file"
                  % (os.linesep, proj, file_name))
        compare_assets_to_files(assets, file_name, tar_file_dict, proj)
    audit_sg_assets[proj] = []
    for asset in all_assets[proj]:
        asset_name = asset[sg_assets.asset_name_attr]
        asset_type = asset[sg_assets.asset_type_attr]
        if (not asset_name.startswith('anim_') and asset_type in ["Animation"]) or (not asset_name.startswith('ag_') and asset_type in ["Animation Group"]):
            print("%sALERT: The '%s' %s asset does not satisfy the naming convention"
                  % (os.linesep, asset_name, asset_type.lower()))
        try:
            output_file = asset[sg_assets.output_file_attr]["name"]
            output_file_url = asset[sg_assets.output_file_attr]["url"]
        except (TypeError, KeyError):
            print("%sALERT: There is no valid output file set for the '%s' asset" % (os.linesep, asset_name))
        else:
            if output_file not in all_tar_files and asset_type in ["Animation"]:
                print("%sALERT: The '%s' output file for the '%s' asset doesn't appear to exist. "
                      "Was that asset intentionally removed?" % (os.linesep, output_file, asset_name))
            try:
                check_svn_file_url(output_file_url)
            except ValueError, e:
                print("%sALERT: Invalid output file URL for '%s' (%s): %s"
                      % (os.linesep, asset_name, asset_type, output_file_url))
            while output_file in tar_file_tracker:
                tar_file_tracker.remove(output_file)
        if asset_name != asset_name.lower():
            print("%sALERT: The '%s' asset (%s) in the '%s' project is NOT strictly lowercase"
                  % (os.linesep, asset_name, asset_type, proj))
        if asset_name in audit_sg_assets[proj]:
            print("%sCONFLICT: Found multiple '%s' assets in the '%s' project"
                  % (os.linesep, asset_name, proj))
        else:
            audit_sg_assets[proj].append(asset_name)
        if asset_type in ["Animation"]:
            check_asset_tasks(sg_assets, asset, asset_name, proj)
    if tar_file_tracker:
        print("%sALERT: The following tar files have no corresponding asset(s) in Shotgun:%s%s"
              % (os.linesep, os.linesep, pprint.pformat(tar_file_tracker)))


def check_svn_file_url(file_url):
    svn_info_cmd = "svn info %s" % file_url
    p = subprocess.Popen(svn_info_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    stdout, stderr = p.communicate()
    #stdout = stdout.strip()
    #stderr = stderr.strip()
    status = p.poll()
    if status != 0:
        raise ValueError(file_url)


def main():
    anim_clip = get_anim_clip_of_interest()
    audio_event = get_audio_event_of_interest()

    maya_files = get_maya_files(MAYA_FILE_DIR)
    maya_file_dict = fill_file_dict(maya_files)
    #pprint.pprint(maya_file_dict)

    tar_files = get_tar_files(TAR_FILE_DIR)
    tar_file_dict = fill_file_dict(tar_files)
    #pprint.pprint(tar_file_dict)

    missing_tar_files, missing_tar_clips = check_for_missing_tar_data(tar_file_dict, maya_file_dict, anim_clip)
    missing_maya_files, missing_maya_clips = check_for_missing_maya_data(tar_file_dict, maya_file_dict, anim_clip, audio_event)

    check_for_duplicate_or_missing_assets_in_sg(tar_file_dict)

    # There are lots of tar files "missing" since we keep the Maya files when we cleanup tar files for unused/old/prototype animations.
    #if missing_tar_files:
    #    missing_tar_files.sort()
    #    print(os.linesep + "It appears that the following tar files are missing:")
    #    pprint.pprint(missing_tar_files)

    if missing_maya_files:
        missing_maya_files.sort()
        print(os.linesep + "It appears that the following Maya files are missing:")
        pprint.pprint(missing_maya_files)

    if missing_maya_clips:
        print(os.linesep + "It appears that the following anim clips are missing in Maya files:")
        for missing in missing_maya_clips:
            print("  '%s' is missing from %s" % missing)

    if missing_tar_clips:
        print(os.linesep + "It appears that the following anim clips are missing in tar files:")
        for missing in missing_tar_clips:
            print("  '%s' is missing from %s" % missing)


if __name__ == "__main__":
    main()
    #compare_all_head_angle_variations()
    #check_keyframes()


