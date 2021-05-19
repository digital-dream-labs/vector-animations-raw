import os
import maya.cmds as cmds

"""
            This script imports Victors cube rig as a reference
            7/2018 Chris Rogers
            (c) Anki, Inc
"""

CUBES_GROUP = "cubes:cube1_grp"
CUBES_RELATIVE_PATH = "assets/models/Victor/Victor_cube_rig.ma"
CUBES_DISPLAY_LAYER = "cubes_geo_lyr"
CUBE1_CTRL = "cubes:cube1_ctrl"
TEXTURE_WARNING = "Couldn't set hardware textuting on modelPanel4"
CUBE_ERROR = "Error referencing cube rig"
SUCCESS_MESSAGE = "Cubes loaded successfully."


def safe_select(obj):
    if cmds.objExists(obj):
        cmds.select(obj, add=True)


def do_import():
    if cmds.objExists(CUBES_GROUP):
        print "Currently a {0} is in scene.".format(CUBES_GROUP),
        return
    try:
        # modelpanel4 is the standard persp window that should be available visible or not
        cmds.modelEditor("modelPanel4", edit=True, displayTextures=True)
    except:
        cmds.warning(TEXTURE_WARNING)
    cube_path = os.path.join(cmds.workspace(q=1,rd=1), CUBES_RELATIVE_PATH)
    if os.path.exists(cube_path):
        cmds.file(cube_path, r=True, type="mayaAscii", gl=True,
                  mergeNamespacesOnClash=False, ns="cubes")
    else:
        cmds.error(CUBE_ERROR)
        return
    safe_select(CUBES_GROUP)
    cmds.xform(CUBE1_CTRL, t=(0,0,10))
    cmds.createDisplayLayer(nr=True,name=CUBES_DISPLAY_LAYER)
    cmds.setAttr(CUBES_DISPLAY_LAYER+".displayType", 2)
    cmds.setAttr(CUBES_DISPLAY_LAYER + ".color", 3)
    cmds.select(cl=True)
    print SUCCESS_MESSAGE,
