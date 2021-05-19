#!/usr/bin/env python


IP_ADDRESS = "192.168.XX.XX"

DEFAULT_VOLUME = 5

POLL_TIMEOUT = 0.5

START_INDEX = 1

END_INDEX = 10000

OUTPUTLOG = None

FILEID = None

import os
import sys
import time
import signal
import requests
import argparse

'''
                python play_all_animations.py 192.168.1.255
                will play each animation loaded on the robot at IP address 192.168.1.255
                it queries the list all anims page and then plays
                one, waits for the anim state on the robot to be idle again
                then plays the next one
                
                the script will use the IP entered as an argument first, then tries the hardcoded one
                if you see this error:
                ImportError: No module named requests
                
                type in this:
                pip install requests
                
                chris rogers 8/2018
                (c) anki, inc.
'''



ANIM_PORT = "8889"
ENGINE_PORT = "8888"

SLEEP_ANIM_CLIP = 'anim_face_sleeping'

LIST_ANIMS_CMD = 'http://{0}:{1}/consolefunccall?func=ListAnimations'
SHOW_CURRENT_ANIM_CMD = 'http://{0}:{1}/consolefunccall?func=ShowCurrentAnimation'
QUERY_ANIM_CMD = 'http://{0}:{1}/consolefunccall?func=ShowCurrentAnimation'
ABORT_ANIM_CMD = 'http://{0}:{1}/consolefunccall?func=AbortCurrentAnimation'
BATTERY_STATS_CMD = 'http://{0}:8888/getenginestats?1000000000000000000000000000000000000'
VOLUME_CMD1 = 'http://{0}:{1}/consolevarset?key=MasterVolumeLevel&value={2}'
VOLUME_CMD2 = 'http://{0}:{1}/consolefunccall?func=DebugSetMasterVolume&args='


globalStartTime = time.time()

_playedAnims = []


parser = argparse.ArgumentParser()
parser.add_argument("-i","--ip_address", help="ip address of robot to connect to.")
parser.add_argument("-t","--timeout", help="timeout value waiting for the robot to respond to 'are you currently playing animation?' default is 0.5 try 1 or 2 if you have timeout errors.")
parser.add_argument("-s","--start", help="index of first animation to play")
parser.add_argument("-e","--end", help="index of last animation to play")
parser.add_argument("-v","--volume", help="volume level (0-5)")
parser.add_argument("-o","--outputlog", help="file to log output")


args = parser.parse_args()



if args.ip_address: IP_ADDRESS = args.ip_address
if args.start: START_INDEX = int(args.start)
if args.end: END_INDEX = int(args.end)
if args.timeout: POLL_TIMEOUT = float(args.timeout)
if args.volume: DEFAULT_VOLUME = int(args.volume)
DEFAULT_VOLUME = int(max(min(DEFAULT_VOLUME, 5), 0))
if args.outputlog: OUTPUTLOG = args.outputlog

print ("ip=         ",IP_ADDRESS)
print ("start=      ",START_INDEX)
print ("end=        ",END_INDEX)
print ("timeout=    ",POLL_TIMEOUT)
print ("volume=     ",DEFAULT_VOLUME)
print ("outputlog=  ",OUTPUTLOG)




# this is to report the total time even if there was a Ctrl-C or other exception
def endScript(sig=None, frame=None):
    elapsedTime = time.time() - globalStartTime
    send(os.linesep + "End time: {0}".format(time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())))
    send("Total time = {0:.2f} seconds for {1} animations".format(elapsedTime, len(_playedAnims)))
    if FILEID is not None:
        FILEID.close()
    sys.exit(0)

signal.signal(signal.SIGINT, endScript)

# function to print to screen and/maybe the output log
def send(o):
    print(o)
    if FILEID is not None:
        try:
            FILEID.writelines(o)
            FILEID.flush()
        except:
            print("problem writing line to file")

def changeVolume(ipAddress, vol):
    cmd1 = VOLUME_CMD1.format(ipAddress, ENGINE_PORT, vol)
    cmd2 = VOLUME_CMD2.format(ipAddress, ENGINE_PORT)
    try:
        r1 = requests.post(cmd1, timeout=POLL_TIMEOUT)
        r2 = requests.post(cmd2, timeout=POLL_TIMEOUT)
    except:
        send(os.linesep + "Failed to change volume: {0}".format(cmd1))
    else:
        if r1.status_code == 200:  # http OK
            send("volume changed to {0}.".format(vol))


def waitForAnim(ipAddress, startTime):
    url = SHOW_CURRENT_ANIM_CMD.format(ipAddress, ANIM_PORT)
    # 300 loops as a failsafe timeout
    for i in range(300):
        queryTime = time.time()
        r = None
        try:
            r = requests.get(url, timeout=POLL_TIMEOUT)
        except requests.ConnectTimeout:
            send("query anim state timed out")
        currentTime = time.time()
        #duration = currentTime - queryTime
        #send("request duration=", duration)
        playTime = currentTime - startTime
        #send("total duration={0:.2f}".format(playTime))
        time.sleep(0.1)
        if r is None:
            continue
        if 'anim' in r.text and SLEEP_ANIM_CLIP not in r.text:
            clip = r.text.split('anim_')[1]
            clip = clip.split('</html>')[0].strip()
            #send(clip)
        else:
            #send("done playing animation")
            return playTime
    return None


def getAllAnims(ipAddress):
    # return list of all anims
    allAnims = []
    url = LIST_ANIMS_CMD.format(ipAddress, ANIM_PORT)
    try:
        r = requests.get(url, timeout=5)
    except requests.exceptions.ConnectTimeout:
        send(os.linesep + "Failed to query all animations")
        return allAnims
    lines = r.content.split(os.linesep)
    for l in lines:
        if 'console' not in l:
            continue
        words = l.strip().split('"')
        nurl = words[1]
        allAnims.append(nurl)
    # chop array by start and end
    allAnims = allAnims[START_INDEX:END_INDEX]
    send ("Number of Animations to play: {0}".format(len(allAnims)))
    return allAnims


def playAnims(ipAddress, animList, showBatteryLevel=True):
    count = START_INDEX
    for a in animList:
        url = "http://{0}:{1}/{2}".format(ipAddress, ANIM_PORT, a)
        animName = a.split("args=")[1].split("+")[0]
        _playedAnims.append(animName)
        send(os.linesep + "Playing animation: %s  " % animName)
        r = requests.get(url)
        startTime = time.time()
        time.sleep(1)
        playTime = waitForAnim(ipAddress, startTime)
        if playTime is None:
            send("Warning: timed out playing {0}".format(animName))
        else:
            send("Done playing index:{2} {0} in {1:.2f} seconds ".format(animName, playTime, count))
        if showBatteryLevel:
            try:
                r = requests.get(BATTERY_STATS_CMD.format(ipAddress), timeout=POLL_TIMEOUT)
            except requests.exceptions.ConnectTimeout:
                continue
            batteryLevel = r.content.split(os.linesep)[0]
            send("(battery level {0} at {1})".format(batteryLevel, time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())))
        count += 1

def main(ipAddress=IP_ADDRESS, vol=DEFAULT_VOLUME):
    global globalStartTime, FILEID
    globalStartTime = time.time()

    if 'XX' in ipAddress:
        msg = "Pass in the IP address as an argument or update the constant at the top of this file"
        raise ValueError(msg)

    if OUTPUTLOG is not None:
        try:
            FILEID = open(OUTPUTLOG,'w')
            print "opening outputlog: {0}".format(OUTPUTLOG)
        except:
            print "there was a problem opening the log file: {0}".format(OUTPUTLOG)

    send("Robot IP address = {0}".format(ipAddress))
    send("Start time: {0}".format(time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())))
    if vol is not None:
        changeVolume(ipAddress, vol)
    allAnims = getAllAnims(ipAddress)
    playAnims(ipAddress, allAnims)
    endScript()


if __name__ == '__main__':
    main()


