"""
Copy animation from all ctrs in a specified clip and paste it to
a different time range (used by copy_anim_clip_ui.py)
"""

import os
import maya.cmds as mc
from maya import mel
from ankimaya import ctrs_manager
from ankimaya import audio_core
from ankimaya import game_exporter
from game_exporter import GAME_EXPORTER_PRESET
from anim_clip_utils import is_there_intersecting_clip, get_anim_clips, find_clip_num_from_name

DEFAULT_NAME_SUFFIX = "_copy"
CLIP_NAME_KEY = "clip_name"
VIC_REF = "vic_ref_xVictor"

TOOLS_DIR = os.getenv("ANKI_TOOLS")
SVN_ROOT_DIR = os.path.dirname(TOOLS_DIR)
GAME_EXPORTER_TEMPLATE_PATH = os.path.join(SVN_ROOT_DIR, "assets", "templates", "gameExporterPreset.ma")
ANIM_SCENES_PATH = os.path.join(SVN_ROOT_DIR, "scenes", "anim")

CUT_KEYS_CONFIRMATION_TEXT = "There are already animation keys in the segment where the frames are" \
                             " going to be pasted. Continue will result in removing those frames"

SAVE_CONFIRMATION_TEXT = "There are unsaved changes in this file. Continue will result in losing those changes."

CONTINUE = "Continue"
CANCEL = "Cancel"


def clip_error_check():
    """
    Returns true if there are errors.
    """
    error_msg = "No animation clips!"
    if not mc.objExists(GAME_EXPORTER_PRESET):
        print(error_msg),
        return True
    if not mc.attributeQuery("ac", n=GAME_EXPORTER_PRESET, exists=True):
        print(error_msg),
        return True
    return False


def are_unsaved_changes():
    return mc.file(q=True, modified=True)


def are_intersecting_keys(start_frame, end_frame, ctrs):
    for ctr in ctrs:
        if mc.keyframe(ctr, q=True, keyframeCount=True, time=(start_frame, end_frame)) > 0:
            return True
    return False


class ClipDuplicator(object):
    def __init__(self, extra_ctrs=[audio_core.AUDIO_NODE_NAME, ctrs_manager.EVENT_CTR]):
        self.original_clips = []
        self.ctr_keys_info = {} #{"node_name":["ctr_name",[],[]]}
        if clip_error_check():
            return
        self.ctrs = ctrs_manager.get_all_connected_ctrs()
        for ctr in extra_ctrs:
            if mc.objExists(ctr):
                self.ctrs.append(ctr)
        self.find_clips()

    def add_anim_clip(self, original_name, new_clip_name, copy_to_frame):
        """
        Copy original clip, change it's start and end frames.
        """
        if clip_error_check():
            return False

        clips_num = mc.getAttr(GAME_EXPORTER_PRESET + '.ac', size=True)

        original_clip_idx = find_clip_num_from_name(original_name)
        if self.is_name_error(original_name, original_clip_idx):
            return False
        # default name is the same as the copied clip but with "_copy" at the end
        if not new_clip_name:
            new_clip_name = original_name + DEFAULT_NAME_SUFFIX
        if new_clip_name in get_anim_clips():
            mc.warning("The '%s' animation clip already exists" % new_clip_name)
            return False

        # Getting original and new clip values
        clip_start_frame, clip_end_frame, clip_duration = self.get_clip_values(original_clip_idx)

        # Copied clip needs to go at the end of existing clips
        last_clip_num = clips_num - 1

        if copy_to_frame is None:
            last_clip_end_frame = mc.getAttr("%s.ac[%s].ace" % (GAME_EXPORTER_PRESET, last_clip_num))
            copy_to_frame = last_clip_end_frame + 1

        new_end_frame = copy_to_frame + clip_duration

        # Don't copy a clip if it intersects an existing clip
        intersecting_clip = is_there_intersecting_clip(copy_to_frame, new_end_frame)
        if intersecting_clip:
            mc.warning("Pasting would result in clip intersection with %s" % (intersecting_clip))
            return False

        confirm_msg = CONTINUE
        if are_intersecting_keys(start_frame=copy_to_frame, end_frame=new_end_frame, ctrs=self.ctrs):
            confirm_msg = mc.confirmDialog(title="Remove existing keys between frame %s and %s" %
                                                 (copy_to_frame, new_end_frame),
                                           message=CUT_KEYS_CONFIRMATION_TEXT,
                                           button=[CONTINUE, CANCEL], defaultButton=CONTINUE,
                                           cancelButton=CANCEL, dismissString=CANCEL)

        if confirm_msg == CONTINUE:
            # Main functionality
            self.copy_ctrs_animation(copy_start = clip_start_frame,
                                     copy_end = clip_end_frame,
                                     paste_start = copy_to_frame,
                                     paste_end = new_end_frame)

            game_exporter.add_anim_clip(clip_name = new_clip_name,
                                        start_frame = copy_to_frame,
                                        end_frame = new_end_frame,
                                        clip_num = last_clip_num+1)

            print("Created '%s' animation clip (frame range = %s to %s)"
                  % (new_clip_name, copy_to_frame, new_end_frame)),
            return True
        else:
            print("No animation was copied and no clips were created"),
            return False

    def get_clip_values(self, original_clip_idx):
        if not isinstance(original_clip_idx, int):
            return None
        clip_start_frame = mc.getAttr(GAME_EXPORTER_PRESET + '.ac[%s].acs' % original_clip_idx)
        clip_end_frame = mc.getAttr("%s.ac[%s].ace" % (GAME_EXPORTER_PRESET, original_clip_idx))
        clip_duration = clip_end_frame - clip_start_frame
        return clip_start_frame, clip_end_frame, clip_duration

    def copy_to_new_file(self, file_name="untitled", original_clip_name="", new_clip_name=""):
        if clip_error_check():
            return
        confirm_msg = CONTINUE
        if are_unsaved_changes():
            confirm_msg = mc.confirmDialog(
                title="Unsaved changes",
                message=SAVE_CONFIRMATION_TEXT,
                button=[CONTINUE, CANCEL], defaultButton=CANCEL,
                cancelButton=CANCEL, dismissString=CANCEL)

        if confirm_msg == CONTINUE:
            # Main functionality
            original_clip_idx = find_clip_num_from_name(original_clip_name)
            if not isinstance(original_clip_idx, int):
                print "Unable to find original clip",
                return
            clip_start_frame, clip_end_frame, clip_duration = self.get_clip_values(original_clip_idx)
            self.custom_copy(clip_start_frame,clip_end_frame)
            if not new_clip_name:
                new_clip_name = original_clip_name + DEFAULT_NAME_SUFFIX
            mc.file(force=True, new=True)
            mel.eval(VIC_REF)
            mc.file(GAME_EXPORTER_TEMPLATE_PATH, i=True)
            self.custom_paste()
            if file_name:
                if not file_name.startswith(os.sep):
                    file_name = os.path.join(ANIM_SCENES_PATH, file_name)
                mc.file(rename=file_name)
                mc.file(save=True, type="mayaAscii")
            game_exporter.add_anim_clip(new_clip_name, 0.0, clip_duration,0)

    def is_name_error(self, original_name, clip_num):
        if clip_num is None:
            print("Please insert the name of the clip"),
            return True
        if original_name != self.original_clips[clip_num]:
            print("%s should be %s" % (original_name, self.original_clips[clip_num])),
            return True
        return False

    def get_last_frame(self, clip_type="original"):
        clip_num = 0
        if clip_type == "original":
            clip_num = len(self.original_clips)
            if clip_num == 0:
                mc.error("there are no original clips!")
        return mc.getAttr("%s.ac[%s].ace" % (GAME_EXPORTER_PRESET, (clip_num - 1)))

    def copy_ctrs_animation(self, copy_start, copy_end, paste_start, paste_end):
        for ctr in self.ctrs:
            if mc.keyframe(ctr, q=True, keyframeCount=True, time=(copy_start, copy_end))>0:
                mc.cutKey(ctr, time=(paste_start, paste_end))
                mc.copyKey(ctr, time=(copy_start, copy_end), option="curve")
                mc.pasteKey(ctr, time=(paste_start, paste_end), option="replace") # without replace it moves the following keys

    def custom_copy(self, copy_start, copy_end):
        """
        Maya's copyKey doesn't seem to work when copying between scenes,
        This function goes through the keys and stores their values
        """
        for ctr in self.ctrs:
            attrs = mc.listAttr(ctr,k=True)
            for attr in attrs:
                vs = mc.keyframe(ctr,
                                 attribute=attr,
                                 query=True,
                                 valueChange=True,
                                 time=(copy_start, copy_end))
                ts = mc.keyframe(ctr,
                                 attribute=attr,
                                 query=True,
                                 timeChange=True,
                                 time=(copy_start, copy_end))
                self.ctr_keys_info["%s_%s" %(ctr.split(":")[1], attr)] = [ctr, vs,ts]

    def custom_paste(self):
        """
        Go through the keys and paste values that got from copying
        """
        if audio_core.AUDIO_NODE_NAME in self.ctrs and not mc.objExists(audio_core.AUDIO_NODE_NAME):
            audio_core.setupAudioNode([])

        # Find the lowest key value to serve as an offset when need to move keys in the beginning
        # of the clip
        all_values = []
        for values in self.ctr_keys_info.values():
            if values[2]:
                all_values += values[2]
        key_offset=min(all_values)

        for anim_curve, values_times in self.ctr_keys_info.iteritems():
            ctr = values_times[0]
            key_values = values_times[1]
            key_times = values_times[2]
            if key_times and key_values:
                for i in range(len(key_times)):
                    if not mc.objExists(anim_curve):
                        mc.setKeyframe(ctr, time=key_times[i]-key_offset)
                    try:
                        mc.setKeyframe(anim_curve, time=key_times[i]-key_offset, value=key_values[i])
                    except StandardError:
                        print("Skipping %s" % anim_curve)

    def find_clips(self):
        """
        Populates original_clips
        """
        last_original_clip_num = -1
        clips_num = mc.getAttr(GAME_EXPORTER_PRESET + '.ac', size=True)
        for num in range(0, clips_num):
            clip_name = mc.getAttr(GAME_EXPORTER_PRESET + '.ac[%s].acn' % num)
            self.original_clips.append(clip_name)


