#!/usr/bin/env python3
"""
This script can be used to prepare a Victor robot for using the SDK to
control the robot.

When used to install to the robot, this script will try to install:
 - binaries and libraries from the Victor master build downloaded to
   ~/Downloads/Victor_master_<number>_artifacts.zip (using the highest
   number available when multiple .zip files are available)
 - animation assets from the directory that $ANKI_ANIM_DIR points at,
   which is typically the animations/ directory in the
   'victor-animation-assets' SVN repo (you can see that setting in
   https://svn.ankicore.com/svn/victor-animation/trunk/tools/other/Maya.env)

When used to install the SDK, this script will try to install:
 - the 'cozmoclad' python package from ~/Downloads/cozmoclad-2.2.0-py3-none-any.whl
 - the 'cozmo' python package from https://github.com/anki/victor-python-sdk-private

Since this script is intended to be executed from within an animator's
Maya environment, it assumes that the $ANKI_ANIM_DIR and $ANKI_TOOLS
environment variables are set correctly.

Copyright: Anki, Inc. 2018
"""

APP_VERSION = "2.2.0"
SDK_VERSION = "1.2.1.dev0"

INSTALL_FILES_SOURCE_DIR = "Downloads"

ROBOT_INSTALLER_ZIP_FILE = "Victor_master_*_artifacts.zip"
LIB_DIR = "lib"
LIB_FILES = ["*.so"]
BIN_DIR = "bin"
FILES_TYPES_TO_NOT_DEPLOY = [".full", ".txt", ".log", ".check_cache", ".gz", ".tar", ".tgz"]

MANIFEST_FILE_NAME = "anim_manifest.json"
MANIFEST_NAME_KEY = "name"
MANIFEST_LENGTH_KEY = "length_ms"

TRIGGER_TIME_ATTR = "triggerTime_ms"
DURATION_TIME_ATTR = "durationTime_ms"

ANIM_DATA_SUBDIRS = ["animations", "animationGroups", "faceAnimations"]

RESOURCES_SUBDIRS = ["config", "webserver"]

# Most animation tar files in SVN are packages of JSON files that should be unpacked in the root
# "animations" directory, but facial animation tar files (packages of PNG files) should be unpacked
# in a subdirectory of the root "faceAnimations" directory. The following list indicates the groups
# of tar files that should be unpacked in a subdirectory, which is named after the tar file.
UNPACK_INTO_SUBDIR = ["faceAnimations"]

EXTRACT_TYPES_FROM_TAR = [".json", ".png"]

ANIM_DIR_ENV_VAR = "ANKI_ANIM_DIR"

TOOLS_DIR_ENV_VAR = "ANKI_TOOLS"

BASH_SCRIPTS_DIR_RELATIVE_TO_TOOLS_DIR = "robot_scripts"

BASH_CMDS_SCRIPT = "bash_cmds.sh"

SDK_INSTALLER_ZIP_FILE = "sdk_installer_%s_clad_%s.zip" % (SDK_VERSION, APP_VERSION)
SDK_INSTALLER_ZIP_FILE_SUBDIR = "dist"
COZMO_CLAD_WHEEL_FILE = "cozmoclad-%s-py3-none-any.whl" % APP_VERSION
COZMO_CLAD_PYTHON = "cozmoclad"
COZMO_SDK_WHEEL_FILE = "cozmo-%s-py3-none-any.whl" % SDK_VERSION
COZMO_SDK_PYTHON = "cozmo"

GIT_URL = "anki/victor-python-sdk-private.git"
GIT_HTTP = "https://github.com/" + GIT_URL
GIT_SSH = "git@github.com:" + GIT_URL
GIT_BRANCH = "master"

ADB_SCRIPT = "/usr/local/bin/adb"
ADB_DEVICES_HEADER = "List of devices attached"
ADB_DEVICE_AVAIL_SUFFIX = "device"
ADB_DEVICE_OFFLINE_SUFFIX = "offline"
ADB_DEVICE_REFUSED_SUFFIX = "refused"

INSTALL_ROBOT_FLAG = "-install_robot"
INSTALL_SDK_FLAG = "-install_sdk"
CONNECT_FLAG = "-connect"
DISCONNECT_FLAG = "-disconnect"
RESTART_FLAG = "-restart"

NETSTATS_WIFI_CONNECTION_PREFIX = "iface=wlan0"
NETSTATS_WIFI_NETWORK_ID_TOKEN = "networkId"
EXPECTED_WIFI_NETWORK_PREFIX = "Cozmo"

RUN_COMMAND_FAILURE_MSG = "Failed to execute '%s' (exit status = %s)"


import sys
import os
import re
import pip
import time
import tempfile
import uuid
import json
import subprocess
import pprint
import copy
import glob
import shutil
import zipfile
import tarfile


def get_env_vars_for_run_cmd(path_var="PATH"):
    # Prepend /usr/local/bin/ to $PATH for adb
    usr_local_bin = "/usr/local/bin"
    env_vars = copy.copy(os.environ)
    if not env_vars[path_var].startswith(usr_local_bin + os.pathsep):
        env_vars[path_var] = usr_local_bin + os.pathsep + env_vars[path_var]
    return env_vars


def run_command(cmd, raise_on_fail=True, display_stdout=False, failure_msg=RUN_COMMAND_FAILURE_MSG):
    """
    Given a command to run, this function will execute that
    in a subprocess and return (status, stdout, stderr)

    If the 'raise_on_fail' input argument is set to True,
    then this function will raise RuntimeError when the
    subprocess returns a non-zero status.
    """
    if display_stdout:
        stdout = None
    else:
        stdout = subprocess.PIPE
    #print("Running: %s" % cmd)
    p = subprocess.Popen(cmd, stdout=stdout, stderr=subprocess.PIPE, shell=True,
                         env=get_env_vars_for_run_cmd())
    (stdout, stderr) = p.communicate()
    if stdout is not None:
        stdout = decode_output_string(stdout)
    if stderr is not None:
        stderr = decode_output_string(stderr)
    status = p.poll()
    if status != 0 and raise_on_fail:
        err_msg = failure_msg % (cmd, status)
        if stderr:
            err_msg += os.linesep + stderr
        raise RuntimeError(err_msg)
    return (status, stdout, stderr)


def decode_output_string(output_string, output_decoders=["utf-8", "latin_1"]):
    """
    This function can be used to decode Unicode strings. If the string
    cannot be successfully decoded, this function returns empty string.
    """

    # The 'latin_1' encoder was picked somewhat arbitrarily. While troubleshooting
    # an install problem for Leigh on 04/26/2017, Daria went through a few encoders
    # until she found the one that worked.

    for output_decoder in output_decoders:
        try:
            return_string = output_string.decode(output_decoder)
        except UnicodeDecodeError:
            continue
        except BaseException:
            return ''
        else:
            return return_string
    return ''


def delete_files_from_dir(file_types, dir_path, file_names):
    delete_count = 0
    file_types = [str(x) for x in file_types]
    #print("Deleting all %s files from %s" % (file_types, dir_path))
    for file_name in file_names:
        file_ext = str(os.path.splitext(file_name)[1])
        if file_ext in file_types:
            os.remove(os.path.join(dir_path, file_name))
            delete_count += 1
    #print("Deleted %s files of types %s" % (delete_count, file_types))
    return delete_count


def get_file_stats(which_dir):
    file_stats = {}
    for (dir_path, dir_names, file_names) in os.walk(which_dir):
        for file_name in file_names:
            file_ext = str(os.path.splitext(file_name)[1])
            if file_ext not in file_stats:
                file_stats[file_ext] = 1
            else:
                file_stats[file_ext] += 1
    return file_stats


def get_anim_length(keyframe_list):
    anim_length = 0
    for keyframe in keyframe_list:
        try:
            trigger_time_ms = keyframe[TRIGGER_TIME_ATTR]
        except KeyError:
            continue
        try:
            duration_time_ms = keyframe[DURATION_TIME_ATTR]
        except KeyError:
            duration_time_ms = 0
        keyframe_length_ms = trigger_time_ms + duration_time_ms
        anim_length = max(anim_length, keyframe_length_ms)
    return anim_length


def get_anim_name_and_length(json_file):
    anim_name_length_mapping = {}
    if not json_file or not os.path.isfile(json_file):
        raise ValueError("Invalid JSON file provided: %s" % json_file)
    with open(json_file, 'r') as fh:
        contents = json.load(fh)
    for anim_name, keyframes in contents.items():
        anim_name = str(anim_name)
        anim_length = get_anim_length(keyframes)
        if not isinstance(anim_length, int):
            if anim_length == int(anim_length):
                anim_length = int(anim_length)
            else:
                print("WARNING: The length of '%s' is not an integer (length = %s)"
                      % (anim_name, anim_length))
        anim_name_length_mapping[anim_name] = anim_length
    return anim_name_length_mapping


def _get_specific_members(members, file_types):
    file_list = []
    for tar_info in members:
        if os.path.splitext(tar_info.name)[1] in file_types:
            file_list.append(tar_info)
    return file_list


def unpack_tarball(tar_file, file_types, put_in_subdir=False):
    anim_name_length_mapping = {}

    # Set the destination directory where the contents of the .tar file will be unpacked.
    dest_dir = os.path.dirname(tar_file)
    if put_in_subdir:
        subdir = os.path.splitext(os.path.basename(tar_file))[0]
        dest_dir = os.path.join(dest_dir, subdir)
        if os.path.isdir(dest_dir):
            # If the destination sub-directory already exists, get rid of it.
            shutil.rmtree(dest_dir)

    try:
        tar = tarfile.open(tar_file)
    except tarfile.ReadError as e:
        raise RuntimeError("%s: %s" % (e, tar_file))

    tar_members = _get_specific_members(tar, file_types)
    #print("Unpacking %s (version %s) (%s files)" % (tar_file, tar_file_rev, len(tar_members)))
    tar.extractall(dest_dir, members=tar_members)
    tar.close()
    if ".json" in file_types:
        json_files = [tar_info.name for tar_info in tar_members if tar_info.name.endswith(".json")]
        json_files = map(lambda x: os.path.join(dest_dir, x), json_files)
        if json_files:
            for json_file in json_files:
                try:
                    anim_name_length_mapping.update(get_anim_name_and_length(json_file))
                except json.decoder.JSONDecodeError:
                    print("ERROR: Unable to determine the length of animation in %s" % json_file)

    return anim_name_length_mapping


def extract_files_from_tar(extract_dir, file_types, put_in_subdir=False):
    """
    Given the path to a directory that contains .tar files and a list
    of file types, eg. [".json", ".png"], this function will unpack
    the given file types from all the .tar files.  If the optional
    'put_in_subdir' input argument is set to True, then the files are
    unpacked into a sub-directory named after the .tar file.
    """
    anim_name_length_mapping = {}

    for (dir_path, dir_names, file_names) in os.walk(extract_dir):

        # Generate list of all .tar files in/under the directory provided by the caller (extract_dir)
        all_files = map(lambda x: os.path.join(dir_path, x), file_names)
        tar_files = [a_file for a_file in all_files if a_file.endswith('.tar')]

        if tar_files and not put_in_subdir:
            # If we have any .tar files to unpack and they will NOT be unpacked into a sub-directory,
            # then first clean up existing files that may conflict with what will be unpacked. If
            # the .tar files WILL be unpacked into a sub-directory, we don't need to do any cleanup
            # here because unpack_tarball() will first delete the sub-directory if it already exists.
            delete_files_from_dir(file_types, dir_path, file_names)

        for tar_file in tar_files:
            anim_name_length_mapping.update(unpack_tarball(tar_file, file_types, put_in_subdir))

        # Remove tar files after unpacking them
        delete_files_from_dir(['.tar'], dir_path, file_names)

        if put_in_subdir:
            # If we are extracting tar files into subdirs, don't recurse into those subdirs.
            break

    return anim_name_length_mapping


class RobotDeploy(object):
    def __init__(self, tools_dir_env_var=TOOLS_DIR_ENV_VAR,
                 bash_scripts_dir=BASH_SCRIPTS_DIR_RELATIVE_TO_TOOLS_DIR,
                 bash_cmds_script=BASH_CMDS_SCRIPT):
        tools_dir = os.getenv(tools_dir_env_var)
        if not tools_dir or not os.path.isdir(tools_dir):
            raise ValueError("The $%s environment variable should point at a valid tools directory "
                             "that contains %s/ among others" % (tools_dir_env_var, bash_scripts_dir))
        self.bash_cmds_script = os.path.join(os.path.dirname(__file__), bash_cmds_script)

    def get_zip_file(self, zip_file=ROBOT_INSTALLER_ZIP_FILE,
                     install_files_source_dir=INSTALL_FILES_SOURCE_DIR):
        # Get the zip file that contains binaries and libs for deployment to robot
        if not install_files_source_dir.startswith(os.sep):
            install_files_source_dir = os.path.join(os.environ["HOME"], install_files_source_dir)
        try:
            zip_file = check_file_and_return_full_path(zip_file, install_files_source_dir)
        except ValueError:
            if '*' in zip_file:
                zip_file = get_highest_file_and_return_full_path(zip_file, install_files_source_dir)
            else:
                raise
        return zip_file

    def prepare(self):
        deployment_dir = tempfile.mkdtemp()
        zip_file = self.get_zip_file()
        print("Unzipping this file for robot deployment: %s" % zip_file)
        zip_ref = zipfile.ZipFile(zip_file, 'r')
        zip_ref.extractall(deployment_dir)
        zip_ref.close()
        #print("Binaries and libs for deployment unpacked in: %s" % deployment_dir)
        lib_dir = self._place_libs(deployment_dir)
        self._place_bins(deployment_dir, lib_dir)
        return deployment_dir

    def _place_libs(self, deployment_dir, lib_dir=LIB_DIR, lib_files=LIB_FILES):
        # Move libs for deployment into a subdirectory
        lib_dir = os.path.join(deployment_dir, lib_dir)
        os.makedirs(lib_dir)
        for lib_file in lib_files:
            files_to_move = glob.glob(os.path.join(deployment_dir, lib_file))
            for file_to_move in files_to_move:
                #print("moving %s into %s" % (file_to_move, lib_dir))
                shutil.move(file_to_move, lib_dir)
        return lib_dir

    def _place_bins(self, deployment_dir, lib_dir, bin_dir=BIN_DIR,
                    file_types_to_skip=FILES_TYPES_TO_NOT_DEPLOY):
        # Move binaries for deployment into a subdirectory
        bin_dir = os.path.join(deployment_dir, bin_dir)
        os.makedirs(bin_dir)
        files_to_move = glob.glob(os.path.join(deployment_dir, "*"))
        for file_to_move in files_to_move:
            if file_to_move in [lib_dir, bin_dir]:
                continue
            file_type = os.path.splitext(file_to_move)[1]
            if file_type in file_types_to_skip:
                continue
            #print("moving %s into %s" % (file_to_move, bin_dir))
            shutil.move(file_to_move, bin_dir)

    def deploy(self, build_root):
        cmd = "export BUILD_ROOT=%s && source %s && eval $VICTOR_DEPLOY"
        cmd = cmd % (build_root, self.bash_cmds_script)
        run_command(cmd)

    def deploy_assets(self, assets_dir, force=True):
        if force:
            cmd = "export ASSETS_DIR=%s && source %s && eval $VICTOR_ASSETS_FORCE"
        else:
            cmd = "export ASSETS_DIR=%s && source %s && eval $VICTOR_ASSETS"
        cmd = cmd % (assets_dir, self.bash_cmds_script)
        run_command(cmd)

    def restart(self):
        cmd = "source %s && eval $VICTOR_RESTART" % self.bash_cmds_script
        run_command(cmd)


class AnimAssets(object):
    def __init__(self, anim_dir_env_var=ANIM_DIR_ENV_VAR):
        anim_dir = os.getenv(anim_dir_env_var)
        if not anim_dir or not os.path.isdir(anim_dir):
            raise ValueError("The $%s environment variable should point at a valid "
                             "animation directory" % anim_dir_env_var)
        self.local_assets_dir = os.path.dirname(anim_dir)
        self.assets_dir = tempfile.mkdtemp()
        self.resources_dir = os.path.join(self.assets_dir, "cozmo_resources")
        self.anim_data_dest_dir = os.path.join(self.resources_dir, "assets")
        os.makedirs(self.anim_data_dest_dir)
        self.add_config_data()

    def add_config_data(self, tools_dir_env_var=TOOLS_DIR_ENV_VAR,
                        bash_scripts_dir=BASH_SCRIPTS_DIR_RELATIVE_TO_TOOLS_DIR,
                        resources_subdirs=RESOURCES_SUBDIRS):
        tools_dir = os.getenv(tools_dir_env_var)
        if tools_dir and os.path.isdir(tools_dir):
             runtime_dir = os.path.join(tools_dir, bash_scripts_dir, "runtime")
             for subdir in resources_subdirs:
                 src_dir = os.path.join(runtime_dir, subdir)
                 dst_dir = os.path.join(self.resources_dir, subdir)
                 shutil.copytree(src_dir, dst_dir)

    def get_assets_dir(self):
        return self.assets_dir

    def unpack_anim_data(self, subdirs=ANIM_DATA_SUBDIRS, extract_types=EXTRACT_TYPES_FROM_TAR):
        anim_name_length_mapping = {}
        for subdir in subdirs:
            put_in_subdir = subdir in UNPACK_INTO_SUBDIR
            src = os.path.join(self.local_assets_dir, subdir)
            subdir = os.path.join(self.anim_data_dest_dir, subdir)
            shutil.copytree(src, subdir)
            try:
                anim_name_length_mapping.update(extract_files_from_tar(subdir, extract_types,
                                                                       put_in_subdir))
            except EnvironmentError as e:
                anim_name_length_mapping = {}
                print("Failed to unpack one or more tar files in [%s] because: %s" % (subdir, e))
            file_stats = get_file_stats(subdir)
            print("After unpacking tar files, '%s' contains the following files: %s"
                  % (os.path.basename(subdir), file_stats))
        if anim_name_length_mapping:
            self.write_animation_manifest(anim_name_length_mapping)

    def write_animation_manifest(self, anim_name_length_mapping, output_json_file=MANIFEST_FILE_NAME):
        all_anims = []
        for name, length in anim_name_length_mapping.items():
            manifest_entry = {}
            manifest_entry[MANIFEST_NAME_KEY] = name
            manifest_entry[MANIFEST_LENGTH_KEY] = length
            all_anims.append(manifest_entry)
        output_data = json.dumps(all_anims, sort_keys=False, indent=2, separators=(',', ': '))
        output_file = os.path.join(self.anim_data_dest_dir, output_json_file)
        if os.path.isfile(output_file):
            print("WARNING: Overwriting existing file: %s" % output_file)
            os.remove(output_file)
        with open(output_file, 'w') as fh:
            fh.write(output_data)
        print("The animation manifest file (with %s entries) = %s" % (len(all_anims), output_file))


class AndroidDebugBridge(object):

    def __init__(self, adb=ADB_SCRIPT):
        self.adb = adb
        try:
            self.check_version()
        except OSError as err:
            raise ValueError("Unable to use Android Debug Bridge (ADB) because: %s" % err) from None

    def connect_to_robot(self, ip_address, device_refused_suffix=ADB_DEVICE_REFUSED_SUFFIX):
        if ip_address is None:
            raise TypeError("Provide a valid IP address for the robot")
        self.start_server()
        cmd = self.adb + " connect " + ip_address
        status, stdout, stderr = run_command(cmd)
        connected = stdout.split(os.linesep)
        while '' in connected:
            connected.remove('')
        if connected and connected[0].endswith(device_refused_suffix):
            raise ValueError("The connection to robot was %s; try rebooting it" % device_refused_suffix)
        return stdout

    def check_connection(self, devices_header=ADB_DEVICES_HEADER,
                         device_avail_suffix=ADB_DEVICE_AVAIL_SUFFIX,
                         device_offline_suffix=ADB_DEVICE_OFFLINE_SUFFIX):
        self.start_server()
        cmd = self.adb + " devices"
        status, stdout, stderr = run_command(cmd)
        devices = stdout.split(os.linesep)
        while '' in devices:
            devices.remove('')
        while devices_header in devices:
            devices.remove(devices_header)
        if devices and devices[0].endswith(device_avail_suffix):
            return devices[0]
        elif devices and devices[0].endswith(device_offline_suffix):
            raise ValueError("The connected robot is %s; try rebooting it" % device_offline_suffix)
        else:
            raise ValueError("No connected robot or android device found")

    def check_version(self):
        cmd = self.adb + " version"
        status, stdout, stderr = run_command(cmd)
        return stdout

    def check_wifi_connection(self, prefix=NETSTATS_WIFI_CONNECTION_PREFIX,
                              network_id_token=NETSTATS_WIFI_NETWORK_ID_TOKEN):
        networks = []
        self.start_server()
        cmd = self.adb + " shell dumpsys netstats"
        status, stdout, stderr = run_command(cmd)
        if stdout:
            regex = re.compile('.*%s="(.*)".*' % network_id_token)
            for stdout_line in stdout.split(os.linesep):
                stdout_line = stdout_line.strip()
                if stdout_line.startswith(prefix):
                    matches = regex.match(stdout_line)
                    network_name = matches.group(1)
                    if network_name:
                        networks.append(network_name)
        if networks:
            # remove any duplicate entries in the list of networks
            networks = list(set(networks))
        #print("Current wifi networks = %s" % networks)
        return networks

    def disconnect(self):
        cmd = self.adb + " disconnect"
        status, stdout, stderr = run_command(cmd)
        time.sleep(1)
        return stdout

    def kill_server(self):
        cmd = self.adb + " kill-server"
        status, stdout, stderr = run_command(cmd)
        time.sleep(1)
        return stdout

    def start_server(self):
        cmd = self.adb + " start-server"
        status, stdout, stderr = run_command(cmd)
        time.sleep(1)
        return stdout

#    def check_running_processes(self):
#        running_processes = []
#        cmd = self.adb + " shell ps"
#        status, stdout, stderr = run_command(cmd)
#        if stdout:
#            ps_lines = stdout.split(os.linesep)
#            for idx in range(1, len(ps_lines)):
#                # skip first line since that is the column headers
#                ps_line = ps_lines[idx]
#                if not ps_line:
#                    continue
#                ps_line = ps_line.strip()
#                if not ps_line:
#                    continue
#                running_processes.append(ps_line.split()[-1])
#        #print("There are currently %s processes running on the connected device"
#        #      % len(running_processes))
#        return running_processes


def install_python_package_from_git(git_url, branch):
    dir_prefix = git_url.split(os.sep)[-1]
    if dir_prefix.endswith(".git"):
        dir_prefix = dir_prefix[:-4]
    clone_dir = branch + '_' + str(uuid.uuid4())
    clone_dir = os.path.join(os.environ["HOME"], dir_prefix, clone_dir)
    os.makedirs(clone_dir)
    print("Created directory: %s" % clone_dir)
    clone_cmd = "git clone -b %s %s %s" % (branch, git_url, clone_dir)
    status, stdout, stderr = run_command(clone_cmd)

    # TODO: Verify that "git clone ..." returns a non-zero exit status when it
    # fails, particularly when it fails because:
    #
    #     Executable requires at least macOS 10.12, but is being run
    #     on macOS 10.11.6, and so is exiting.
    #
    # If that fails WITH an exit status of zero, we should check stdout.lower()
    # and stderr.lower() for "error" and raise an exception here if an error is
    # detected in that manner.

    pip.main(['install', '--no-dependencies', '--ignore-installed', '-e', clone_dir])


def check_git_tools():
    # Use this function to check the machine's command-line Git tools BEFORE uninstalling
    # any packages to increase the odds that the subsequent installations will succeed.
    git_version_cmd = "git --version"
    status, stdout, stderr = run_command(git_version_cmd)
    return stdout


def _get_fq_wheel_files(wheel_files, zip_file, files_source_dir, zip_subdir=None):
    fq_wheel_files = []
    if zip_file:
        temp_dir = tempfile.mkdtemp()
        zip_file = check_file_and_return_full_path(zip_file, files_source_dir)
        zip_ref = zipfile.ZipFile(zip_file, 'r')
        zip_ref.extractall(temp_dir)
        zip_ref.close()
        files_source_dir = os.path.join(temp_dir, os.path.splitext(os.path.basename(zip_file))[0])
        if zip_subdir:
            files_source_dir = os.path.join(files_source_dir, zip_subdir)
    for wheel_file in wheel_files:
        wheel_file = check_file_and_return_full_path(wheel_file, files_source_dir)
        fq_wheel_files.append(wheel_file)
    return fq_wheel_files


def install_python_sdk(packages=[COZMO_SDK_PYTHON, COZMO_CLAD_PYTHON],
                       wheel_files=[COZMO_CLAD_WHEEL_FILE, COZMO_SDK_WHEEL_FILE],
                       zip_file=SDK_INSTALLER_ZIP_FILE, zip_subdir=SDK_INSTALLER_ZIP_FILE_SUBDIR,
                       files_source_dir=None, force_uninstall=False):
    fq_wheel_files = _get_fq_wheel_files(wheel_files, zip_file, files_source_dir, zip_subdir)
    for package in packages:
        pip.main(['uninstall', '--yes', package])
        if force_uninstall:
            time.sleep(1)
            package_dir = os.path.join(pip.locations.site_packages, package)
            try:
                shutil.rmtree(package_dir)
            except FileNotFoundError:
                pass
    time.sleep(3)
    for wheel_file in fq_wheel_files:
        pip.main(['install', '--ignore-installed', '--no-dependencies', wheel_file])


def install_python_sdk_from_git(packages=[COZMO_SDK_PYTHON, COZMO_CLAD_PYTHON],
                                wheel_files=[COZMO_CLAD_WHEEL_FILE],
                                files_source_dir=None,
                                git_url=GIT_SSH, git_branch=GIT_BRANCH):
    if git_url and git_branch:
        # Check git tools BEFORE uninstalling anything.
        check_git_tools()
    install_python_sdk(packages, wheel_files, zip_file=None, files_source_dir=files_source_dir)
    if git_url and git_branch:
        install_python_package_from_git(git_url, git_branch)


def get_highest_file_and_return_full_path(file_name, source_dir):
    if not file_name:
        raise ValueError("Invalid file: %s" % file_name)
    if file_name.startswith(os.sep) or source_dir is None:
        fq_files = glob.glob(file_name)
    else:
        if not source_dir or not os.path.isdir(source_dir):
            raise ValueError("Invalid directory: %s" % source_dir)
        fq_files = glob.glob(os.path.join(source_dir, file_name))
    if not fq_files:
        raise ValueError("Invalid file: %s" % file_name)
    fq_files.sort()
    fq_files.reverse()
    for fq_file in fq_files:
        if os.path.isfile(fq_file):
            return fq_file
    raise ValueError("Invalid files: %s" % fq_files)


def check_file_and_return_full_path(file_name, source_dir):
    if not file_name:
        raise ValueError("Invalid file: %s" % file_name)
    if file_name.startswith(os.sep) or source_dir is None:
        fq_file = file_name
    else:
        if not source_dir or not os.path.isdir(source_dir):
            raise ValueError("Invalid directory: %s" % source_dir)
        fq_file = os.path.join(source_dir, file_name)
    if not os.path.isfile(fq_file):
        raise ValueError("Invalid file: %s" % fq_file)
    return fq_file


def android_main(args, install_files_source_dir=INSTALL_FILES_SOURCE_DIR,
                 expected_wifi_network_prefix=EXPECTED_WIFI_NETWORK_PREFIX):

    # When installing, install both apps (cozmo and standalone engine) and then launch regular
    # cozmo app.  User should connect to their robot using that, allowing it to update the
    # firmware if needed.  Once the robot is up and running (in FreePlay), this android_main()
    # function can be triggered again (without the install flag set) to kill the regular cozmo
    # app and run the standalone engine instead.

    #app_mgr = AndroidAppsManager()
    adb = AndroidDebugBridge()

    # Always kill the running processes, whether stopping, starting or installing
    #adb.stop_processes()
    #app_mgr.stop_apps()

    if INSTALL_FLAG in args:
        if not install_files_source_dir.startswith(os.sep):
            install_files_source_dir = os.path.join(os.environ["HOME"], install_files_source_dir)
        if SDK_ONLY_FLAG not in args:
            installed_files = app_mgr.install_apps(files_source_dir=install_files_source_dir)
            print("Installed: %s" % installed_files)
        if NO_SDK_FLAG not in args:
            install_python_sdk(files_source_dir=install_files_source_dir)
    elif STOP_FLAG in args:
        app_mgr.adb.kill_server()
    else:
        networks = app_mgr.adb.check_wifi_connection()
        if not networks:
            raise ValueError("No connected wifi robot/network found")
        wifi_network = networks[0]
        if not wifi_network.lower().startswith(expected_wifi_network_prefix.lower()):
            raise ValueError("Device is currently connected to '%s', not a '%s' robot/network"
                             % (wifi_network, expected_wifi_network_prefix))

    app_status = app_mgr.check_if_apps_running()


def _get_robot_ip_address(args):
    for arg in args:
        if not arg.startswith('-'):
            count = 0
            try:
                for address_part in arg.split('.'):
                    address_part = int(address_part)
                    count += 1
            except (TypeError, ValueError):
                continue
            if count == 4:
                # We have four integers separated by a dot, so assume it is a valid IP address
                return arg
    return None


def install_robot():
    assets = AnimAssets()
    assets.unpack_anim_data()
    robot = RobotDeploy()
    build_root = robot.prepare()
    robot.deploy(build_root)
    assets_dir = assets.get_assets_dir()
    robot.deploy_assets(assets_dir)
    robot.restart()
    print("Robot installation and restart completed")

    # Remove the two temp directories where the robot binaries & libs
    # and the animation assets were unpacked
    shutil.rmtree(build_root)
    shutil.rmtree(assets_dir)


def main(args, install_files_source_dir=INSTALL_FILES_SOURCE_DIR):

    if not install_files_source_dir.startswith(os.sep):
        install_files_source_dir = os.path.join(os.environ["HOME"], install_files_source_dir)

    if INSTALL_SDK_FLAG in args:
        install_python_sdk_from_git(files_source_dir=install_files_source_dir)

    elif DISCONNECT_FLAG in args:
        adb = AndroidDebugBridge()
        adb.disconnect()
        adb.kill_server()
        print("Disconnected everything and killed adb server")
        return None

    elif CONNECT_FLAG in args or INSTALL_ROBOT_FLAG in args or RESTART_FLAG in args:
        if RESTART_FLAG in args:
            restart_robot = True
        else:
            restart_robot = False
        adb = AndroidDebugBridge()
        try:
            device = adb.check_connection()
        except ValueError:
            robot_ip_address = _get_robot_ip_address(args)
            adb.connect_to_robot(robot_ip_address)
            restart_robot = True
            time.sleep(10)
            device = adb.check_connection()
        if INSTALL_ROBOT_FLAG in args:
            install_robot()
        else:
            if restart_robot:
                # restart robot now if that was explicitly requested or we just reconnected to it
                robot = RobotDeploy()
                robot.restart()
            device = device.split()[0]
            print("Connected to device %s" % device)

    else:
        adb = AndroidDebugBridge()
        device = adb.check_connection()


if __name__ == "__main__":
    main(sys.argv[1:])


