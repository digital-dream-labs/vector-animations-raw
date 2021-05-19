import json
from pprint import pprint

'''

                        this script takes in an anki animation json file and scans for
                        floats and lists of floats and reduces those values to a lower precision
                        defined by the constant
                        PLACES
                        chris rogers (c) anki 2018

'''


PLACES = 12

# test files
f = '/Users/chris.rogers/Documents/anim_onboarding_wakeup_01.json'
o =  '/Users/chris.rogers/Documents/out'+str(PLACES)+'places.json'

FORMAT = '{0:.'+str(PLACES)+'f}'

fid = open(f,'r')
d = json.load(fid)
fid.close()
ar = d['anim_onboarding_wakeup_01']
for a in ar:
    #print a
    for k in a.keys():
        if type(a[k]) ==type(0.33):

            n = float(FORMAT.format(a[k]))
            #print type(a[k]), a[k], n
            a[k] = n
        # all lists are lists of floats
        if type(a[k]) == type([0,1]):
            #print(a[k])
            if type(a[k][0]) == type(0.3):
                for i,val in enumerate(a[k],0):
                    n = float(FORMAT.format(val))
                    a[k][int(i)] = n
                    #print n

with open(o, 'w') as outfile:
    json.dump(d, outfile)

