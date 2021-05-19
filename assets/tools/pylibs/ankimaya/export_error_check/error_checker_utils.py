import json
import os
from shutil import copyfile
import maya.cmds as mc

# Tool gets populated from the user json file, but in case of a reset or in case that file doesn't
# exist it gets copied from the original commited json file
#
JSON_FILE = os.path.join(os.path.dirname(__file__), "export_error_check.json")
# can be of a different maya version, so user json file is just in maya dir (instead of a sub version dir)
USER_JSON_FILE = os.path.join(os.getenv("HOME"), ".anki", "maya", "export_error_check.json")

VECTOR_MASTER_GRP = "x:actor_grp"
COZMO_MASTER_GRP = VECTOR_MASTER_GRP
BINGO_MASTER_GRP = "x:Bingo"

VECTOR_RIG_NAME = "Victor_rig_01.ma"
VECTOR_RIG_PATH = os.path.join(os.getenv("HOME"), "workspace", "victor-animation", "assets", "rigs",
                               VECTOR_RIG_NAME)
COZMO_RIG_NAME = "Cozmo_midRes_rig.ma"
COZMO_RIG_PATH = os.path.join(os.getenv("HOME"), "workspace", "cozmo-animation", "assets", "rigs",
                              COZMO_RIG_NAME)
BINGO_RIG_NAME = "bingo_rig_master.ma"
BINGO_RIG_PATH = os.path.join(os.getenv("HOME"), "workspace", "bingo-animation", "assets", "rigs",
                              BINGO_RIG_NAME)

CHARS = {"cozmo": [2016, COZMO_RIG_NAME, COZMO_RIG_PATH, COZMO_MASTER_GRP],
         "victor": [2018, VECTOR_RIG_NAME, VECTOR_RIG_PATH, VECTOR_MASTER_GRP],
         "bingo": [2018, BINGO_RIG_NAME, BINGO_RIG_PATH, BINGO_MASTER_GRP]}

TOOLS_DIR = os.getenv("ANKI_PROJECT_ROOT")  # to find the name of the project

def update_anim_jsons(anim_jsons):
    """
    Sometimes get a list of both anim clips and tar files.
    This makes sure only json files are present in anim_jsons
    """
    updated_anim_jsons = []
    for anim_json in anim_jsons:
        if anim_json.split(".")[-1]=="json":
            updated_anim_jsons.append(anim_json)
    return updated_anim_jsons


def add_json_node(export_type="On Export", group_name="Animation", node_name = "",
                  tool_tip="", message="",
                  status="", fix_function="", user_json_file=USER_JSON_FILE, json_file = JSON_FILE):
    """
    Adds a node to the json file from which build the tool and populate the tree
    """
    if not os.path.exists(user_json_file):
        add_user_json_file(json_path=json_file, user_json_path=user_json_file)
    with open(user_json_file, "r+") as data_file:
        data = json.load(data_file)
        new_node = {"name":node_name, "status":status, "fix_function":fix_function,
                 "message": message, "tool_tip":tool_tip}
        data[export_type][group_name].append(new_node)
    with open(user_json_file, "w") as data_file:
        data_file.write(json.dumps(data, indent=4,
                                   sort_keys=True, separators=(',', ': ')))

def add_user_json_file(json_path=JSON_FILE, user_json_path=USER_JSON_FILE):
    """
    Can be used for resetting a file, or creating one if it doesn't exist
    """
    user_json_dir = os.path.dirname(user_json_path)
    if not os.path.isfile(json_path):
        mc.warning("%s file is missing" % json_path)
        return

    if not os.path.exists(user_json_dir):
        os.makedirs(user_json_dir)
    copyfile(json_path, user_json_path)

def write_checks_to_json(section_name, json_dict, json_file=USER_JSON_FILE):
    """
    Add a whole group of checks to the json file
    """
    with open(json_file, "r+") as data_file:
        data = json.load(data_file)
        data[section_name] = json_dict
    with open(json_file, "w") as data_file:
        data_file.write(json.dumps(data, indent=4,
                                   sort_keys=True, separators=(',', ': ')))

def optimize_json(json_dict):
    if isinstance(json_dict, dict):
        for key, value in json_dict.iteritems():
            optimize_json(value)
    elif isinstance(json_dict, list):
        remove_message_repetition(json_dict)

def remove_message_repetition(messages_list):
    for message_info in messages_list:
        if messages_list.count(message_info) > 1:
            remove_repetition_of_element(messages_list, message_info)

def remove_repetition_of_element(list, element):
    while list.count(element) > 1:
        list.remove(element)

def get_char_name():
    for char_name in CHARS.keys():
        if char_name in TOOLS_DIR:
            return char_name
    print "Could not find which project is the enviroment set to",
    return None

def get_anim_curves():
    anim_curves = mc.ls(type="animCurveTL") + \
                  mc.ls(type="animCurveTA") + \
                  mc.ls(type="animCurveTT") + \
                  mc.ls(type="animCurveTU") + \
                  mc.ls(type="animCurveUL") + \
                  mc.ls(type="animCurveUA") + \
                  mc.ls(type="animCurveUT") + \
                  mc.ls(type="animCurveUU")
    return anim_curves

