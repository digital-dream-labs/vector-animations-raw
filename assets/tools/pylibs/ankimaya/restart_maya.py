import os
import sys
import subprocess
import time
import socket


DEBUG = True

stdout_pipe = subprocess.PIPE
stderr_pipe = subprocess.PIPE


def run_command_core(cmd, stdout_pipe=stdout_pipe, stderr_pipe=stderr_pipe, shell=False, split=False):  # TODO add cwd
    if DEBUG:
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
    if DEBUG:
        print "cmd:status: ", status
        print "cmd:stdout: ", stdout
        print "cmd:stderr: ", stderr
    return (status, stdout, stderr)



APP = '/Applications/Autodesk/maya2018/Maya.app/Contents/bin/maya'

ADDR = '/tmp/commandPortDefault'

def SendCommand():
    try:
        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client.connect(ADDR)
        command = 'quit' # the command from external editor to maya

        MyMessage = command
        client.send(MyMessage)
        data = client.recv(1024)
        client.close()
        print 'The Result is %s' % data
    except:
        pass

    for i in range(60):
        cmd = 'ps -x | grep Maya.app'
        (status, stdout, stderr) =run_command_core(cmd, shell=True)
        if 'Maya.app' not in stdout:
            break
        time.sleep(0.1)



    cmd = 'open -a Maya'
    run_command_core(cmd,shell=True)

if __name__=='__main__':
     SendCommand()