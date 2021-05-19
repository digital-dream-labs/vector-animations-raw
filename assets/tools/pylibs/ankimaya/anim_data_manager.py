
# The purpose of this class is to replace maya's baking for animation export.
# Instead of baking data_node, we are checking times where all ctrs have keys
# and populating animation data with values from data_node's attributes.


import maya.cmds as mc
from ankimaya import ctrs_manager, robot_data
import copy

# TODO: Move these constants into a constants.py file, from where they should
#       be imported here and in any other files where they are used.
HACK_TIMELINE_SCALE = 0.99
FLOAT_EQUALITY_TOLERANCE = 0.05

RED_MULTIPLIER = 1.0
GREEN_MULTIPLIER = 1.0
BLUE_MULTIPLIER = 1.0

NO_DRIVERS_MSG = "No drivers"

UNIT_CONVERSION_NODE = "unitConversion"

# iI the connection to an attribute hapens not through set driven keys specify what they are, so that
# they become a part of additional attributes

ADDITIONAL_ATTRS_CTRS = {"LeftEyeLightness":"x:mech_eye_L_ctrl.Lightness",
                           "RightEyeLightness":"x:mech_eye_R_ctrl.Lightness",
                           "LeftEyeGlowSize": "x:mech_eye_L_ctrl.GlowSize",
                           "RightEyeGlowSize": "x:mech_eye_R_ctrl.GlowSize"}

class AnimDataManager(object):

    def __init__(self, data_node, start_frame, end_frame, check_muted=True, full_setup=True):
        # TODO: have less functions being called in here, but rather use them when needed

        self.data_node = data_node
        self.messages_for_user = []
        self.movement_attrs = ["Radius", "Forward", "Turn"]
        self.event_ctrl = ctrs_manager.EVENT_CTR
        self.skip_objects = ["x:virtual_all_ctrl", self.event_ctrl]
        self.mech_all_ctr = "x:mech_all_ctrl"
        self.moac_ctr = "x:moac_ctrl"
        self.backpack_ctr = "x:backpack_ctrl"

        if check_muted:
            self.is_ctr_muted(self.event_ctrl)
            self.is_ctr_muted(self.mech_all_ctr)
            self.is_ctr_muted(self.backpack_ctr)

        self.data_attributes = mc.listAttr(self.data_node, userDefined=True, k=True)
        self.data_attrs_ctrs = {}
        self.muted_data_attrs_ctrs = {}
        self.populate_data_attrs_ctrs()
        self.movement_frames = []

        # Fix for when gets wrong start frame, but by very small amount
        # (bug originally found in 'anim_freeplay_reacttoface_identified' animation)
        self.start_frame = round(start_frame, 5)
        self.end_frame = end_frame

        if full_setup:
            self.keyed_frames = self.get_all_frames_on_ctrs(start_frame, end_frame)
            self.anim_data = self.get_anim_data() # [attr_name:{frame_num:value}]
        else:
            self.keyed_frames = None
            self.anim_data = None

    def is_ctr_muted(self, ctr_name):
        if ctrs_manager.is_ctr_muted(ctr_name):
            msg = "%s will not be exported (muted or no keyable attrs)" % ctr_name
            if msg not in self.messages_for_user:
                self.messages_for_user.append(msg)
            return True
        return False

    def is_attr_muted(self, attr_name):
        if mc.mute(attr_name, q=True):
            msg = "%s will not be exported (muted or no keyable attrs)" % attr_name
            if msg not in self.messages_for_user:
                self.messages_for_user.append(msg)
            return True
        return False

    def get_source_connections(self, fq_attr):
        try:
            connections = mc.listConnections(fq_attr, s=True, d=False)
        except ValueError:
            return None
        if connections:
            for connection in connections:
                if UNIT_CONVERSION_NODE in connection:
                    connections.remove(connection)
                    connections.extend(self.get_source_connections(connection))
        return connections

    def get_connection(self, fq_attr):
        connections = self.get_source_connections(fq_attr)
        for connection in connections:
            if mc.listAttr(connection, k=True):
                if not self.is_ctr_muted(connection):
                    # exclude ctrs that have muted attributes
                    return connection

    def populate_data_attrs_ctrs(self):
        """
        Populate a dict of data attributes and ctr names that are
        connected by set driven keys to those attrs.
        """
        for attr in self.data_attributes:
            fq_attr = self.data_node + "." + attr
            driver = mc.setDrivenKeyframe(fq_attr, driver=True, q=True)[0]
            if attr in ADDITIONAL_ATTRS_CTRS.keys():
                self.data_attrs_ctrs[attr] = ADDITIONAL_ATTRS_CTRS[attr]
            elif NO_DRIVERS_MSG in driver:
                continue
            else:
                # exclude ctrs that have muted attributes
                if self.is_attr_muted(driver):
                    self.muted_data_attrs_ctrs[attr] = driver
                else:
                    self.data_attrs_ctrs[attr] = driver

    def get_all_frames_on_ctrs(self, start_frame, end_frame):
        """
        Get times where all ctrs have been keyed.
        @return: list of frames of keys of all ctrs
        """
        dag_objects = mc.ls(dagObjects=True)
        all_keyed_times = self.get_frames_on_ctrs(dag_objects, start_frame, end_frame)
        try:
            all_keyed_times.sort()
        except AttributeError:
            pass
        reduced_keys = self.remove_multiple_close_keyframes(all_keyed_times)
        return reduced_keys

    def get_frames_on_ctrs(self, ctrs, start_frame, end_frame):
        """
        Get frames on ctrs and find if they are ctrs.
        """
        keyed_times = [start_frame]
        for ctr in ctrs:
            if ctr in self.skip_objects:
                continue
            object_times = mc.keyframe(ctr, query=True, timeChange=True,
                                       time=(start_frame, end_frame))
            try:
                if object_times.count(0.0) != len(object_times):
                    keyed_times.extend(object_times)
            except AttributeError:
                pass
        keyed_times.append(end_frame)
        all_keyed_times = list(set(keyed_times))
        return all_keyed_times

    def get_values_for_attr(self, data_attr, ctrl_attr, use_absolute_frames=False):
        """
        Get values of a specific attribute.
        @return: {frame_num:value}
        """
        frame_nums = mc.keyframe(ctrl_attr, query=True, timeChange=True,
                                 time=(self.start_frame, self.end_frame))
        if frame_nums is None:
            return {}
        fq_attr = self.data_node + "." + data_attr
        data_times_values = {}
        for frame_num in frame_nums:
            value = mc.getAttr(fq_attr, time=frame_num)
            if use_absolute_frames:
                data_times_values[frame_num] = value
            else:
                data_times_values[self.scale_frame(frame_num)] = value
        return data_times_values

    def get_anim_data(self, use_absolute_frames=False, face_only=False, data_dict=None):
        """
        Get a dictionary of all attributes and the {frame_num:value} dict that corresponds to them.
        @return: {"attr_name":{frame_num:value}}
        """
        anim_data = {}
        if data_dict is None:
            data_dict = copy.deepcopy(self.data_attrs_ctrs)
        for attr, ctrl_attr in data_dict.iteritems():
            if face_only and not robot_data.is_procedural_face_attr(attr):
                print("Skipping '%s' attribute in get_anim_data()" % attr)
                continue
            anim_data[attr] = self.get_values_for_attr(attr, ctrl_attr, use_absolute_frames)

        return anim_data

    def get_muted_anim_data(self, use_absolute_frames=False, face_only=False):
        muted_anim_data = self.get_anim_data(use_absolute_frames, face_only, self.muted_data_attrs_ctrs)
        return muted_anim_data

    def remove_close_keyframes(self, keyframes=[]):
        """
        Slightly modyfied from prevoius tool iteration.,
        This function assumes that the list of keyframes is sorted.
        """
        if keyframes == [] or keyframes == None:
            return []
        reduced_keyframes = []
        idx = 0
        while idx < len(keyframes):
            first = keyframes[idx]
            try:
                second = keyframes[idx + 1]
            except IndexError:
                reduced_keyframes.append(first)
                break
            if (second - first) < FLOAT_EQUALITY_TOLERANCE:
                # these two keyframes are the "same", so only use first
                reduced_keyframes.append(first)
                idx += 2
            else:
                reduced_keyframes.append(first)
                idx += 1
        return reduced_keyframes

    def remove_multiple_close_keyframes(self, keyframes):
        initial_keyframes = keyframes
        reduced_keyframes = []
        while True:
            reduced_keyframes = self.remove_close_keyframes(initial_keyframes)
            if reduced_keyframes == initial_keyframes:
                break
            initial_keyframes = reduced_keyframes
        return reduced_keyframes

    def get_mech_all_data(self, start_frame, end_frame):
        """
        Get values only for Radius, Forward, Turn where the movement ctr is keyed.
        @return: {frame:{attr:value}}
        """
        mech_data = {}
        mech_frames = self.get_frames_on_ctrs([self.mech_all_ctr], start_frame, end_frame)
        mech_frames.sort()
        mech_frames = self.remove_close_keyframes(mech_frames)
        self.movement_frames += mech_frames
        for frame_num in mech_frames:
            attr_value = {}
            for attr in self.movement_attrs:
                attr_value[attr] = mc.getAttr(self.data_node + "." + attr, time=frame_num)
            mech_data[frame_num] = attr_value
        return mech_data

    def get_reset_keys(self, start_frame, end_frame):
        """
        Gets keys where MState gets reset
        dict of frames and values for Radius, where M State changes and Forward, Turn are 0.
        @return: {frame_num:radius_value}
        """
        # find keys on moac_ctr
        # the ones where Forward and Turn are 0, are the ones where reset happened.
        moac_times = mc.keyframe(self.moac_ctr, query=True, timeChange=True,
                                 time=(start_frame, end_frame))
        try:
            moac_times.sort()
        except AttributeError:
            pass
        moac_times = self.remove_close_keyframes(moac_times)
        try:
            moac_times = list(set(moac_times))
        except TypeError:
            return {}
        self.movement_frames += moac_times
        try:
            self.movement_frames.sort()
        except AttributeError:
            pass
        self.movement_frames = self.remove_close_keyframes(self.movement_frames)
        reset_frame_radius_values = {}
        for frame_num in moac_times:
            turn_value = mc.getAttr(self.data_node + ".Turn", time=frame_num)
            fwd_value = mc.getAttr(self.data_node + ".Forward", time=frame_num)
            if turn_value == 0 and fwd_value == 0:
                reset_frame_radius_values[frame_num] = mc.getAttr(self.data_node + ".Radius",
                                                                  time=frame_num)
        return reset_frame_radius_values

    def get_move_data(self):
        """
        Get values of only movement ctrs.
        This is specific to how movement json gets generated.
        Hopefully can rewrite it so that all the json making modules behave in more simillar manner
        then won't need separate lists for different functions, but for now this is here.
        @return: [{attr_name:value,...,"Time":frame_num},...]
        """
        move_data = []
        reset_frame_radius_values = self.get_reset_keys(self.start_frame, self.end_frame)
        mech_data = self.get_mech_all_data(self.start_frame, self.end_frame)

        self.movement_frames = list(set(self.movement_frames))
        try:
            self.movement_frames.sort()
        except AttributeError:
            pass
        self.movement_frames = self.remove_close_keyframes(self.movement_frames)
        for frame in self.movement_frames:
            valid_keyframe = {"Forward": 0,
                              "Turn": 0,
                              "Radius": 0,
                              "Time": self.scale_frame(frame),
                              "Reset": False}
            if frame in reset_frame_radius_values.keys():
                valid_keyframe["Radius"] = round(reset_frame_radius_values[frame])
                valid_keyframe["Reset"] = True
                move_data.append(valid_keyframe)
            elif frame in mech_data.keys():
                attr_values = mech_data[frame]
                for attr in valid_keyframe.keys():
                    if attr in attr_values.keys():
                        valid_keyframe[attr] = round(attr_values[attr])
                move_data.append(valid_keyframe)
        return move_data

    def get_lights_data(self):
        """
        Analyses attributed of a data node that end with light - the first
        part of their name is the name of the side and the second is the color.
        @rtype: dict
        @return: {frame_num:{side:[rgb_values]}}
        """
        lights_data = {}

        color_index = dict(red=0, green=1, blue=2, brightness=0)
        color_offset = dict(red=RED_MULTIPLIER, green=GREEN_MULTIPLIER, blue=BLUE_MULTIPLIER,
                            brightness=RED_MULTIPLIER)


        try:
            backpack_frame_nums = mc.keyframe(self.backpack_ctr, query=True, timeChange=True,
                                          time=(self.start_frame, self.end_frame))
        except ValueError:
            return {}

        if backpack_frame_nums is None:
            return {}
        if self.start_frame not in backpack_frame_nums:
            backpack_frame_nums.insert(0, self.start_frame)
        if self.end_frame not in backpack_frame_nums:
            backpack_frame_nums.append(self.end_frame)

        backpack_frame_nums.sort()
        backpack_frame_nums = self.remove_multiple_close_keyframes(backpack_frame_nums)

        lights_attributes = self.get_lights_attributes()
        for frame_num in backpack_frame_nums:
            current_frame_data = {}
            for attribute in lights_attributes:
                attr_words = attribute.split("_")
                color = attr_words[1]
                side = attr_words[0]
                value = mc.getAttr(self.data_node + "." + attribute, time=frame_num)
                if value > 1.0:
                    value = 1.0
                elif value < 0.0:
                    value = 0.0
                if side not in current_frame_data.keys():
                    current_frame_data[side] = [0.0, 0.0, 0.0, 0.0]
                current_frame_data[side][color_index[color]] = value * color_offset[color]
                lights_data[self.scale_frame(frame_num)] = current_frame_data
        return lights_data

    def get_lights_attributes(self):
        lights_attributes = []
        for attribute in self.data_attributes:
            try:
                if attribute.split("_")[2] == "light":
                    lights_attributes.append(attribute)
            except IndexError:
                continue
        return lights_attributes

    def scale_frame(self, frame_num):
        return (frame_num - self.start_frame) * HACK_TIMELINE_SCALE
