#!/usr/bin/env python

CUTOFF_DAY = 30

USER = "dariajerjomina"


# old_aniamtion_finder.py finds unused, old animations. It checks for clips in forms of
# json files inside cozmo-assets/trunk/animations and finds the ones that are not being used
# insed anim groups json files.
# It also checks for animation groups that are not being used in AnimationTriggerMap.json and
# thus have no corresponding CLAD events.

# daria.jerjomina@anki.com
# 09/08/2016


import tarfile
import os
import json
import time
from datetime import datetime, timedelta
import anim_groups


# For timestamps
#
# print "last modified: %s" % time.ctime(os.path.getmtime(
# self.anim_clips_path+"/"+tar_file))
# print "created: %s" % time.ctime(
# os.path.getctime(os.path.getmtime(self.anim_clips_path+"/"+tar_file)))


class AnimationFinder:

    def __init__(self):
        self.anim_clips_path = "/Users/%s/workspace/cozmo-assets/trunk/animations" % USER
        self.anim_groups_path = "/Users/%s/workspace/cozmo-assets/trunk/animationGroups" % USER
        self.anim_trigger_map_path = \
            "/Users/%s/workspace_git/cozmo-one/lib/anki/products-cozmo-assets" \
            "/animationGroupMaps/AnimationTriggerMap.json" % USER

        self.ungrouped_clips = []  # clips that are not in animation groups
        self.no_event_animgroups_clips = {}  # anim groups that are not in AnimationTriggerMap
        self.tars_clips = {} #{tar_to_delete:[clips]}
        self.old_clips = []
        self.new_clips = []
        self.old_clips_unused = []
        self.new_clips_unused = []
        self.old_anim_groups = []
        self.new_anim_groups = []

        self.all_clip_names = []
        self.grouped_clips = []
        self.anim_groups_names_paths = {}
        self.anim_group_names = []
        self.anim_groups_with_events = []
        self.unused_tars = []
        self.untared_clips = []
        self.unused_untared_clips = []

        self.some_days_ago = datetime.now() - timedelta(days=CUTOFF_DAY)

    def main(self):
        self.find_all_clips()
        # self.all_clip_names = self.get_all_clips()
        self.grouped_clips = self.get_grouped_clips(self.anim_groups_path)
        self.ungrouped_clips = self.get_ungrouped_clips()

        self.anim_groups_with_events = self.get_event_anim_groups()
        self.find_no_event_animgroups()
        self.find_unused_tars()

        self.output_animation_info()

    def find_all_clips(self):
        """
        All names of all the json files inside animation folder and
        """
        # clip_names=[]
        for file_in_question in os.listdir(self.anim_clips_path):
            if file_in_question[-5:] == ".json":
                self.all_clip_names.append(file_in_question[:-5])
                self.untared_clips.append(file_in_question[:-5])
            elif file_in_question[-4:] == ".tar":
                last_modyfied = datetime.fromtimestamp(os.path.getctime(self.anim_clips_path + "/" + file_in_question))
                self.tars_clips[self.anim_clips_path + "/" + file_in_question] = []
                files_in_tar = get_files_in_tar(self.anim_clips_path+"/"+file_in_question)
                for file_name in files_in_tar:
                    self.tars_clips[self.anim_clips_path + "/" + file_in_question].append(file_name[:-5])
                    if file_name[-5:] == ".json":
                        self.all_clip_names.append(file_name[:-5])
                        if last_modyfied < self.some_days_ago:
                            # print ("%s was last modyfied %s, before %s" %(
                            #     file_in_question,last_modyfied, self.some_days_ago))
                            self.old_clips.append(file_name[:-5])
                        else:
                            self.new_clips.append(file_name[:-5])

    def find_unused_tars(self):
        for tar, clip_list in self.tars_clips.iteritems():
            if self.are_clips_used(clip_list):
                self.unused_tars.append(tar)
        self.unused_tars.sort()

    def are_clips_used(self, clips):
        for clip in clips:
            if clip not in self.old_clips_unused:
                return False
        return True

    def find_unused_untared_clips(self):
        for clip in self.old_clips_unused:
            if clip not in self.tars_clips.values:
                self.unused_untared_clips.append(clip)

    def get_ungrouped_clips(self):
        """
        Populates ungrouped_clips - all files in animations directory that are not mentioned in
        animgroups
        """
        ungrouped_clips = []
        for clip_name in self.all_clip_names:
            if clip_name not in self.grouped_clips:
                ungrouped_clips.append(clip_name)
                if clip_name in self.old_clips:
                    self.old_clips_unused.append(clip_name)
                elif clip_name in self.new_clips:
                    self.new_clips_unused.append(clip_name)

        return ungrouped_clips

    def get_grouped_clips(self, dir_path):
        """
        Finds all clips mentioned in animgroups
        """
        grouped_clips = []
        for anim_group_file in os.listdir(dir_path):
            if anim_group_file[-5:] == ".json":
                self.anim_group_names.append(anim_group_file[:-5])
                self.anim_groups_names_paths[anim_group_file[:-5]] = dir_path+"/"+anim_group_file
                with open(dir_path+"/"+anim_group_file) as data_file:
                    try:
                        data = json.load(data_file)
                        for anim_node in data["Animations"]:
                            grouped_clips.append(anim_node["Name"])
                    except ValueError:
                        print "could not parse: %s" %(dir_path+"/"+anim_group_file)
            # If directory, continue recursively
            elif os.path.isdir(dir_path+"/"+anim_group_file):
                grouped_clips += (self.get_grouped_clips(dir_path+"/"+anim_group_file))
        return grouped_clips

    def find_no_event_animgroups(self):
        for anim_group in self.anim_group_names:
            if anim_group not in self.anim_groups_with_events:
                self.no_event_animgroups_clips[anim_group] = \
                    anim_groups.get_clips_in_anim_group(self.anim_groups_names_paths[anim_group])

                last_modyfied = datetime.fromtimestamp(
                    os.path.getctime(self.anim_groups_names_paths[anim_group]))
                if last_modyfied < self.some_days_ago:
                    self.old_anim_groups.append(anim_group)
                else:
                    self.new_anim_groups.append(anim_group)

    def get_event_anim_groups(self):
        event_anim_groups = []
        with open(self.anim_trigger_map_path) as data_file:
            data = json.load(data_file)
            for anim_node in data["Pairs"]:
                event_anim_groups.append(anim_node["AnimName"])
        return event_anim_groups

    def output_animation_info(self):

        # if self.ungrouped_clips is not None:
        #     print os.linesep + "The following animation clips have not been added to anim groups:" + os.linesep
        #     print(os.linesep.join(self.ungrouped_clips))
        # else:
        #     print "All clips are in anim groups"

        print(os.linesep + "The following animation clips have not been added to anim groups:")

        print(os.linesep + "These clips were created more than %s days ago:" % CUTOFF_DAY)
        print(os.linesep + os.linesep.join(self.old_clips_unused))

        print(os.linesep + "These clips were created less than %s days ago:" % CUTOFF_DAY)
        print(os.linesep + os.linesep.join(self.new_clips_unused))

        print(os.linesep + "Old tars with clips that are not being used in anim groups:")
        print(os.linesep + os.linesep.join(self.unused_tars))

        # if self.no_event_animgroups_clips is not None:
        #     print os.linesep + "The following animation groups have no corresponding clad events:" + os.linesep
        #     for anim_group, clips in self.no_event_animgroups_clips.iteritems():
        #         # in case need to know clips
        #         # print os.linesep + "Anim Group: %s" %(anim_group)
        #         # print "Clips:\n\t"+("\n\t".join(self.ungrouped_clips))
        #         print anim_group

        # print(os.linesep + "The following animation groups have no corresponding clad events:" + os.linesep)
        #
        # print(os.linesep + "These anim groups were created more than %s days ago:" % CUTOFF_DAY)
        # print(os.linesep + os.linesep.join(self.old_anim_groups))
        #
        # print(os.linesep + "These anim groups were created less than %s days ago:" % CUTOFF_DAY)
        # print(os.linesep + os.linesep.join(self.new_anim_groups))

        print(os.linesep + "There are %s clips overall" % len(self.all_clip_names))
        print("%s clips are not used" % len(self.ungrouped_clips))
        print("%s clips are not inside tar files and %s of them are unused"
              % (len(self.untared_clips), len(self.unused_untared_clips)))
        # print("%s of them are old clips" % len(self.old_clips_unused))
        # print("%s of them are new clips" % len(self.new_clips_unused))

        print(os.linesep + "There are %s tar files that have old clips which are not used in anim groups"
              % len(self.unused_tars) + os.linesep)


def get_files_in_tar(path_to_tar):
    tar = tarfile.open(path_to_tar)
    tar_kids = tar.getnames()
    return tar_kids


if __name__ == "__main__":
    animation_finder = AnimationFinder()
    animation_finder.main()


