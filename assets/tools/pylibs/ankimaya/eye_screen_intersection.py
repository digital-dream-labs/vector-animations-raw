import maya.cmds as mc
import ankimaya.coz2vic_anim_converter as coz2vic
reload(coz2vic)
import json
import os
import copy
from shutil import copyfile

# go through all frames
# check where verteces are comparing to their limits
# msg if they intersect the limit

# right and left from looking straight at the screen (left value is lower than right)
# TOP_R_SCREEN_VTX = "x:screenEdge_geo.vtx[1]"
# BTTM_L_SCREEN_VTX = "x:screenEdge_geo.vtx[16]"

R_TOP_SCREEN_LOC = ["x:r_top_screenEdge_loc","x:r_top_originalScreenEdge_loc"]
L_BTTM_SCREEN_LOC = ["x:l_bttm_screenEdge_loc", "x:l_bttm_originalScreenEdge_loc"]

L_TOP_EYE_LOC = "x:l_top_eyeEdge_loc"
L_EYE_LOC = "x:l_eyeEdge_loc"
L_BTTM_EYE_LOC = "x:l_bttm_eyeEdge_loc"
R_TOP_EYE_LOC = "x:r_top_eyeEdge_loc"
R_BTTM_EYE_LOC = "x:r_bttm_eyeEdge_loc"
R_EYE_LOC = "x:r_eyeEdge_loc"

TOP_BLINK_LOCS = ["x:l_top_eyeBlink_loc","x:r_top_eyeBlink_loc"]
BTTM_BLINK_LOCS = ["x:r_bttm_eyeBlink_loc", "x:l_bttm_eyeBlink_loc"]

#BTTM_BLINK_LIMIT = 0.2
#TOP_BLINK_LIMIT = -0.2

BLINK_DISTANCE=0.4

EYE_L_GEO = "x:eye_L_geo"
EYE_R_GEO = "x:eye_R_geo"

TOP_LID_CTRS = ['x:mech_upperLid_R_ctrl', 'x:mech_upperLid_L_ctrl']
BTTM_LID_CTRS = ['x:mech_lwrLid_R_ctrl', 'x:mech_lwrLid_L_ctrl']

VTX_INFO = {"vertex_name": "",
            "overshoot_value": 0.0,
            "overshoot_type": ""}

LOCATOR_INFO = {"locator_name": "",
                "overshoot_value": 0.0,
                "overshoot_type": ""}

TOP_EYE_LOCATORS = [L_TOP_EYE_LOC, R_TOP_EYE_LOC]
BTTM_EYE_LOCATORS = [L_BTTM_EYE_LOC, R_BTTM_EYE_LOC]

PROBLEM_FRAMES = {0.0:[]} # frame_num:[vtx_info, ...]

home_dir = os.getenv("HOME")
JSON_EXPORT_PATH = os.path.join(home_dir,".anki","maya","eye_intersection_data", "all")
JSON_EXPORT_PATH_EXCLUDING_BLINKS = os.path.join(home_dir,".anki","maya","eye_intersection_data", "excluding_blinks")
JSON_EXPORT_PATH_RED_FLAGED = os.path.join(home_dir,".anki","maya","eye_intersection_data", "red_flaged")

ANIM_PATH = os.path.join(home_dir, "workspace","victor-animation","scenes")

EYE_CTRS = ["x:mech_eyes_all_ctrl",
            "x:mech_eye_R_ctrl",
            "x:mech_eye_L_ctrl",
            "x:eyeCorner_R_OuterTop_ctrl",
            "x:eyeCorner_R_innerTop_ctrl",
            "x:eyeCorner_R_OuterBtm_ctrl",
            "x:eyeCorner_R_innerBtm_ctrl",
            "x:eyeCorner_L_OuterBtm_ctrl",
            "x:eyeCorner_L_OuterTop_ctrl",
            "x:eyeCorner_L_innerTop_ctrl",
            "x:eyeCorner_L_innerBtm_ctrl",
            "x:mech_lwrLid_L_ctrl",
            "x:mech_lwrLid_R_ctrl",
            "x:mech_upperLid_R_ctrl",
            "x:mech_upperLid_L_ctrl"]

class EyeScreenIntersection(object):

    def __init__(self):
        self.problem_locators = []
        self.problem_no_blinks_locators = []
        self.red_flagged_problems = []
        self.current_frame = mc.currentTime(q=True)

    def checkLimits(self,
                    top_treshold=0.0,
                    bttm_treshold=0.0,
                    left_treshold=0.0,
                    right_treshold=0.0):

        # the position of these points might change depending on the position of the head, body, etc.
        # that"s why check their position here and not on init
        self.screen_top_limit_ys = [mc.xform(R_TOP_SCREEN_LOC[0], q=True, t=True, a=True, ws=True)[1],
                                    mc.xform(R_TOP_SCREEN_LOC[1], q=True, t=True, a=True, ws=True)[1]]

        self.screen_bttm_limit_ys = [mc.xform(L_BTTM_SCREEN_LOC[0], q=True, t=True, a=True, ws=True)[1],
                                     mc.xform(L_BTTM_SCREEN_LOC[1], q=True, t=True, a=True, ws=True)[1]]

        self.screen_left_limit_xs = [mc.xform(L_BTTM_SCREEN_LOC[0], q=True, t=True, a=True, ws=True)[0],
                                     mc.xform(L_BTTM_SCREEN_LOC[1], q=True, t=True, a=True, ws=True)[0]]

        self.screen_right_limit_xs = [mc.xform(R_TOP_SCREEN_LOC[0], q=True, t=True, a=True, ws=True)[0],
                                      mc.xform(R_TOP_SCREEN_LOC[1], q=True, t=True, a=True, ws=True)[0]]

        self.eye_ys = [mc.xform(R_TOP_EYE_LOC, q=True, t=True, a=True, ws=True)[1],
                       mc.xform(L_TOP_EYE_LOC, q=True, t=True, a=True, ws=True)[1]]

        # user has ability to add a treshhold to see if eyes are close to the edge of the screen
        top_limits = [self.screen_top_limit_ys[0] - top_treshold,
                      self.screen_top_limit_ys[1] - top_treshold]
        bttm_limits = [self.screen_bttm_limit_ys[1] + bttm_treshold,
                       self.screen_bttm_limit_ys[1] + bttm_treshold]
        left_limits = [self.screen_left_limit_xs[0] + left_treshold,
                       self.screen_left_limit_xs[1] + left_treshold]
        right_limits = [self.screen_right_limit_xs[0] - right_treshold,
                        self.screen_right_limit_xs[1] - right_treshold]

        for top_limit in  self.screen_top_limit_ys:
            for locator in TOP_EYE_LOCATORS:
                current_pos = mc.xform(locator, q=True, t=True, ws=True)
                if current_pos[1] > top_limit:
                    problem_loc_info = self.add_to_json(locator, (current_pos[1] - top_limit), "top")
                    self.problem_no_blinks_locators.append(copy.deepcopy(problem_loc_info))
                    if not self.are_upper_lid_values():
                        self.red_flagged_problems.append(copy.deepcopy(problem_loc_info))

        for bttm_limit in self.screen_bttm_limit_ys:
            for locator in BTTM_EYE_LOCATORS:
                current_pos = mc.xform(locator, q=True, t=True, ws=True)
                if current_pos[1] < bttm_limit:
                    problem_loc_info = self.add_to_json(locator, (bttm_limit-current_pos[1]), "bottom")
                    self.problem_no_blinks_locators.append(copy.deepcopy(problem_loc_info))
                    if not self.are_lower_lid_values():
                        self.red_flagged_problems.append(copy.deepcopy(problem_loc_info))

        current_pos = mc.xform(L_EYE_LOC, q=True, t=True, ws=True)
        for left_limit in self.screen_left_limit_xs:
            if current_pos[0] < left_limit:
                # print "current_pos[0] ", current_pos[0]
                # print "left_limit ", left_limit
                problem_loc_info = self.add_to_json(L_EYE_LOC, (left_limit - current_pos[0]), "left")
                if not self.is_blink():
                    self.problem_no_blinks_locators.append(copy.deepcopy(problem_loc_info))

        current_pos = mc.xform(R_EYE_LOC, q=True, t=True, ws=True)
        for right_limit in self.screen_right_limit_xs:
            if current_pos[0] > right_limit:
                problem_loc_info = self.add_to_json(R_EYE_LOC,(current_pos[0] - right_limit), "right")
                if not self.is_blink():
                    self.problem_no_blinks_locators.append(copy.deepcopy(problem_loc_info))

    def are_upper_lid_values(self):
        for ctr in TOP_LID_CTRS:
            if self.are_ctr_values(ctr):
                return True
        return False

    def are_lower_lid_values(self):
        for ctr in BTTM_LID_CTRS:
            if self.are_ctr_values(ctr):
                return True
        return False

    def are_ctr_values(self, ctr):
        mc.currentTime(self.current_frame)
        ctr_attrs = mc.listAttr(ctr, k=True)
        for attr in ctr_attrs:
            # print mc.getAttr(ctr+"."+attr, time = self.current_frame)
            if mc.getAttr(ctr+"."+attr, time = self.current_frame)!=0\
                    and mc.getAttr(ctr+"."+attr, time = self.current_frame)!=1:
                return True
        return False

    def is_blink(self):
        top_blink_positions = [mc.xform(TOP_BLINK_LOCS[0], q=True, t=True, ws=True)[0],
                               mc.xform(TOP_BLINK_LOCS[1], q=True, t=True, ws=True)[1]]
        bttm_blink_positions = [mc.xform(BTTM_BLINK_LOCS[0], q=True, t=True, ws=True)[0],
                               mc.xform(BTTM_BLINK_LOCS[1], q=True, t=True, ws=True)[1]]
        for i in range (len(top_blink_positions)):
            if (top_blink_positions[i]-bttm_blink_positions[i])<BLINK_DISTANCE:
                # print "top_blink_positions[i]-bttm_blink_positions[i] ", (top_blink_positions[i]-bttm_blink_positions[i])
                continue
            else:
                return False
        return True

    def add_to_json(self, locator_name, overshoot_value, type):
        problem_vtx = copy.deepcopy(LOCATOR_INFO)
        problem_vtx["locator_name"] = locator_name
        problem_vtx["overshoot_value"] = overshoot_value
        problem_vtx["overshoot_type"] = type
        self.problem_locators.append(problem_vtx)
        return problem_vtx

    def get_problem_frames(self):

        problem_frames_dict = {}
        no_blink_frames_dict = {}
        red_flaged_frames_dict = {}

        frames = []
        for ctr in EYE_CTRS:
            try:
                frames += (mc.keyframe(ctr, query=True, timeChange=True))
            except Exception:
                continue

        key_frames = list(set(frames))
        key_frames.sort()

        for frame in key_frames:
            self.current_frame = frame
            mc.currentTime(frame)
            self.problem_locators = []
            self.problem_no_blinks_locators = []
            self.red_flagged_problems = []

            self.checkLimits()

            if self.problem_locators:
                problem_frames_dict[frame] = self.problem_locators
            if self.problem_no_blinks_locators:
                no_blink_frames_dict[frame] = self.problem_no_blinks_locators
            if self.red_flagged_problems:
                red_flaged_frames_dict[frame] = self.red_flagged_problems

        return problem_frames_dict, no_blink_frames_dict, red_flaged_frames_dict

    def generate_problem_msg(self):

        problem_frames_dict, no_blink_frames_dict, red_flaged_frames_dict  = copy.deepcopy(self.get_problem_frames())
        print ("Eyes are overlaping screen on frames: \n")
        for frame, self.problem_locators in problem_frames_dict.iteritems():
            # print "\n"
            # print frame
            print (self.problem_locators)

    def generate_intersection_json(self, file_name, path, problem_dict):
        problem_frames_dict = copy.deepcopy(problem_dict)
        if problem_frames_dict == {} or problem_frames_dict==None:
            return
        json_dict = {file_name: problem_frames_dict}
        output_json = json.dumps(json_dict, sort_keys=False, indent=2, separators=(",", ": "))
        if not os.path.exists(path):
            os.makedirs(path)
        #print os.path.join(path.split("/"), os.path.basename(file_name) + ".json")
        json_filename = os.path.join(path, file_name + ".json")
        with open(json_filename, "w") as fh:
            fh.write(output_json)
        print "Output json: "
        print json_filename
        return output_json

    def generate_jsons(self, file_name):
        problem_frames_dict, no_blink_frames_dict, red_flaged_frames_dict = self.get_problem_frames()
        self.generate_intersection_json(file_name, JSON_EXPORT_PATH, problem_frames_dict)
        self.generate_intersection_json(file_name, JSON_EXPORT_PATH_EXCLUDING_BLINKS, no_blink_frames_dict)
        self.generate_intersection_json(file_name, JSON_EXPORT_PATH_RED_FLAGED, red_flaged_frames_dict)

def generate_jsons_for_multiple_files(ma_files):
    file_num = 0
    for ma_file in ma_files:
        file_num+=1
        print "\nfile %s of %s\n" %(file_num, len(ma_files))
        try:
            mc.file(ma_file, force=True, open=True)
            # file ("/Users/dariajerjomina/workspace/victor-animation/assets/rigs/Victor_rig_01.ma",
            #       loadReference="xRN", type="mayaAscii")
            mc.file("/Users/dariajerjomina/workspace/victor-animation/assets/rigs/Victor_rig_01.ma", loadReference="xRN")

            eye_screen_intersection = EyeScreenIntersection()
            try:
                eye_screen_intersection.generate_jsons(os.path.basename(ma_file)[:-3])
            except Exception:
                print "Could not generate intersection json for %s" % ma_file
            # try:
            #output_json = eye_screen_intersection.generate_intersection_json(os.path.basename(ma_file))
            # except Exception:
            #     print "Could not generate intersection json for %s" % ma_file
        except Exception:
            print "\n\nCould not analyze %s\n\n" %(ma_file)

def check_for_blink():
    # if verteces on the edges of the eyes are intersecting both sides of the screen
    pass

def get_maya_files(path=ANIM_PATH):
    # walk through dirs recursively and look for .ma files
    ma_files = []
    for (dirpath, dirnames, filenames) in os.walk(path):
        for i in range(len(filenames)):
            if isinstance(filenames[i], str):
                if filenames[i].endswith(".ma"):
                    ma_files.append(os.path.join(dirpath, filenames[i]))

    generate_jsons_for_multiple_files(ma_files)
    #return ma_files


def generate_used_file_names(anim_groups_path = "/Users/dariajerjomina/workspace/victor-animation-assets/trunk/animations"):
    used_file_names = []
    for file_name in os.listdir(anim_groups_path):
        base_file_name = os.path.splitext(file_name)[0]
        used_file_names.append(base_file_name)
    return used_file_names


def filter_used_anims(path, destination_path, anim_groups_path = "/Users/dariajerjomina/workspace/victor-animation-assets/trunk/animations"):
    used_anim_names = generate_used_file_names(anim_groups_path=anim_groups_path)
    for (dirpath, dirnames, file_names) in os.walk(path):
        for file_name in file_names:
            #print "file_name ", file_name
            if os.path.splitext(file_name)[0] in used_anim_names:
                print file_name
                original_file = os.path.join(dirpath, file_name)
                copy_file = os.path.join(destination_path, file_name)
                copyfile(original_file, copy_file)