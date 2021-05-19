#!/usr/bin/env python3

# Copyright: Anki, Inc. 2017

# This value comes from Anki::Comms::MsgPacket::MAX_SIZE in the coretech messaging library
CHUNK_SIZE = 2048

ANIM_DIR_ENV_VAR = "ANKI_ANIM_DIR"

ADB_SCRIPT = "/usr/local/bin/adb"

ANIMATION_STARTING_VERBAL_MSG = "begin animation"
ANIMATION_COMPLETE_VERBAL_MSG = "animation complete"

ANIM_NAMES_FLAG = "-anims"
ANIM_FILES_FLAG = "-files"
ANIM_VOLUME_FLAG = "-volume"
ANIM_IGNORE_CLIFFS_FLAG = "-ignore_cliffs"
ANIM_CONNECT_CUBES_FLAG = "-connect_cubes"
ANIM_ENABLE_REACTIONS_FLAG = "-enable_reactions"

ARG_DELIMITER = ','
LOOPS_DELIMITER = ':'
MIN_NUM_LOOPS = 1

NUM_CUBES = 3


import sys
import os
import time
import pprint
import tempfile
import concurrent.futures._base

import cozmo
import cozmo.run
cozmo.run.DEFAULT_ADB_CMD = ADB_SCRIPT
import cozmo.lights
from cozmo._clad import _clad_to_engine_iface

try:
    from robot_config import check_robot_battery
except ImportError:
    check_robot_battery = None


def read_file_in_chunks(file_path, chunk_size):
    if not os.path.isfile(file_path):
        raise ValueError("File missing: %s" % file_path)
    chunks = []
    with open(file_path, 'rb') as fh:
        #chunk = bytes(fh.read(chunk_size).decode('ascii'), 'utf-8')
        chunk = fh.read(chunk_size)
        while chunk:
            chunks.append(chunk)
            chunk = fh.read(chunk_size)
    return chunks


def strip_ascii_whitepace(text_file):
    #print("Reading file: %s" % text_file)
    fh = open(text_file, 'r')
    contents = fh.read()
    fh.close()

    # Strip out all newline and space characters
    contents = contents.replace(os.linesep, '')
    contents = contents.replace(' ', '')

    file_name = os.path.basename(text_file)
    file_name, file_ext = os.path.splitext(file_name)
    file_name += '-'
    (fd, stripped_file) = tempfile.mkstemp(prefix=file_name, suffix=file_ext)

    fh = open(stripped_file, 'w')
    fh.write(contents)
    fh.close()
    #print("Wrote file: %s" % stripped_file)

    return stripped_file


class CozmosCubes(object):
    def __init__(self, world):
        self.world = world

    def get_connected_cubes_list(self):
        cubes = list(self.world.connected_light_cubes)
        return cubes

    def get_num_connected_cubes(self):
        count = 0
        for cube in self.world.connected_light_cubes:
            count += 1
        return count

    def disconnect(self):
        if self.get_num_connected_cubes() == 0:
            # already connected to zero cubes, no need to disconnnect
            return None
        self.world.disconnect_from_cubes()
        time.sleep(0.5)
        #print("number of connected cubes (after disconnect) = %s" % self.get_num_connected_cubes())

    def connect(self, connect_color=cozmo.lights.blue_light):
        if self.get_num_connected_cubes() >= NUM_CUBES:
            # already connected to 3 or more cubes, no need to connect
            return None
        self.world.connect_to_cubes()
        time.sleep(0.5)
        #print("number of connected cubes (after connect) = %s" % self.get_num_connected_cubes())
        if connect_color:
            self.light_cubes(connect_color)

    def light_cubes(self, color, light_time_sec=5):
        # The 'color' input parameter should be 'cozmo.lights.red_light' or something similar
        if not color:
            return None
        from cozmo.objects import LightCube1Id, LightCube2Id, LightCube3Id
        cube1 = self.world.get_light_cube(LightCube1Id)  # looks like a paperclip
        cube2 = self.world.get_light_cube(LightCube2Id)  # looks like a lamp / heart
        cube3 = self.world.get_light_cube(LightCube3Id)  # looks like the letters 'ab' over 'T'
        all_cubes = [cube1, cube2, cube3]
        for cube in all_cubes:
            if cube is not None:
                cube.set_lights(color)
        time.sleep(light_time_sec)
        for cube in all_cubes:
            if cube is not None:
                cube.set_lights_off()


class CozmoAnimTransferAndPlay(object):
    def __init__(self, coz, anim_names, file_paths, volume, ignore_cliffs, connect_cubes,
                 enable_reactions, arg_delimiter=ARG_DELIMITER):
        self.coz = coz
        self.anim_names = anim_names.split(arg_delimiter)
        while '' in self.anim_names:
            self.anim_names.remove('')
        self.file_paths = file_paths.split(arg_delimiter)
        while '' in self.file_paths:
            self.file_paths.remove('')
        try:
            self.volume = float(volume)
        except (ValueError, TypeError):
            print("WARNING: Invalid value provided for volume: %s" % volume)
            self.volume = None
        self.ignore_cliffs = ignore_cliffs
        self.connect_cubes = connect_cubes
        self.enable_reactions = enable_reactions

    def check_loops(self, num_loops):
        try:
            num_loops = int(num_loops)
        except (TypeError, ValueError):
            num_loops = MIN_NUM_LOOPS
        else:
            num_loops = max(MIN_NUM_LOOPS, num_loops)
        return num_loops

    def play_anims(self, announce=False, loops_delimiter=LOOPS_DELIMITER):
        failed_anims = {}

        #########################################################
        # TODO: Allow animators to set the volume of Victor VO
        #if self.volume is not None:
        #    self.coz.set_robot_volume(self.volume)
        #########################################################

        cubes = CozmosCubes(self.coz.world)
        #print("number of connected cubes (before) = %s" % cubes.get_num_connected_cubes())
        if self.connect_cubes:
            cubes.connect()
        else:
            cubes.disconnect()
        #print("number of connected cubes (after) = %s" % cubes.get_num_connected_cubes())

        if self.ignore_cliffs:
            # disable cliff detection
            self.coz.enable_stop_on_cliff(False)
        if self.enable_reactions:
            # enable reactions, eg. cliff reaction animation
            self.coz.enable_all_reaction_triggers(True)

        if announce and ANIMATION_STARTING_VERBAL_MSG:
            self.coz.say_text(ANIMATION_STARTING_VERBAL_MSG).wait_for_completed()
        for anim_name in self.anim_names:
            anim_name = anim_name.strip()
            try:
                anim_name, num_loops = anim_name.rsplit(loops_delimiter, 1)
            except ValueError:
                num_loops = MIN_NUM_LOOPS
            num_loops = self.check_loops(num_loops)
            print("Playing animation: %s" % anim_name)
            try:
                self.coz.play_anim(anim_name, loop_count=num_loops).wait_for_completed()
            except ValueError as err:
                failed_anims[anim_name] = str(err)

            if self.enable_reactions:
                # give the robot time to react if, for example, a cliff was encountered
                time.sleep(15)

        if check_robot_battery:
            check_robot_battery(self.coz.battery_voltage)
        print("Played animations: %s" % ', '.join(self.anim_names))
        if announce and ANIMATION_COMPLETE_VERBAL_MSG:
            self.coz.say_text(ANIMATION_COMPLETE_VERBAL_MSG).wait_for_completed()

        # Undo any changes made above to cliff detection and/or reactions being enabled
        if self.ignore_cliffs:
            self.coz.enable_stop_on_cliff(True)
        if self.enable_reactions:
            self.coz.enable_all_reaction_triggers(False)

        return failed_anims

    def refresh_anims(self):
        """
        Refresh animations so that they are added to anim_names on the sdk side
        TODO: investigate the timing of refresh in sdk, can we avoid the sleep?
        """
        time.sleep(0.5)
        self.coz.conn.anim_names.refresh()
        self.coz.conn.anim_names.wait_for_loaded()
        time.sleep(0.5)

    def transfer_image_file(self, img_file, chunk_size=CHUNK_SIZE):
        # If saved with a NOT terrible program these should just be one chunk since it's only
        # a 128 x 64 png. However, "Apple Preview" and GIMP are terrible and create 4K images
        # thats like half the size of a .bmp every pixel save.
        chunks = read_file_in_chunks(img_file, chunk_size)
        num_chunks = len(chunks)
        print("The %s file has %s chunks of bytes to transfer" % (img_file, num_chunks))
        for idx in range(num_chunks):
            msg = _clad_to_engine_iface.TransferFile(fileBytes=chunks[idx], filePart=idx,
                      numFileParts=num_chunks, filename=os.path.basename(img_file),
                      fileType=_clad_to_engine_iface.FileType.FaceImg)
            self.coz.conn.send_msg(msg)

    def update_facial_anims_on_robot(self, facial_anims, source_dir):
        from facial_animation import get_facial_png_files
        for facial_anim in facial_anims:
            try:
                png_files = get_facial_png_files(facial_anim, source_dir)
            except (RuntimeError, ValueError) as err:
                print("WARNING: %s" % err)
                continue
            for png_file in png_files:
                png_file = png_file.strip()
                self.transfer_image_file(png_file)
            # Directory upload complete, process everything you just got
            msg = _clad_to_engine_iface.ReadFaceAnimationDir()
            self.coz.conn.send_msg(msg)

    def transfer_anims(self, chunk_size=CHUNK_SIZE):
        try:
            from ankiutils.anim_files import report_file_stats
        except ImportError:
            report_file_stats = None
        file_stats_msgs = []
        for anim_file in self.file_paths:
            anim_file = anim_file.strip()
            if not os.path.isfile(anim_file):
                raise ValueError("File missing: %s" % anim_file)
            self.transfer_single_anim(anim_file)
            if report_file_stats:
                file_stats_msgs.append(report_file_stats(anim_file))

            # Is there any good way to avoid refreshing EVERYTHING when one animation is added?
            self.refresh_anims()

        return file_stats_msgs

    def transfer_single_anim(self, anim_file, chunk_size=CHUNK_SIZE):
        # TODO: Move this method to SDK robot.py ?

        try:
            from facial_animation import get_facial_anims, FACIAL_ANIM_DIR
        except ImportError:
            facial_anims = None
        else:
            facial_anims = get_facial_anims(anim_file)
        if facial_anims:
            anim_tar_file_dir = os.getenv(ANIM_DIR_ENV_VAR)
            if not anim_tar_file_dir:
                raise ValueError("The '%s' environment variable should be set" % ANIM_DIR_ENV_VAR)
            png_tar_file_dir = os.path.join(os.path.dirname(anim_tar_file_dir), FACIAL_ANIM_DIR)
            try:
                self.update_facial_anims_on_robot(facial_anims, png_tar_file_dir)
            except ValueError as err:
                raise ValueError("Failed to update facial animation for %s because: %s"
                                 % (os.path.basename(anim_file), err))

        anim_file = strip_ascii_whitepace(anim_file)
        chunks = read_file_in_chunks(anim_file, chunk_size)
        num_chunks = len(chunks)
        for idx in range(num_chunks):
            msg = _clad_to_engine_iface.TransferFile(fileBytes=chunks[idx], filePart=idx,
                      numFileParts=num_chunks, filename=os.path.basename(anim_file),
                      fileType=_clad_to_engine_iface.FileType.Animation)
            self.coz.conn.send_msg(msg)

        print("Transferred animation file: %s" % os.path.basename(anim_file))


_anim_names = None
_file_paths = None
_volume = None
_ignore_cliffs = None
_connect_cubes = None
_enable_reactions = None


def run(coz_conn):
    coz = coz_conn.wait_for_robot()
    worker = CozmoAnimTransferAndPlay(coz, _anim_names, _file_paths, _volume, _ignore_cliffs,
                                      _connect_cubes, _enable_reactions)

    if _file_paths:
        # TODO: Should this get added to the SDK API as coz.transfer_anim() or something similar?
        file_stats_msgs = worker.transfer_anims()
    else:
        file_stats_msgs = []

    # TODO: Replace with the name of the animation from the file
    failed_anims = worker.play_anims()
    if failed_anims:
        raise ValueError("Failed to play one or more animations:" + os.linesep
                         + pprint.pformat(failed_anims))
    elif file_stats_msgs:
        for file_stats_msg in file_stats_msgs:
            print(file_stats_msg)


def main():
    global _anim_names, _file_paths, _volume, _ignore_cliffs, _connect_cubes, _enable_reactions

    anim_names_idx = sys.argv.index(ANIM_NAMES_FLAG) + 1
    _anim_names = sys.argv[anim_names_idx]

    try:
        file_paths_idx = sys.argv.index(ANIM_FILES_FLAG) + 1
        _file_paths = sys.argv[file_paths_idx]
    except (ValueError, IndexError):
        _file_paths = ''

    try:
        volume_idx = sys.argv.index(ANIM_VOLUME_FLAG) + 1
        _volume = sys.argv[volume_idx]
    except (ValueError, IndexError):
        _volume = None

    _ignore_cliffs = ANIM_IGNORE_CLIFFS_FLAG in sys.argv
    _connect_cubes = ANIM_CONNECT_CUBES_FLAG in sys.argv
    _enable_reactions = ANIM_ENABLE_REACTIONS_FLAG in sys.argv

    cozmo.setup_basic_logging()
    try:
        cozmo.connect(run)
    except (cozmo.ConnectionError, concurrent.futures._base.Error) as err:
        if not str(err):
            err = str(type(err))
        sys.exit("A connection error occurred: %s" % err)


if __name__ == "__main__":
    main()


