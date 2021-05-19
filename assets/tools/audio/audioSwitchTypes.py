"""
Autogenerated python message buffer code.
Source: /Users/Ben.Gabaldon/victor/robot/clad/src/clad/audio/audioSwitchTypes.clad
Full command line: victor-clad/tools/message-buffers/emitters/Python_emitter.py robot/clad/src/clad/audio/audioSwitchTypes.clad
"""

from __future__ import absolute_import
from __future__ import print_function

def _modify_path():
  import inspect, os, sys
  search_paths = [
    'Ben.Gabaldon/victor/-',
    'Ben.Gabaldon/victor/victor-clad/tools/message-buffers/support/python',
  ]
  currentpath = os.path.abspath(os.path.dirname(inspect.getfile(inspect.currentframe())))
  for search_path in search_paths:
    search_path = os.path.normpath(os.path.abspath(os.path.realpath(os.path.join(currentpath, search_path))))
    if search_path not in sys.path:
      sys.path.insert(0, search_path)
_modify_path()

import msgbuffers

Anki = msgbuffers.Namespace()
Anki.AudioMetaData = msgbuffers.Namespace()
Anki.AudioMetaData.SwitchState = msgbuffers.Namespace()

class GenericSwitch(object):
  "Automatically-generated uint_32 enumeration."
  Invalid = 0

Anki.AudioMetaData.SwitchState.GenericSwitch = GenericSwitch
del GenericSwitch


class Robot_Vic_External_Input_Source(object):
  "Automatically-generated uint_32 enumeration."
  Invalid               = 0
  Streaming_Wave_Portal = 4272719686
  Wave_Portal           = 4178937859

Anki.AudioMetaData.SwitchState.Robot_Vic_External_Input_Source = Robot_Vic_External_Input_Source
del Robot_Vic_External_Input_Source


class Robot_Vic_External_Processing(object):
  "Automatically-generated uint_32 enumeration."
  Default_Processed = 1906807385
  Invalid           = 0
  Unprocessed       = 860658140

Anki.AudioMetaData.SwitchState.Robot_Vic_External_Processing = Robot_Vic_External_Processing
del Robot_Vic_External_Processing


class Robot_Vic_Head_Direction(object):
  "Automatically-generated uint_32 enumeration."
  Invalid                       = 0
  Robot_Vic_Head_Direction_Down = 3234804922
  Robot_Vic_Head_Direction_Up   = 123512153

Anki.AudioMetaData.SwitchState.Robot_Vic_Head_Direction = Robot_Vic_Head_Direction
del Robot_Vic_Head_Direction


class Robot_Vic_Lift_Direction(object):
  "Automatically-generated uint_32 enumeration."
  Invalid                       = 0
  Robot_Vic_Lift_Direction_Down = 3238791869
  Robot_Vic_Lift_Direction_Up   = 807633034

Anki.AudioMetaData.SwitchState.Robot_Vic_Lift_Direction = Robot_Vic_Lift_Direction
del Robot_Vic_Lift_Direction


class Robot_Vic_Mood_Switch(object):
  "Automatically-generated uint_32 enumeration."
  Angry     = 1206605712
  Curious   = 620622945
  Effort    = 2445358259
  Excited   = 2633337909
  Happy     = 1427264549
  Invalid   = 0
  Neutral   = 670611050
  Sad       = 443572635
  Surprised = 2662801688

Anki.AudioMetaData.SwitchState.Robot_Vic_Mood_Switch = Robot_Vic_Mood_Switch
del Robot_Vic_Mood_Switch


class Robot_Vic_Mvmt_Size(object):
  "Automatically-generated uint_32 enumeration."
  Invalid              = 0
  Robot_Vic_Mvmt_Long  = 3071588350
  Robot_Vic_Mvmt_Micro = 414260672
  Robot_Vic_Mvmt_Short = 3300471426

Anki.AudioMetaData.SwitchState.Robot_Vic_Mvmt_Size = Robot_Vic_Mvmt_Size
del Robot_Vic_Mvmt_Size


class Robot_Vic_Scrn_Procedural_Shift_Length(object):
  "Automatically-generated uint_32 enumeration."
  Invalid     = 0
  Shift_Long  = 3156794696
  Shift_Short = 3265274760

Anki.AudioMetaData.SwitchState.Robot_Vic_Scrn_Procedural_Shift_Length = Robot_Vic_Scrn_Procedural_Shift_Length
del Robot_Vic_Scrn_Procedural_Shift_Length


class Robot_Vic_Stim_Switch(object):
  "Automatically-generated uint_32 enumeration."
  Invalid = 0
  Stim_01 = 446181668
  Stim_02 = 446181671
  Stim_03 = 446181670
  Stim_04 = 446181665

Anki.AudioMetaData.SwitchState.Robot_Vic_Stim_Switch = Robot_Vic_Stim_Switch
del Robot_Vic_Stim_Switch


class Robot_Vic_Stim_Switch_Old_Reference_Only(object):
  "Automatically-generated uint_32 enumeration."
  Invalid = 0
  Stim_01 = 446181668
  Stim_02 = 446181671
  Stim_03 = 446181670
  Stim_04 = 446181665

Anki.AudioMetaData.SwitchState.Robot_Vic_Stim_Switch_Old_Reference_Only = Robot_Vic_Stim_Switch_Old_Reference_Only
del Robot_Vic_Stim_Switch_Old_Reference_Only


class Robot_Vic_Tread_Drive(object):
  "Automatically-generated uint_32 enumeration."
  Invalid               = 0
  Robot_Vic_Tread_Drive = 4283612440
  Robot_Vic_Tread_Spin  = 2961118536

Anki.AudioMetaData.SwitchState.Robot_Vic_Tread_Drive = Robot_Vic_Tread_Drive
del Robot_Vic_Tread_Drive


class Robot_Vic_Tread_Speed(object):
  "Automatically-generated uint_32 enumeration."
  Invalid                  = 0
  Robot_Vic_Tread_Backward = 3258446947
  Robot_Vic_Tread_Forward  = 1541107887

Anki.AudioMetaData.SwitchState.Robot_Vic_Tread_Speed = Robot_Vic_Tread_Speed
del Robot_Vic_Tread_Speed


class SwitchGroupType(object):
  "Automatically-generated uint_32 enumeration."
  Invalid                                  = 0
  Robot_Vic_External_Input_Source          = 3465152049
  Robot_Vic_External_Processing            = 475135532
  Robot_Vic_Head_Direction                 = 358594767
  Robot_Vic_Lift_Direction                 = 3690255634
  Robot_Vic_Mood_Switch                    = 1492705913
  Robot_Vic_Mvmt_Size                      = 1553011127
  Robot_Vic_Scrn_Procedural_Shift_Length   = 1706342803
  Robot_Vic_Stim_Switch                    = 2087220263
  Robot_Vic_Stim_Switch_Old_Reference_Only = 2717392740
  Robot_Vic_Tread_Drive                    = 4283612440
  Robot_Vic_Tread_Speed                    = 724346585

Anki.AudioMetaData.SwitchState.SwitchGroupType = SwitchGroupType
del SwitchGroupType


