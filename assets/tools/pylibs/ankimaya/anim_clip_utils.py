
import maya.cmds as mc
from ankimaya import game_exporter
from game_exporter import GAME_EXPORTER_PRESET


CLIP_NAME_KEY = "clip_name"


def is_there_intersecting_clip(start_frame, end_frame, strict=False):
    try:
        clips_num = mc.getAttr(GAME_EXPORTER_PRESET + '.ac', size=True)
    except ValueError:
        print("Please make sure to have animation clips in your scene")
        return None

    for num in range(0, clips_num):
        clip_start_frame = mc.getAttr(GAME_EXPORTER_PRESET + '.ac[%s].acs' % num)
        clip_end_frame = mc.getAttr("%s.ac[%s].ace" % (GAME_EXPORTER_PRESET, num))
        clip_name = mc.getAttr(GAME_EXPORTER_PRESET + '.ac[%s].acn' % num)
        if strict:
            if clip_start_frame <= start_frame <= end_frame <= clip_end_frame:
                return clip_name
        else:
            if do_timeframes_intersect(timeframe01=[clip_start_frame, clip_end_frame],
                                       timeframe02=[start_frame, end_frame]):
                return clip_name
    return None


def get_anim_clips():
    """
    Copied from syncWithGameExporter() of ag_editor
    """
    # Get anim clips from Game Exporter...
    gameExporterAnims = game_exporter.get_clip_info('', include_all=True)[2]
    gameExporterAnims = [str(x[CLIP_NAME_KEY]) for x in gameExporterAnims]
    while '' in gameExporterAnims:
        gameExporterAnims.remove('')

    # Add all anim clips from Game Exporter
    animClips = []
    for anim in gameExporterAnims:
        if anim not in animClips:
            animClips.append(anim)
    return animClips


def do_timeframes_intersect(timeframe01=None, timeframe02=None):
    if len(timeframe01)!=2 or len(timeframe02)!=2:
        raise ValueError("do_timeframes_intersect: Timeframes should have two values: [start, end]")

    if timeframe02[0] in [timeframe01[0],timeframe01[1]] or timeframe02[1] in [timeframe01[0],timeframe01[1]]:
        return True
    if timeframe02[0] <= timeframe01[0] <= timeframe02[1]:
        return True
    if timeframe02[1] <= timeframe01[1] <= timeframe02[0]:
        return True
    if timeframe01[0] <= timeframe02[1] <= timeframe01[1]:
        return True
    if timeframe01[0] <= timeframe02[0] <= timeframe01[1]:
        return True
    return False


def find_clip_num_from_name(find_clip_name=""):
    try:
        clips_num = mc.getAttr(GAME_EXPORTER_PRESET + '.ac', size=True)
    except ValueError:
        print("Please make sure to have animation clips in your scene")
        return None
    for num in range(0, clips_num):
        clip_name = mc.getAttr(GAME_EXPORTER_PRESET + '.ac[%s].acn' % num)
        if clip_name == find_clip_name:
            return num
    print("Cannot find '%s' animation clip" % find_clip_name)


