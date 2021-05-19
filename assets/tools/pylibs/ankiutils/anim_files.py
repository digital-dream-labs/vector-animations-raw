
FILE_LAST_UPDATED_MSG = "%s was last updated %.2f %s ago"

MAYA_FILE_EXT = ".ma"

OUTPUT_PACKAGE_EXT = ".tar"


import sys
import os
import subprocess
import time
import pprint


def get_newest_json_file(dir_path, file_ext=".json"):
    # Get the last file we think is modified in there...
    proc = subprocess.Popen("cd %s; ls -1t *%s  | head -1" % (dir_path, file_ext), stdout=subprocess.PIPE, shell=True)
    (anim_file, err) = proc.communicate()
    if not anim_file:
        raise ValueError("No animation file found in %s" % dir_path)
    anim_file = anim_file.strip()
    anim_file = os.path.join(dir_path, anim_file)
    print("Last exported animation = %s" % anim_file)
    return anim_file


def get_json_file_for_anim(anim_name, dir_path, file_ext=".json", exists=True):
    # Get the anim file for a given animation
    anim_file = anim_name
    if not anim_file.endswith(file_ext):
        anim_file += file_ext
    if not anim_file.startswith(os.sep):
        anim_file = os.path.join(dir_path, anim_file)
    #print("Animation = %s" % anim_file)
    if exists and not os.path.isfile(anim_file):
        raise ValueError("Animation file not available: %s" % anim_file)
    return anim_file


def report_file_stats(anim_file):
    try:
        stat = os.stat(anim_file)
    except (IOError, OSError) as e:
        if e.errno == errno.ENOENT:
            raise ValueError("Animation file not available: %s" % anim_file)
        else:
            raise
    mod_time = stat.st_mtime
    current_time = time.time()
    mod_age = current_time - mod_time
    if mod_age > 86400.0:
        mod_age = mod_age / 86400.0
        age_units = "days"
    elif mod_age > 3600.0:
        mod_age = mod_age / 3600.0
        age_units = "hours"
    elif mod_age > 60.0:
        mod_age = mod_age / 60.0
        age_units = "minutes"
    else:
        age_units = "seconds"
    file_stat_msg = FILE_LAST_UPDATED_MSG % (os.path.basename(anim_file), mod_age, age_units)
    return file_stat_msg


def get_all_maya_files(maya_files_dir):
    maya_files = []
    for dir_path, dirs, files in os.walk(maya_files_dir):
        for maya_file in files:
            if not maya_file.endswith(MAYA_FILE_EXT):
                continue
            maya_file = os.path.join(dir_path, maya_file)
            if os.path.isfile(maya_file):
                maya_files.append(maya_file)
            else:
                print("%s is not a valid file" % maya_file)
    print(os.linesep + "maya_files = %s" % pprint.pformat(maya_files))
    return maya_files


