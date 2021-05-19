import os
import sys
from pprint import pprint


COZMO_ANIM_DIR = os.path.join(os.environ['HOME'], 'workspace', 'victor-animation-assets', 'animations')
COZMO_AG_DIR = os.path.join(os.environ['HOME'], 'workspace', 'victor-animation-assets', 'animationGroups')

'''
                        this script will list each folder in animationGroups,
                        then check the contents of every json in that folder
                        to see if the animation clip name matches the folder name
                        it prints *********** for a non-match
                        and ------------ for things in locomotion that actually have driving or hiking in them

                        chris rogers (c) Anki 2018
                        
                        
                        12/2018 - this needs to run after the json files have been moved
                        into animationGroup folders

'''
tofix = []

for folder in os.listdir(COZMO_AG_DIR):
    print "\nFOLDER: ",folder
    path = os.path.join(COZMO_AG_DIR, folder)
    for jsonfile in os.listdir(path):
        print"\tJSONFILE:{0} [{1}]".format(jsonfile,folder)
        with open( os.path.join(COZMO_AG_DIR, folder, jsonfile)) as f:
            content = f.readlines()
            for l in content:
                if 'Name' in l:
                    n = l.split(':')[1]
                    tag = ''
                    if folder not in n:
                        tag = "******"
                        new_array = []
                        new_array.append('folder:[{0}]'.format(folder).strip())
                        new_array.append('json:[{0}]'.format(jsonfile).strip())
                        new_array.append('anim:[{0}]'.format(n).strip().replace('\n',''))
                        tofix.append(new_array)
                    if folder == 'locomotion':
                        if 'hiking' in n or 'driving' in n:
                            tag = "--------------"
                    print '\t\t{0} {1}'.format(n.strip(), tag)


print "FILES TO FIX:"
print len(tofix)
for t in tofix:
    print "{0}\t\t\t{1}\t\t\t{2}".format(t[0],t[1],t[2])