import tarfile
import os
import json
import time
import tarfile
from datetime import datetime, timedelta
import anim_groups
import copy

"""
This is a rough, unfinished version of a tool to help check json values
"""


ANIMATIONS_DIR = "/Users/dariajerjomina/workspace/victor-animation-assets/trunk/animations"
ANIM_PATH = "/Users/dariajerjomina/workspace/victor-animation/scenes"

HOME_DIR = os.getenv("HOME")
PROBLEM_JSONS_PATH = JSON_EXPORT_PATH_RED_FLAGED = os.path.join(HOME_DIR,".anki","maya","eye_intersection_data", "red_flaged_005")


def is_all_bad_overshoot_value_json_file(json_path, condition=">", value=0.0):
    new_data = None
    bad_paths = []
    good_value_num = 0
    print "json_path ",json_path
    with open(json_path) as data_file:
        data = json.load(data_file)
        for clip_name, clip_data in data.iteritems():
            for frame_num, frame_data in clip_data.iteritems():
                for i, item in enumerate(frame_data):
                        if check_condition(condition=condition, value01=value, value02=item["overshoot_value"]):
                            bad_paths.append([clip_name,frame_num,i])
                        else:
                            good_value_num+=1
        #find_overshoot_values(condition=">", value=0.0, recursive=True)
    if good_value_num==0:
        return True
    else:
        return False
        # for path in  bad_paths:
        #     print path
        #     data[path[0]][path[1]][path[2]] = None
        #     #del data[bad_paths[0]][bad_paths[1]][bad_paths[2]]
        # print data

def remove_bad_overshoot_value_jsons(condition=">", value=0.0, path=PROBLEM_JSONS_PATH):
    removed_files = []
    for file_in_question in os.listdir(path):
        file_in_question = os.path.join(path, file_in_question)
        if (is_all_bad_overshoot_value_json_file(json_path=file_in_question, condition=condition, value=value)):
            removed_files.append(file_in_question)
            os.remove(file_in_question)
    print "removed %s files" %(len(removed_files))
    print removed_files

def check_condition(condition=">", value01=0.0, value02=0.0):
    #todo: try doing this with eval
    if (condition==">"):
        if value01>value02: return True
    elif (condition == "<"):
        if value01 < value02: return True
    elif (condition == "=="):
        if value01 == value02: return True
    elif (condition == "<="):
        if value01 <= value02: return True
    elif (condition == ">="):
        if value01 >= value02: return True
    else:
        print ("%s is not an acceptable condition")

def split_list(list_to_split, split_item="__"):
    sub_list = []
    splited_list = []
    for item in list_to_split:
        if item!=split_item or item is None:
            sub_list.append(item)
        else:
            splited_list.append(sub_list)
            sub_list = []
    return splited_list

# def find_overshoot_values(data, key_name, condition=">", value01=0.0, value02=0.0):


#TODO: AT SOME POINT MAKE JSON AUDIT WORK RECURSIVELY

# def track_path_to_key(input_json, target_key, path_tracker=None, last_key=None, separator="__"):
#     print "path_tracker ", path_tracker
#     print "last_key ", last_key
#     if path_tracker is None:
#         path_tracker = []
#
#     if last_key is not None:
#         # When function is called, it creates its own scope/block so that changes to variables in function process is isolated from global scope.
#         print "path_tracker ", path_tracker
#         path_tracker = list(path_tracker + [last_key])
#
#     if isinstance(input_json, dict) and input_json:
#         for key in input_json:
#             if key == target_key:
#                 path_tracker.append(separator)
#                 return path_tracker
#
#             if type(input_json[key]) is dict or type(input_json[key]) is list:
#                 path_tracker = track_path_to_key(input_json[key], target_key, path_tracker, key)
#
#     elif isinstance(input_json, list) and input_json:
#         for entity in input_json:
#             path_tracker = track_path_to_key(entity, target_key, path_tracker,
#                                              input_json.index(entity))
#
#     else:
#        if path_tracker: #If path_tracker is not empty
#            path_tracker.pop()
#
#     return path_tracker
#
# def audit_json_file(input_json, key_name, separator="__"):
#     all_key_paths_merged = track_path_to_key(input_json=input_json, target_key=key_name, path_tracker=None, last_key=None, separator=separator)
#     all_key_paths = split_list(all_key_paths_merged, separator)
#     for key_path in all_key_paths:
#         print split_list(key_path, None)



# CLOSEST ONE, but path finding doesn't work
# def find_values_in_json_node(key_name, data_node, all_values, problem_values, key_paths, key_path, condition, value, last_key = None, separator = ""):
#     if last_key is not None:
#         # When function is called, it creates its own scope/block so that changes to variables in
#         #  function process is isolated from global scope.
#         key_path = list(key_path + [last_key])
#
#     if isinstance(data_node, dict) and data_node:
#         if key_name in data_node.keys():
#             all_values.append(data_node[key_name])
#             if check_condition(condition, data_node[key_name], value):
#                 problem_values.append(data_node[key_name])
#             print "key_path.append(%s)" % (key_name)
#             key_path.append(key_name)
#             print "key_path = %s" %(key_path)
#             key_paths.append(copy.copy(key_path))
#             print "key_path = []"
#             key_path = []
#         for key, item in data_node.iteritems():
#             print "key_path.append(%s)" %(key)
#             key_path.append(key)
#             find_values_in_json_node(key_name, item, all_values, problem_values, key_paths, key_path, condition, value)
#
#     elif isinstance(data_node, list) and data_node:
#         loop_path = []
#         for i, item in enumerate(data_node):
#             print "key_path.append(%s)" %(i)
#             #key_path_beofre_loop.append(i)
#             find_values_in_json_node(key_name, item, all_values, problem_values, key_paths, key_path, condition, value)
    # leaf
    # else:
    #     key_path = []





def get_lightness_value(clip_path):
    """
    Finds all clips mentioned in animgroups
    """
    lightness_values = []
    with open(clip_path) as data_file:
        data = json.load(data_file)
        for anim_node in data.values()[0]:
            if anim_node["Name"] == "ProceduralFaceKeyFrame":
                try:
                    # if (anim_node["leftEye"][19]!=1):
                    lightness_values.append(anim_node["leftEye"][21])
                    # if (anim_node["rightEye"][19] != 1):
                    lightness_values.append(anim_node["rightEye"][21])
                except IndexError:
                    pass
        return lightness_values


def get_lightness_in_tar(path_to_tar):
    if (path_to_tar.endswith("tar") or path_to_tar.endswith("tar.gz")):
        tar = tarfile.open(path_to_tar)
        tar_kids = tar.getnames()
        tar.extractall(path=ANIMATIONS_DIR)
    else:
        return None

    lightness_values_dict = {}
    for kid_file in tar_kids:
        if kid_file[-5:] == ".json":
            non_default_values = []
            lightness_values = get_lightness_value(ANIMATIONS_DIR+"/"+kid_file)
            for value in lightness_values:
                #if not (0.9 < value < 1.1):
                if value!=0:
                    non_default_values.append(value)
            # ignore empty non-default values and the ones where all elements are identical
            if non_default_values!=[] and non_default_values.count(non_default_values[0])!=len(non_default_values):
                lightness_values_dict[kid_file] = non_default_values
        os.remove(ANIMATIONS_DIR+"/"+kid_file)
    return lightness_values_dict

# def get_values_in_tar(path_to_tar, condition, value):
#     if (path_to_tar.endswith("tar") or path_to_tar.endswith("tar.gz")):
#         tar = tarfile.open(path_to_tar)
#         tar_kids = tar.getnames()
#         tar.extractall(path=ANIMATIONS_DIR)
#     else:
#         return None
#
#     values_dict = {}


def get_problem_ma_files(tar_files):
    anim_files = []
    files_str = ""
    for root, dirs, filenames in os.walk(ANIM_PATH):
        for filename in filenames:
            if "." in filename:
                if filename.split(".")[1]=="ma" and filename.split(".")[0] in tar_files:
                    anim_files.append(os.path.join(root[49:],filename))
                    files_str+=str(os.path.join(root[49:],filename))
                    files_str += " "
    return anim_files, files_str

def find_problem_lightness():
    all_non_default_lightness = []
    tar_files = []
    for file_in_question in os.listdir(ANIMATIONS_DIR):
        if (file_in_question.endswith("tar") or file_in_question.endswith("tar.gz")):
            lightness_values = get_lightness_in_tar(ANIMATIONS_DIR+"/"+file_in_question)
            if lightness_values!={} and lightness_values!=None:
                tar_files.append(file_in_question.split("/")[-1].split(".")[0])
                all_non_default_lightness.append(lightness_values)

    print "There are %s tar files with non default lightness values" %(len(all_non_default_lightness))
    print "tar_files=%s" %(tar_files)
    for lightness_val in all_non_default_lightness:
        print "\n"
        for json_name, lightness_vals in lightness_val.iteritems():
            print "json file: ", json_name
            print "non default lightness values:", lightness_vals

    print "problem_ma_files=%s" %(get_problem_ma_files(tar_files)[1])
    print "problem_ma_files=%s" % (get_problem_ma_files(tar_files)[0])

def main():
    pass


# import ankimaya.find_in_anim_clip_json
# reload(ankimaya.find_in_anim_clip_json)
# ankimaya.find_in_anim_clip_json.main()


# some_json_dict = {"01":{"01_a":0,"01_b":{"id":"correct value"}},"02":{"02_a":0,"02_b":0,"02_c":{"id":1,"id02":"wrong value"}}}
#
# print track_path_to_key(some_json_dict,"id", 3)
#
# def track_path_to_key(input_json, target_key, update_value, path_tracker = None ,  last_key = None):
#     if path_tracker is None:
#         path_tracker = []
#
#     if last_key is not None:
#         #When function is called, it creates its own scope/block so that changes to variables in function process is isolated from global scope.
#         path_tracker = list(path_tracker + [last_key])
#
#     if type(input_json) is dict and input_json:
#         for key in input_json:
#             if key == target_key:
#                 return path_tracker
#
#             if type(input_json[key]) is dict or type(input_json[key]) is list:
#                 path_tracker = track_path_to_key(input_json[key], target_key, update_value, path_tracker, key)
#
#     elif type(input_json) is list and input_json:
#         for entity in input_json:
#             path_tracker = track_path_to_key(entity, target_key, update_value, path_tracker, input_json.index(entity))
#
#     else:
#         if path_tracker: #If path_tracker is not empty
#             path_tracker.pop()
#
#     return path_tracker