#!/usr/bin/env python


PS_CMD = "ps -eo pid,args"
PID_HEADER = "PID"

PROCESS_NAME_FLAG = "-process_name"
KILL_FLAG = "-kill"


import os
import sys
import subprocess
import signal


def get_flag_value(args, flag):
    try:
        flag_idx = args.index(flag)
    except ValueError:
        return None
    try:
        flag_value = args[flag_idx + 1]
    except IndexError:
        return None
    else:
        return flag_value


def get_process_name_value(args, process_name_flag=PROCESS_NAME_FLAG):
    return get_flag_value(args, process_name_flag)


def get_kill_value(args, kill_flag=KILL_FLAG):
    if kill_flag in args:
        return True
    return False


def get_all_pids(ps_cmd=PS_CMD, pid_header=PID_HEADER):
    pid_mapping = {}
    p = subprocess.Popen(ps_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    stdout, stderr = p.communicate()
    stdout = stdout.strip()
    stderr = stderr.strip()
    status = p.poll()
    if status != 0:
        msg = "Unable to lookup all running pids"
        if stderr:
            msg += "..." + os.linesep + stderr
        raise RuntimeError(msg)
    pids = stdout.split(os.linesep)
    for pid in pids:
        pid = pid.strip()
        pid, process_name = pid.split(' ', 1)
        if pid == pid_header:
            continue
        pid = long(pid)
        pid_mapping[pid] = process_name
    return pid_mapping


def main(args, process_name=None, kill=None):
    pids = []
    if not process_name:
        process_name = get_process_name_value(args)
    if not process_name:
        raise ValueError("Provide a process name for which pids should be returned")
    if kill is None:
        kill = get_kill_value(args)
    pid_mapping = get_all_pids()
    this_pid = long(os.getpid())
    print("pid of this process = %s" % this_pid)
    print("number of pids = %s" % len(pid_mapping))
    for pid, proc_name in pid_mapping.items():
        if process_name in proc_name:
            if pid != this_pid:
                pids.append(pid)
            print("%s: %s" % (pid, proc_name))
    if kill:
        for pid in pids:
            if pid == this_pid:
                continue
            os.kill(pid, signal.SIGKILL)
            print("killed process with pid = %s" % pid)
    return pids


if __name__ == "__main__":
    main(sys.argv[1:])


