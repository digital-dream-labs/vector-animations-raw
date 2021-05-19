#!/usr/bin/env python
"""
            This script will run export a series of known good and known bad maya files for
            regression testing.
            Errors are listed in red in the UI.
            Author: Chris Rogers 9/2018
            Copyright 2018 Anki, Inc.
"""

import os
import json
import copy
import subprocess
import maya.cmds as cmds
from window_docker import Dock
from ankimaya.export_for_robot import export_robot_anim, verify_export_path, set_export_path

VERBOSE = 1

WINTITLE = 'Regression Tests'

# List of files that are good
MAYA_FILE_PATH = os.path.join(os.environ['HOME'], 'workspace/victor-animation/scenes/sandbox/tests/Unittests')
OUTPUT_PATH = os.path.join(os.environ['HOME'], 'code/victor/EXTERNALS/animation-assets/animations/')
OUTPUT_PATH_TAR = os.path.join(os.environ['HOME'], 'workspace/victor-animation-assets/animations/')

VERIFIED_PATH = os.path.join(os.path.dirname(__file__), 'unit_test_verfied_json')
GOOD_MAYA_FILES = [
    'anim_audio_track_test.ma', 'anim_head_track_test.ma',
    'anim_backpack_lights_test.ma', 'anim_lift_track_test.ma',
    'anim_body_track_test.ma', 'anim_proc_face_test.ma',
    'anim_event_track_test.ma', 'anim_recorded_angle_test.ma']

# List of files that the exporter should not export
# Corrupt file, cozmo instead of vector, no wheel keys so exporter rejects it
BAD_MAYA_FILES = ['anim_test_fail_01.ma', 'anim_test_fail_02.ma', 'anim_recorded_angle_testFAIL.ma']

OUTPUT_FILES_TO_DELETE = ['anim_audio_track_test_01.json',
                            'anim_backpack_lights_test_01.json',
                            'anim_backpack_lights_test_02.json',
                            'anim_body_track_test_01.json',
                            'anim_body_track_test_02.json',
                            'anim_body_track_test_03.json',
                            'anim_event_track_test_01.json',
                            'anim_event_track_test_02.json',
                            'anim_head_track_test_01.json',
                            'anim_head_track_test_01.json',
                            'anim_head_track_test_02.json',
                            'anim_lift_track_test_01.json',
                            'anim_lift_track_test_02.json',
                            'anim_proc_face_test_01.json',
                            'anim_proc_face_test_02.json',
                            'anim_recorded_angle_test_01.json',
                            'anim_recorded_angle_test_02.json']

OUTPUT_TAR_FILES_TO_DELETE = ['anim_audio_track_test.tar',
                              'anim_proc_face_test.tar',
                              'anim_backpack_lights_test.tar',
                              'anim_event_track_test.tar',
                              'anim_head_track_test.tar',
                              'anim_recorded_angle_test.tar',
                              'anim_body_track_test.tar',
                              'anim_lift_track_test.tar']

# invalid tar file
BAD_TAR_FILE = ['anim_test_bad_01.tar']

stdout_pipe = subprocess.PIPE
stderr_pipe = subprocess.PIPE

# Maya 2016 uses PySide and Maya 2017+ uses PySide2, so try PySide2 first before resorting to PySide
try:
    from PySide2.QtCore import *
    from PySide2.QtGui import *
    from PySide2.QtWidgets import *
    from PySide2.QtUiTools import *
    from shiboken2 import wrapInstance
except ImportError:
    from PySide.QtCore import *
    from PySide.QtGui import *
    from PySide.QtUiTools import *
    from shiboken import wrapInstance


def read_anim_file(anim_file):
    """
    Given the path to a .json animation file, this function
    will read the contents of that file and return a 2-item
    tuple of (animation name, list of all keyframes)
    """
    if not os.path.isfile(anim_file):
        raise ValueError("Anim file missing: %s" % anim_file)
    fh = open(anim_file, 'r')
    try:
        contents = json.load(fh)
    except StandardError, e:
        # print("Failed to read %s file because: %s" % (anim_file, e))
        raise
    finally:
        fh.close()
    anim_name, all_keyframes = contents.items()[0]
    # print("The '%s' animation (%s) has %s total keyframes" % (anim_name, anim_file, len(all_keyframes)))
    return (anim_name, all_keyframes)


def convert_vals_to_int(keyframe):
    for key in keyframe.keys():
        val = keyframe[key]
        try:
            val = int(round(val))
        except TypeError:
            pass
        keyframe[key] = val


def convert_all_body_motion_vals_to_int(keyframe_list):
    for keyframe in keyframe_list:
        if keyframe["Name"] in ["BodyMotionKeyFrame", "HeadAngleKeyFrame", "LiftHeightKeyFrame"]:
            # We recently changed the values in some keyframes from floats
            # to integers, so generate an integer-only version of this keyframe
            # for comparison.
            convert_vals_to_int(keyframe)


def do_compare(first_file, second_file):
    result = ''
    num_bad_keyframes = 0
    try:
        first_name, first_keyframes = read_anim_file(first_file)
        second_name, second_keyframes = read_anim_file(second_file)
    except ValueError:
        return "ValueError in do_compare: {0} is probably not a valid json file."

    first_keyframes_copy = copy.deepcopy(first_keyframes)
    convert_all_body_motion_vals_to_int(first_keyframes_copy)
    second_keyframes_copy = copy.deepcopy(second_keyframes)
    convert_all_body_motion_vals_to_int(second_keyframes_copy)

    result += ("The following keyframes are missing from %s:" % second_file)
    for keyframe in first_keyframes:
        if keyframe not in second_keyframes:
            if "probability" in keyframe and not isinstance(keyframe["probability"], list):
                # We recently changed the "probability" attribute of audio keyframes from
                # a single float value to a list of floats, so check both forms here.
                keyframe_copy = copy.deepcopy(keyframe)
                keyframe_copy["probability"] = [keyframe_copy["probability"]]
                if keyframe_copy not in second_keyframes:
                    result += str(keyframe)
                    num_bad_keyframes += 1
            elif keyframe["Name"] in ["BodyMotionKeyFrame", "HeadAngleKeyFrame", "LiftHeightKeyFrame"]:
                keyframe_copy = copy.deepcopy(keyframe)
                convert_vals_to_int(keyframe_copy)
                if keyframe not in second_keyframes_copy and keyframe_copy not in second_keyframes:
                    result += str(keyframe)
                    num_bad_keyframes += 1
            else:
                result += str(keyframe)

    result += ("The following keyframes are missing from %s:" % first_file)
    for keyframe in second_keyframes:
        if keyframe not in first_keyframes:
            if "probability" in keyframe and isinstance(keyframe["probability"], list):
                # We recently changed the "probability" attribute of audio keyframes from
                # a single float value to a list of floats, so check both forms here.
                keyframe_copy = copy.deepcopy(keyframe)
                try:
                    keyframe_copy["probability"] = keyframe_copy["probability"][0]
                except IndexError:
                    result += str(keyframe)
                    num_bad_keyframes += 1
                else:
                    if keyframe_copy not in first_keyframes:
                        result += str(keyframe)
                        num_bad_keyframes += 1
            elif keyframe["Name"] in ["BodyMotionKeyFrame", "HeadAngleKeyFrame", "LiftHeightKeyFrame"]:
                keyframe_copy = copy.deepcopy(keyframe)
                convert_vals_to_int(keyframe_copy)
                if keyframe not in first_keyframes_copy and keyframe_copy not in first_keyframes:
                    result += str(keyframe)
                    num_bad_keyframes += 1
            else:
                result += str(keyframe)
                num_bad_keyframes += 1
    return (result, num_bad_keyframes)


class AnimUTWidget(QWidget):
    def __init__(self, *args, **kwargs):
        super(AnimUTWidget, self).__init__(*args, **kwargs)
        self.log = []
        self.outputfiles = []
        self.errors = []
        self.initUI()

    def _setStatus(self, msg):
        print msg
        self.statusLabel.setText(msg)
        self.log.append(msg)
        self.te.append(str(msg))
        self.te.setAcceptRichText(True)
        QApplication.processEvents()

    def initUI(self):
        lo = QVBoxLayout()
        self.setLayout(lo)
        title = QLabel('Anki Animation Regression Tests')
        button = QPushButton('Run Tests')
        buttonc = QPushButton('Cancel')
        lo.addWidget(title)
        lo.addWidget(button)

        self.statusLabel = QLabel('Status')
        lo.addWidget(self.statusLabel)
        self.te = QTextEdit()
        self.te.setText('Ready to start tests.')
        lo.addWidget(self.te)
        lo.addWidget(buttonc)
        button.clicked.connect(self.run_tests)
        buttonc.clicked.connect(self.close)

        self.show()

    def close(self):
        global _dockControl
        try:
            cmds.deleteUI(_dockControl)
        except:
            pass

    def _isValidTarFile(self, tarfile):
        if not os.path.exists(tarfile):
            raise IOError("no file {0}".format(tarfile))
            return
        # Use run command to try to list tar file
        cmd = '/usr/bin/tar tf {0}'.format(tarfile)
        (status, stdout, stderr) = run_command_core(cmd, shell=True)
        if status == 0:
            # msg = 'tar file is valid'
            # self._setStatus(msg)
            return 0
        else:
            # msg = 'tar file not valid.'
            self.errors.append('{0} is invalid tar file.'.format(tarfile))
            # self._setStatus(msg)
            return 1

    def _isValidJSON(self, jsonfile):
        if not os.path.exists(jsonfile):
            print "no file: {0}".format(jsonfile)
            raise IOError("no file {0}".format(jsonfile))
            return
        try:
            fid = open(jsonfile, 'r')
            d = json.load(fid)
            fid.close()
        except:
            # msg = 'JSON file not valid.'
            self.errors.append('{0} is invalid json file.'.format(jsonfile))
            return 1
        # msg = 'JSON file is valid.'
        return 0

    def _doCompare(self):
        msg = 'starting compare:'
        self._setStatus(msg)
        # For each known good maya file, compare results to known good json file
        for i in range(len(self.outputfiles)):
            if VERBOSE: print 'self.outputfiles[i]=', self.outputfiles[i]
            if self.outputfiles[i].endswith('json'):
                filename = os.path.basename(self.outputfiles[i]).replace('.json', '_verified.json')
                verified = os.path.join(VERIFIED_PATH, filename)
                ret, num = do_compare(self.outputfiles[i], verified)

                msg = "compare:{0} {1} - {2}".format(num, os.path.basename(self.outputfiles[i]),
                                                     os.path.basename(verified))
                if num == 0:
                    msg = "<font color=green>compare(0 is pass): {0} {1} - {2}</font>".format(num, os.path.basename(
                        self.outputfiles[i]), os.path.basename(verified))
                else:
                    msg = "<font color=red>compare(0 is pass): ERROR {0} {1} - {2}</font>".format(num, os.path.basename(
                        self.outputfiles[i]), os.path.basename(verified))
                    self.errors.append('{0} did not pass'.format(self.outputfiles[i]))
                self._setStatus(msg)

    def _doExport(self, show_json=True, testShouldFail=False):
        """Export files using export_robot_anim
        testShouldFail flag is to color a test green if was supposed to fail and it did
        :return empty array if no files were generated
        :return list of output files if there were any"""
        # Bypass the dialogs so we can automate these tests
        out_files = (export_robot_anim(show_json=False, bypass_dialog=True))

        if out_files is None or len(out_files) < 1:
            msg = "<font color=red>No Output files were generated</font>"
            if testShouldFail:
                msg = "<font color=green>No output files for a FAIL test. Correct result.</font>"
            self._setStatus(msg)
            return []
        for o in out_files:
            self.outputfiles.append(o)

        msg = "{0} files were generated.".format(len(out_files))
        if len(out_files) > 0:
            msg = '{0}{1}{2}'.format('<font color=green>', msg, '</font>')
        else:
            msg = '{0}{1}{2}'.format('<font color=red>', msg, '</font>')
        for o in self.outputfiles:
            self.log.append(o)
        self._setStatus(msg)
        return out_files

    def _checkExport(self):
        """For each output file, determine if json or tar
        If json, make sure its valid json
        If tar make sure its a valid tar file
        """
        for of in self.outputfiles:
            if not os.path.exists(of):
                msg = 'Missing file. {0}'.format(of)
                self._setStatus(msg)
                continue
            if of.endswith('.json'):
                ret = self._isValidJSON(of)
                if ret != 0:
                    msg = "<font color=red>{0} is not a valid json file.</font>".format(os.path.basename(of))
                    self.errors('{0} not a valid json file.'.format(of))
                    self._setStatus(msg)
                else:
                    msg = "<font color=green>{0} is a valid json file.</font>".format(os.path.basename(of))
                    self._setStatus(msg)

            if of.endswith('.tar'):
                ret = self._isValidTarFile(of)
                if ret != 0:
                    self.errors('{0} not a valid tar file.'.format(of))
                    msg = "<font color=red>{0} is not a valid tar file.</font>".format(os.path.basename(of))
                    self._setStatus(msg)
                else:
                    msg = "<font color=green>{0} is a valid tar file.</font>".format(os.path.basename(of))
                    self._setStatus(msg)

    def _delete_old_results(self, debug=False):
        debug=True
        # Teardown from previous tests
        for of in OUTPUT_FILES_TO_DELETE:
            path = os.path.join(OUTPUT_PATH, of)
            print path
            try:
                if os.path.exists(path):
                    os.remove(path)
            except:
                raise IOError("could not remove file: {0}.".format(path))
            if debug:
                msg = 'deleted {0}'.format(of)
                self._setStatus(msg)

        for of in OUTPUT_TAR_FILES_TO_DELETE:
            path = os.path.join(OUTPUT_PATH_TAR, of)
            print path
            try:
                if os.path.exists(path):
                    os.remove(path)
            except:
                raise IOError("could not remove file: {0}.".format(path))
            if debug:
                msg = 'deleted {0}'.format(of)
                self._setStatus(msg)



    def _run_good_maya_exports(self):
        for g in GOOD_MAYA_FILES:
            mayafile = os.path.join(MAYA_FILE_PATH, g)
            if not os.path.exists(mayafile):
                msg = ("testing known good file:NO FILE: {0}.".format(mayafile))
                self._setStatus(msg)
                continue
            else:
                msg = "testing known good file:opening {0}".format(g)
                self._setStatus(msg)
            cmds.file(mayafile, open=True, force=True)
            ret = self._doExport()
            QApplication.processEvents()

    def _run_bad_maya_exports(self):
        for b in BAD_MAYA_FILES:
            mayafile = os.path.join(MAYA_FILE_PATH, b)
            if not os.path.exists(mayafile):
                msg = ("testing file to FAIL:NO FILE: {0}.".format(mayafile))
                self._setStatus(msg)
                continue
            else:
                msg = "testing file to FAIL:opening {0}".format(mayafile)
                self._setStatus(msg)
                cmds.file(mayafile, open=True, force=True)
                try:
                    self._doExport(testShouldFail=True)
                except ValueError:
                    msg = '<font color=green>testing file to FAIL: {0} failed as it should.</font>'.format(mayafile)
                    self._setStatus(msg)

    def run_tests(self):
        print "starting run tests...."
        self.te.clear()

        # delete old results so they will not be validated
        self._delete_old_results()

        # this test should export 1 json per clip and 1 tar file for each good maya file
        # there should be no errors
        self._run_good_maya_exports()

        # check to see that each output json file is a valid json file and same for tar file
        self._checkExport()

        # compare the output json files again known good results
        self._doCompare()

        # run maya files that should cause errors and/or no output
        self._run_bad_maya_exports()

        # make sure no json or tar files were made and that the errors occurred
        msg = "done running tests."

        self._setStatus(msg)
        if len(self.errors) == 0:
            self.te.append("No errors.")
        else:
            self.te.update(self.errors)

        # delete results so they dont exist in the asset directory
        self._delete_old_results()

def run_command_core(cmd, stdout_pipe=stdout_pipe, stderr_pipe=stderr_pipe, shell=False, split=False):
    if VERBOSE:
        print "CMD=", cmd
    if split:
        cmd = cmd.split()
    try:
        p = subprocess.Popen(cmd, stdout=stdout_pipe, stderr=stderr_pipe, shell=shell)
    except OSError as err:
        print("Failed to execute '%s' because: %s" % (cmd, err))
        return (None, None, None)
    (stdout, stderr) = p.communicate()
    status = p.poll()
    if VERBOSE:
        print "cmd:status: ", status
        print "cmd:stdout: ", stdout
        print "cmd:stderr: ", stderr
    return (status, stdout, stderr)


_dockControl = None


def main():
    try:
        cmds.deleteUI(WINTITLE)
    except:
        pass
    global _dockControl
    ui, dockWidget, _dockControl = Dock(AnimUTWidget, width=320, winTitle=WINTITLE)
    _globalPreviewUI = ui
    return ui


if __name__ == '__main__':
    main()
