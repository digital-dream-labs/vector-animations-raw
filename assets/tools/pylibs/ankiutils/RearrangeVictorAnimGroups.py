import os
import subprocess
from pprint import pprint
import sys

"""
        this script creates (sortof) an SVN changelist
        to organize animationGroup.json files into
        directories determined by their feature name extracted
        from the file name
        
        chris rogers 7/2018
        (c) anki 2018


"""

# LIVE = True to actually execute SVN add/move and os.mkdir commands but this script does not "commit"
LIVE = False

VICTOR_ANIM_DIR = os.path.join(os.environ['HOME'], 'workspace', 'victor-animation', 'scenes', 'anim')
VICTOR_AG_DIR = os.path.join(os.environ['HOME'], 'workspace', 'victor-animation-assets', 'animationGroups')

# move stuff from old and engine

OLD_DIR = os.path.join(VICTOR_AG_DIR, 'old')
ENGINE_DIR = os.path.join(VICTOR_AG_DIR, 'engine')

old_files = os.listdir(OLD_DIR)
engine_files = os.listdir(ENGINE_DIR)

# get features from scenes/anims
anim_files = os.listdir(VICTOR_ANIM_DIR)
maya_features = []
for f in anim_files:
    if not f.endswith('.ma'):
        maya_features.append(f)

# TODO dont forget the old and engine files

# sys.exit(0)
'''
# move from old and engine
for f in old_files:
    src = os.path.join( VICTOR_AG_DIR, 'old',f)
    dest = os.path.join(VICTOR_AG_DIR, f)
    cmd = ['svn','move',src,dest]
    print cmd
    if LIVE: subprocess.call(cmd)

for f in engine_files:
    src = os.path.join( VICTOR_AG_DIR, 'engine',f)
    dest = os.path.join(VICTOR_AG_DIR, f)
    cmd = ['svn','move',src,dest]
    print cmd
    if LIVE: subprocess.call(cmd)

'''

features = []
fmap = {}
ag_files = os.listdir(VICTOR_AG_DIR)
print "FEATURES..."
for agf in ag_files:
    #print agf
    if 'json' in agf:
        base = agf.split('.')[0]
        words = base.split('_')
        feature = words[1]
        if feature not in features:
            features.append(feature)
        # now see if this feature can be found in maya_features
        if feature in maya_features:
            print feature

features = sorted(features)
maya_features = sorted(maya_features)
for mf in maya_features:
    fmap[mf] = []

for k in fmap.keys():
    for f in features:

        if k.lower() == f.lower():
            fmap[k].append(f)
            features.remove(f)
        # check for plural nouns
        if k.lower() == f.lower()[0:-1] or k.lower()[0:-1] == f.lower():
            fmap[k].append(f)
            features.remove(f)
print("\n\nFMAP")
pprint(fmap)
print("\n\nFEAUTRES")
pprint(features)

# for a,b in enumerate( maya_features):
#    print features[a], '\t',b
# to double check
# pprint(fmap)


'''

        if feature not in features:
            features.append(feature)
            pth = os.path.join(VICTOR_AG_DIR, feature)
            cmd = ['svn', 'add', pth]
            print cmd
            if LIVE and not os.path.exists(pth):
                os.mkdir(pth)
            if LIVE: subprocess.call(cmd)
            src = os.path.join(VICTOR_AG_DIR, agf)
            dest = os.path.join(VICTOR_AG_DIR, feature, agf)
            cmd = ['svn','move',src,dest]
            print cmd
            if LIVE: subprocess.call(cmd)
            
{
  #  'AVS' : ['avs'],
    'Attention': ['attention', 'lookatface', 'lookatphone', 'lookinplaceforfaces'],
    'Blackjack': ['blackjack'],
    'Bored': ['bored'],
    'Bouncer': ['bouncer'],
    'ChargerDocking': ['chargerdocking', 'charger'],
    'Clock': ['clock'],
    'Codelab': ['codelab'],
#  'Communication': ['communication'],
    'CozmoSays': ['cozmosays'],
    'CozmoSings': ['cozmosings'],
    'Cube': [],
    'CubeConnection': ['cubeconnection'],
    'CubeToss': ['cubetoss'],
    'DanceBeat': ['dancebeat'],
    'Dancing': ['dancing'],
    'Dizzy': ['dizzy'],
    'Explorer': ['explorer', 'planning'],
    'EyeColorReaction': ['eyecolorreact'],
    'EyeContact': ['eyecontact'],
# 'EyePoses': ['eyeposes'],
#  'Feedback': ['feedback'],
    'FindCube': ['findcube'],
    'Fistbump': ['fistbump'],
    'Freeplay': ['freeplay'],
# 'FrequencyTest': ['frequency_test'],
    'GameSetup': ['gamesetup'],
# 'Gazing': ['gazing'],
    'Generic': ['generic'],
    'Greeting': ['greeting'],
    'GuardDog': ['guarddog'],
    'Hiccup': ['hiccup', 'hiccups'],
#  'HowOld': ['howold'],
#  'InspectHeldCube': ['inspectheldcube'],
    'KeepAlive': ['keepalive'],
    'Keepaway': ['keepaway'],
    'KnowledgeGraph': ['knowledgegraph'],
    'Laser': ['laser'],
    'Launch': ['launch'],
    'Locomotion': ['loco'],
    'LookAtDevice': ['lookatdevice'],
    'MeetVictor': ['meetvictor'],
    'MemoryMatch': ['memorymatch'],
#  'MicState': ['micstate'],
#  'Movement': ['movement'],  

anim_movement_comehere_reaction_01.tar   anim_movement_reacttoface_01.tar
anim_movement_alreadyhere_01.tar         anim_movement_directioncommands_01.tar
anim_movement_comehere_01.tar            anim_movement_lookinplaceforfaces_01.tar


    'Needs': ['energy', 'repair', 'power'],
    'NoWifi': ['nowifi', 'nocloud'],
    'Observing': ['observe'],
    'Onboarding': ['onboarding'],
    'Other': ['neutral'],
    'Pause': ['pause'],
    'Peekaboo': ['peekaboo'],
    'PetDetection': ['petdetection'],
    'Petting': ['petting'],
    'Photograph': ['takepicture'],
    'Play': ['play'],
    'Pounce': ['cubepounce', 'quick'],
    'PowerOffOn': [],
    'PowerOnOff': [],
#  'PowerSaveMode': ['powersavemode'],

anim_power_offon_01.tar            anim_power_onoff_01.tar            anim_powersavemode_temperature.tar


    'Pyramid': ['pyramid'],
    'QA': ['qa'],
    'RTIllumination': ['rtillumination'],
    'RTMotion': ['rtmotion'],
    'RTPickup': ['rtpickup'],
    'RTSound': ['rtsound'],
    'ReactToBlock': ['reacttoblock', 'reacttonewblock', 'reacttonewblockonground', 'rtobstacle'],
    'ReactToCliff': ['reacttocliff'],
    'ReactToHabitat': ['reacttohabitat'],
#  'Referencing': ['referencing'],
    'RequestToPlay': ['requesttoplay', 'rtp', 'askforblock', 'requestgame', 'rtpkeepaway', 'rtpmemorymatch'],
#  'RtShake': ['rtshake'], some are drive anims and there's also rtsound
    'SDK': ['sdk'],
    'SlowPoke': ['slowpoke'],
#  'SnowGlobe': ['snowglobe'],
    'SpeedTap': ['speedtap', 'cubetapping'],
    'Spinner': ['spinner'],
    'TextToSpeech': ['texttospeech'],
    'ThirdBlockTower': [],
    'Timer': ['timer', 'timersup'],
    'VoiceCommand': ['vc', 'comehere'],
    'VoiceMessage': ['message'],
#  'Volume': ['volume'],
    'WakeWord': ['wakeword'],
    'Weather': ['weather'], anim_avs_listen2weather_03.tar
    'Workout': ['workout'], ?
    'backpack': [],
    'fastbump': ['fastbump'],
    'gotoSleep': ['gotosleep'],
 # 'handdetection': ['handdetection'],
    'hiking': ['hiking'],
#  'holiday': ['holiday'],
    'meetcozmo': ['meetcozmo'],
    'slowbump': ['slowbump'],
    'sparking': ['sparking'],
    'upgrades': ['upgrade']
}

[,
    'audio',
    'clock',  # create new
    'demo',
    

 #REMOVE  'test'  # nishkar test simple moods
    ]
'''

