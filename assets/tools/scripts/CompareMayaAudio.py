import os, glob
import os.path
import json

#Grab all .ma files
#Grab all .json files
# Compare the number of audio files

#SVN trunk
ma_path = "/Users/mollyjameson/dev/maya anims/trunk/scenes/anim/"
#Master from git
json_path = "/Users/mollyjameson/dev/test/products-cozmo-assets/animations/"

print "Runninig Diff of anki anims and sounds"

#Read in a maya files
#If a json files exists of the same name
# Read in json file and check audio wav names
# Compare to number of audio nodes in maya files

for i in os.listdir(ma_path):
    if i.endswith(".ma"):
      filename = i.replace(".ma","")
      json_file_name = os.path.join(json_path, filename + ".json")
      if( os.path.isfile(json_file_name) ):
        num_wavs_json = 0
        num_wava_maya = 0
        with open(json_file_name) as data_file:    
          #data = json.load(data_file)
          #json_str = str(data)
          json_str = data_file.read()
          num_wavs_json = json_str.count(".wav")
        with open(ma_path + i) as data_file: 
          maya_str = data_file.read()
          num_wava_maya = maya_str.count(".wav")
        if( num_wava_maya != num_wavs_json ):
          print filename + " has " + str(num_wavs_json) + " sounds in json but maya thinks " + str(num_wava_maya)
          #print "ERROR MISMATCH with " + filename
      else:
        print "no file for " + str(i)

print "Done Running Script"

