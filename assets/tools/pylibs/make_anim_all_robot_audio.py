#!/usr/bin/env python

SVN_REPO_WITH_TOOLS = "victor-animation"

GIT_REPO = "victor"


import os
import sys
import json
from ankimaya import audio_core


ANIM_NAME = "anim_factory_audio_test_all_sounds"

AUDIO_EVENT_DURATION = 1000 # milliseconds

START_TIME = 33 # milliseconds

SKIP_EVENTS = ["Play__Dev_Robot__External_Source", "Play__Robot_Vo__Test"]


def setup_environment(project_root_var="ANKI_PROJECT_ROOT", tools_root_var="ANKI_TOOLS"):
    home_dir = os.getenv("HOME")
    project_root = os.getenv(project_root_var)
    if not project_root:
        project_root = os.path.join(home_dir, "workspace", GIT_REPO)
        os.environ[project_root_var] = project_root
    tools_root = os.getenv(tools_root_var)
    if not tools_root:
        tools_root = os.path.join(home_dir, "workspace", SVN_REPO_WITH_TOOLS, "tools")
        os.environ[tools_root_var] = tools_root


def make_audio_keyframe(event_name, event_id, trigger_time):
    keyframe = audio_core.getDefaultAudioJson()
    keyframe[audio_core.EVENT_NAME_ATTR] = [event_name]
    keyframe[audio_core.AUDIO_ID_ATTR] = [event_id]
    #keyframe[audio_core.TRIGGER_TIME_ATTR] = convert_time(audioKeyframes[AUDIO_ENUM_ATTR][1][idx], offset=clip_start)
    keyframe[audio_core.TRIGGER_TIME_ATTR] = trigger_time
    return keyframe


def get_all_audio_events():
    event_names, event_mapping = audio_core.loadAudioAttrsFromPy()
    for event in event_names:
        if event not in event_mapping:
            raise ValueError("The '%s' event is missing from the event name -> ID mapping" % event)
    print("There are %s audio events" % len(event_mapping))
    return event_mapping


def write_json_file(anim_name, keyframes):
    json_dict = {anim_name : keyframes}
    output_json = json.dumps(json_dict, sort_keys=False, indent=2, separators=(',', ': '))
    output_file = os.path.join(os.getcwd(), anim_name + ".json")
    if os.path.isfile(output_file):
        raise ValueError("Move or delete existing %s file and then run this again" % output_file)
    with open(output_file, 'w') as fh:
        fh.write(output_json)
    print("Wrote file: %s" % output_file)
    return output_file


def main(anim_name=ANIM_NAME, skip_events=None,
         start_time=START_TIME, audio_event_duration=AUDIO_EVENT_DURATION,
         start_anim_event=audio_core.DEFAULT_AUDIO_EVENT,
         end_anim_event=audio_core.DEFAULT_AUDIO_EVENT):
    if skip_events is None:
        skip_events = SKIP_EVENTS
    keyframes = []
    setup_environment()
    event_mapping = get_all_audio_events()
    trigger_time = start_time
    keyframes.append(make_audio_keyframe(start_anim_event, event_mapping[start_anim_event], trigger_time))
    trigger_time += audio_event_duration
    for name, id in event_mapping.items():
        for skip_event in skip_events:
            if name.startswith(skip_event):
                name = None
                break
        if name is None:
            continue
        if name.lower().endswith("loop_stop"):
            # The loop stop events are placed immediately after the loop play events; see below
            continue
        keyframes.append(make_audio_keyframe(name, id, trigger_time))
        trigger_time += audio_event_duration
        if name.lower().endswith("loop_play"):
            loop_stop_name = name.replace("play", "stop")
            loop_stop_name = loop_stop_name.replace("Play", "Stop")
            loop_stop_name = loop_stop_name.replace("PLAY", "STOP")
            loop_stop_id = event_mapping[loop_stop_name]
            keyframes.append(make_audio_keyframe(loop_stop_name, loop_stop_id, trigger_time))
            trigger_time += audio_event_duration
    keyframes.append(make_audio_keyframe(end_anim_event, event_mapping[end_anim_event], trigger_time))
    output_file = write_json_file(anim_name, keyframes)
    return output_file


if __name__ == '__main__':
    main()


