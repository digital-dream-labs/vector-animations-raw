

HOSTNAME = "localhost"
LOCAL_PORT_NUM = 8080
DEVICE_PORT_NUM = 2223  # This port must match what is used on the device
MOBILEDEVICE = "/usr/local/bin/mobiledevice"
LSOF = "/usr/sbin/lsof"
USBMUX_DAEMON_NAME = "usbmuxd"
DEFAULT_TUNNEL_TIMEOUT = 1000 # milliseconds
TUNNELING_MSG = "Tunneling from local port %s to device port %s..."
PORT_USED_MSG = "Process with pid = %s is %s tunneling to device"
FAILURE_MSG = "Failed to enable preview on robot!  Is any device connected via USB cable?"
CONNECTION_REFUSED_STRING = "Device refused connection"
NOT_ENABLED_MSG = "Preview on robot not enabled"


# This global variable is set to the output file that is currently receiving updates from mobiledevice
_tunneling_output_file = None


import sys
import os
import errno
import subprocess
import json
import tempfile
import tarfile
import time

from ankiutils.anim_files import get_newest_json_file, get_json_file_for_anim, report_file_stats
from facial_animation import get_facial_anims, get_facial_png_files, FACIAL_ANIM_DIR

from maya import cmds


# 1. Get some anim file (the last one exported by default)
# 2. make sure mobiledevice lib is running


def get_pid_using_local_port(lsof=LSOF, port=LOCAL_PORT_NUM):
    if not os.path.isfile(lsof):
        cmds.warning("File missing: %s" % lsof)
        return None
    lsof_cmd = "%s -Fp -i :%s" % (lsof, port)
    p = subprocess.Popen(lsof_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    stdout, stderr = p.communicate()
    stdout = stdout.strip()
    stderr = stderr.strip()
    status = p.poll()
    if status != 0:
        if stderr:
            print(stderr)
        return None
    pid = long(stdout[1:])
    return pid


def kill_usbmux_daemon(daemon_name=USBMUX_DAEMON_NAME):
    # TODO: If we need to get this working, we'll need to figure out the password/authentication
    #       for this sudo command, eg. set sudo passwords to NOT timeout in /etc/sudoers and have
    #       animators enter their password once or something along those lines.
    kill_cmd = "sudo killall -9 %s" % daemon_name
    p = subprocess.Popen(kill_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    stdout, stderr = p.communicate()
    stdout = stdout.strip()
    stderr = stderr.strip()
    status = p.poll()
    if status != 0:
        if stdout:
            print(stdout)
    if stderr:
        print(stderr)


def enable_preview_on_robot(mobiledevice=MOBILEDEVICE, local_port=LOCAL_PORT_NUM,
                            device_port=DEVICE_PORT_NUM, send_output_to_file=False,
                            tunnel_timeout=DEFAULT_TUNNEL_TIMEOUT):
    global _tunneling_output_file
    pid = get_pid_using_local_port(port=local_port)
    if pid is not None:
        cmds.warning(PORT_USED_MSG % (pid, "already"))
        return None
    if not os.path.isfile(mobiledevice):
        cmds.warning("File missing: %s" % mobiledevice)
        return None
    md_cmd = "%s tunnel -t %s %s %s" % (mobiledevice, tunnel_timeout, local_port, device_port)
    #print("Running: %s" % md_cmd)
    if send_output_to_file:
        (fd, output_file) = tempfile.mkstemp(prefix="preview_on_robot_", suffix=".log")
        #print(output_file)
        p = subprocess.Popen(md_cmd, stdout=fd, stderr=fd, shell=True)
    else:
        output_file = None
        p = subprocess.Popen(md_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    time.sleep(3)
    status = p.poll()
    if status is None:
        # process is now running
        print(TUNNELING_MSG % (local_port, device_port))
        _tunneling_output_file = output_file
    else:
        stdout, stderr = p.communicate()
        if status == 0:
            if stdout:
                stdout = stdout.strip()
                print(stdout)
        elif stderr:
            stderr = stderr.strip()
            print(stderr)
    pid = get_pid_using_local_port(port=local_port)
    if pid is None:
        cmds.warning(FAILURE_MSG)
    else:
        print PORT_USED_MSG % (pid, "now"),


def play_anim_on_robot(anim_file, post_cmd="cmd_anim_update", host=HOSTNAME, port=LOCAL_PORT_NUM):
    anim_name = os.path.splitext(os.path.basename(anim_file))[0]
    curl_cmd = 'curl -d "@%s" %s:%s/%s/%s' % (anim_file, host, port, post_cmd, anim_name)
    print("Running: %s" % curl_cmd)
    os.system(curl_cmd)

def prepare_robot(post_cmd="cmd_prepare_robot", host=HOSTNAME, port=LOCAL_PORT_NUM):
    curl_cmd = 'curl -d "%s" %s:%s/%s' % (post_cmd, host, port, post_cmd)
    print("Running: %s" % curl_cmd)
    os.system(curl_cmd)

def setup_facial_anims_on_device(facial_anim, post_cmd="cmd_face_anim_setup", host=HOSTNAME, port=LOCAL_PORT_NUM):
    curl_cmd = 'curl -d "%s" %s:%s/%s/%s' % (facial_anim, host, port, post_cmd, facial_anim)
    print("Running: %s" % curl_cmd)
    os.system(curl_cmd)

def copy_png_file_to_device(png_file, facial_anim, post_cmd="cmd_face_anim_install", host=HOSTNAME, port=LOCAL_PORT_NUM):
    curl_cmd = 'curl --data-binary "@%s" %s:%s/%s/%s/%s' % (png_file, host, port, post_cmd, facial_anim, os.path.basename(png_file))
    print("Running: %s" % curl_cmd)
    os.system(curl_cmd)

def refresh_facial_anims_on_device(facial_anim, post_cmd="cmd_face_anim_refresh", host=HOSTNAME, port=LOCAL_PORT_NUM):
    curl_cmd = 'curl -d "%s" %s:%s/%s/%s' % (facial_anim, host, port, post_cmd, facial_anim)
    print("Running: %s" % curl_cmd)
    os.system(curl_cmd)


def update_facial_anims_on_robot(facial_anims, source_dir):
    for facial_anim in facial_anims:
        try:
            png_files = get_facial_png_files(facial_anim, source_dir)
        except (RuntimeError, ValueError), e:
            cmds.warning(str(e))
            continue
        setup_facial_anims_on_device(facial_anim)
        for png_file in png_files:
            copy_png_file_to_device(png_file, facial_anim)
        refresh_facial_anims_on_device(facial_anim)


def main(anim_name=None):
    export_path = os.getenv("ANKI_ANIM_EXPORT_PATH")
    if export_path:
        try:
            if anim_name:
                anim_file = get_json_file_for_anim(anim_name, export_path)
            else:
                anim_file = get_newest_json_file(export_path)
        except ValueError, e:
            cmds.warning(str(e))
            return None
        if anim_file:

            # TODO: Uncomment the following line after merging the PR 3382 changes (COZMO-9539)
            #prepare_robot()

            facial_anims = get_facial_anims(anim_file)
            if facial_anims:
                anim_tar_file_dir = os.getenv("ANKI_ANIM_DIR")
                png_tar_file_dir = os.path.join(os.path.dirname(anim_tar_file_dir), FACIAL_ANIM_DIR)
                update_facial_anims_on_robot(facial_anims, png_tar_file_dir)
            fh = None
            if _tunneling_output_file:
                fh = open(_tunneling_output_file, 'r')
                # seek to the end of the file
                fh.seek(0,2)
            play_anim_on_robot(anim_file)
            if fh:
                # read any output that was added to the file by THIS call to play_anim_on_robot()
                play_output = fh.read().strip()
                fh.close()
                if not play_output:
                    cmds.warning(NOT_ENABLED_MSG)
                elif CONNECTION_REFUSED_STRING in play_output:
                    cmds.warning(play_output.split(os.linesep)[-1])
                else:
                    print(play_output)
                    file_stat_msg = report_file_stats(anim_file)
                    print file_stat_msg,
            else:
                file_stat_msg = report_file_stats(anim_file)
                print file_stat_msg,
    else:
        raise ValueError("Please ensure that ANKI_ANIM_EXPORT_PATH is set in the Maya.env file")


