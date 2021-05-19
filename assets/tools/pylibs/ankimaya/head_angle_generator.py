
# Duplicates animation three times on one timeline with modified head angle and creates
# related animation clips.


# TODO: place these in a separate file
HEAD_ANGLES = [-40, -20, 20]


import maya.cmds as mc
from ankimaya import ctrs_manager
from ankimaya import audio_core


class HeadAngleGenerator(object):
    def __init__(self):
        self.head_angle_clips = []
        self.original_clips = []
        self.ctrs = []
        self.place_side_keys = True
        self.last_key_steped = False

    def main(self):
        if not self.find_clips():
            return
        self.ctrs = ctrs_manager.get_all_connected_ctrs()
        self.remove_extra_animation()
        if mc.objExists(audio_core.AUDIO_NODE_NAME):
            self.ctrs.append(audio_core.AUDIO_NODE_NAME)
        if clip_error_check():
            return
        last_frame = self.add_anim_clips()
        mc.playbackOptions(maxTime=last_frame)

    def add_anim_clips(self):
        """
        Copy original clip, change it's start and end frames.
        """
        original_num_clips = len(self.original_clips)
        clip_end_frame = 0

        # TODO: find clips that are selected and only use those
        for clip_num in range(original_num_clips):
            original_name = mc.getAttr(ctrs_manager.GAME_EXPORTER_PRESET + '.ac[%s].acn' % clip_num)
            if self.is_name_error(original_name, clip_num):
                return
            last_clip_num = original_num_clips - 1 + len(HEAD_ANGLES) * clip_num
            clip_start_frame = mc.getAttr(ctrs_manager.GAME_EXPORTER_PRESET + '.ac[%s].acs' % clip_num)
            clip_end_frame = mc.getAttr("%s.ac[%s].ace" % (ctrs_manager.GAME_EXPORTER_PRESET,
                                                           clip_num))
            clip_duration = clip_end_frame - clip_start_frame
            last_clip_end_frame = mc.getAttr("%s.ac[%s].ace" % (ctrs_manager.GAME_EXPORTER_PRESET,
                                                                last_clip_num))

            if self.place_side_keys:
                self.add_side_keys(clip_start_frame, clip_end_frame)
            if self.last_key_steped:
                self.step_last_keyes()

            clip_end_frame = self.create_head_clips(clip_start_frame,
                                                    last_clip_end_frame,
                                                    clip_end_frame,
                                                    clip_duration,
                                                    last_clip_num,
                                                    original_name)

        return clip_end_frame

    def step_last_keyes(self):
        """
        set the out tangent of all the last keys on the ctrs to stepped mode
        """
        for ctr in self.ctrs:
            attributes = mc.listAttr(ctr, k=True)
            if attributes:
                for attr in attributes:
                    keyed_frames = mc.keyframe(ctr + '.' + attr, q=True, timeChange=True)
                    if keyed_frames:
                        mc.keyTangent(ctr + '.' + attr, time=(keyed_frames[-1], keyed_frames[-1]),
                                      outTangentType='step')

    def is_name_error(self, original_name, clip_num):
        if original_name != self.original_clips[clip_num]:
            mc.error("%s should be %s" % (original_name, self.original_clips[clip_num]))
            return True
        return False

    def create_head_clips(self,
                          original_start_frame,
                          last_end_frame,
                          original_end_frame,
                          clip_duration,
                          previous_clip_num,
                          original_name):
        """
        Create new clips for different head angles and copy animation.
        """
        clip_end_frame = last_end_frame
        clip_num = previous_clip_num
        new_end_frame = 0
        for i in range(len(HEAD_ANGLES)):
            clip_num += 1
            new_start_frame = clip_end_frame + 1
            new_end_frame = new_start_frame + clip_duration
            head_angle_offset = HEAD_ANGLES[i]
            self.copy_ctrs_animation(original_start_frame, original_end_frame,
                                     new_start_frame, new_end_frame, head_angle_offset)
            add_anim_clip(original_name,
                          new_start_frame, new_end_frame,
                          HEAD_ANGLES[i], clip_num)

            clip_end_frame = new_end_frame
        return new_end_frame

    def find_clips(self):
        """
        Populates head_angle_clips and original_clips
        @return: bool depending on whether could find all the clips
        """
        last_original_clip_num = -1
        clips_num = mc.getAttr(ctrs_manager.GAME_EXPORTER_PRESET + '.ac', size=True)
        for num in range(0, clips_num):
            clip_name = mc.getAttr(ctrs_manager.GAME_EXPORTER_PRESET + '.ac[%s].acn' % num)
            if clip_name is None:
                continue
            if "_head_angle_" not in clip_name:
                self.original_clips.append(clip_name)
                if num != last_original_clip_num + 1:
                    mc.error("%s is in a wrong place. all original clips should go before "
                             "head angle clips" % clip_name)
                    return False
                last_original_clip_num = num
            else:
                self.head_angle_clips.append(clip_name)
        if len(self.head_angle_clips)>0 and len(self.head_angle_clips)!=len(self.original_clips)*3:
            print ("wrong head angle clip number. PLease delete head angles before reexporting")
            return False
        return True

    def get_last_frame(self, clip_type="original"):
        clip_num = 0
        if clip_type == "original":
            clip_num = len(self.original_clips)
            if clip_num == 0:
                mc.error("there are no original clips!")
        # Not used right now, but maybe later
        elif clip_type == "all":
            clip_num = len(self.original_clips) + len(self.head_angle_clips)

        return mc.getAttr("%s.ac[%s].ace" % (ctrs_manager.GAME_EXPORTER_PRESET, (clip_num - 1)))

    def remove_head_angle_clips(self):
        clips_num = mc.getAttr(ctrs_manager.GAME_EXPORTER_PRESET + '.ac', size=True)

    def add_side_keys(self, start_frame, end_frame):
        """
        Creates keyframes at the first and last frames - need to have before copying
        """
        self.add_key(start_frame)
        self.add_key(end_frame)

    def add_key(self, key_frame):
        mc.select(clear=True) # Can't use mc.keyframe if keyframes are selected, so clear selection
        mc.currentTime(key_frame)
        for ctr in self.ctrs:
            # so that procedural start and end keys are not placed on audio node
            if ctr is not audio_core.AUDIO_NODE_NAME:
                currently_keyed = mc.keyframe(ctr, q=True,
                            time=(mc.currentTime(q=1), mc.currentTime(q=1)))
                if mc.keyframe(ctr, q=1) is not None and currently_keyed is None:
                    mc.setKeyframe(ctr)
                    mc.keyframe(ctr, time=(mc.currentTime(q=1), mc.currentTime(q=1)),
                                tickDrawSpecial=True)

    def remove_extra_animation(self):
        """
        In case need to remove animation after the last frame
        """
        last_frame = self.get_last_keyframe()
        last_original_frame = self.get_last_frame(clip_type="original")
        for ctr in self.ctrs:
            mc.cutKey(ctr, time=(last_original_frame + 1, last_frame))

    def copy_ctrs_animation(self, copy_start, copy_end, paste_start, paste_end, offset_value):
        for ctr in self.ctrs:
            try:
                mc.cutKey(ctr, time=(paste_start, paste_end))
                mc.copyKey(ctr, time=(copy_start, copy_end), option="curve")
                if ctr == ctrs_manager.HEAD_CTR:
                    mc.pasteKey(ctr, time=(paste_start, paste_start), valueOffset=offset_value)
                else:
                    mc.pasteKey(ctr, time=(paste_start, paste_start))
            except (TypeError, RuntimeError):  # If not a ctr or has no keys
                pass

    def get_last_keyframe(self):
        all_frames = []
        for ctr in self.ctrs:
            frames = mc.keyframe(ctr, q=True, timeChange=True)
            if frames:
                all_frames += frames
        if all_frames:
            return max(all_frames)
        else:
            print "can't find an end frame"
            return 0


# --------------------------------------------------------------------------------------------------
# Animation cutting, copying and clip related helper functions.
# --------------------------------------------------------------------------------------------------

def add_anim_clip(original_name, start_frame, end_frame, head_angle, clip_num,
                  game_exporter_preset="gameExporterPreset2"):
    """
    Create new animtion clip with specified parameters, unless it alreadye exists
    """
    new_clip_name = "%s_head_angle_%s" % (original_name, -head_angle)
    if mc.getAttr("%s.ac[%s].acn" % (game_exporter_preset, clip_num)) == new_clip_name:
        return
    mc.setAttr("%s.ac[%s].acn" % (game_exporter_preset, clip_num), new_clip_name, type="string")
    mc.setAttr("%s.ac[%s].acs" % (game_exporter_preset, clip_num), start_frame)
    mc.setAttr("%s.ac[%s].ace" % (game_exporter_preset, clip_num), end_frame)


def clip_error_check():
    """
    Returns true if there are errors.
    """
    if not mc.attributeQuery("ac", n=ctrs_manager.GAME_EXPORTER_PRESET, exists=True):
        mc.error("No animation clips!")
        return True
    return False


