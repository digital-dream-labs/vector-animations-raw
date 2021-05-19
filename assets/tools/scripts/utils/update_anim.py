#!/usr/bin/env python

import sys
import json

def update_anim(version_num):
    """
    modify DEPS file by changing version number of animation assets
    """
    deps_file = "/Users/dariajerjomina/workspace_git/victor/DEPS"
    with open(deps_file,"r+") as data_file:
        data = json.load(data_file)
        data["svn"]["repo_names"]["cozmo-assets"]["version"] = version_num
        data_file.seek(0)
        data_file.write(json.dumps(data, indent=4,sort_keys=True,separators=(',', ': ')))
        data_file.truncate()
        data_file.close()

if __name__ == "__main__":
    try:
        version_num = sys.argv[1]
    except IndexError:
        print "add version number as first argument"
    else:
        update_anim(version_num)
