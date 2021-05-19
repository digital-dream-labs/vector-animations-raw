"""
This script can be used to reset the selected controllers to
their default value.

Copyright: Anki, Inc. 2018

This is a modified version of resetControllers.py from
https://www.highend3d.com/maya/script/controllerreseter-for-maya
which is subject to the MIT License. The header in that original
version of the script is:
------------------------------------------------------------------------
resetControllers.py - Python Script
------------------------------------------------------------------------
Copyright 2012 Carlos Chacon L. All rights reserved.

DESCRIPTION:
Resets the selected controllers to their default value.

USAGE:
*Select the controllers to be reset.
*Run the script.

AUTHOR:
Carlos Chacon L. (caedo.00 at gmail dot com)
------------------------------------------------------------------------
"""

import maya.cmds as cmds


CUSTOM_ATTRS = { "x:mech_eyes_all_ctrl.ScanlineOpacity" : 1.0,
                 "x:mech_eye_R_ctrl.Lightness" : 1,
                 "x:mech_eye_L_ctrl.Lightness" : 1,
                 "x:mech_eye_R_ctrl.GlowSize" : 0,
                 "x:mech_eye_L_ctrl.GlowSize" : 0,
                 "x:mech_eye_R_ctrl.GlowVis" : 0,
                 "x:mech_eye_L_ctrl.GlowVis" : 0 }


def isSingleAttribute(attr, obj):
    """
    Checks if the attr is single or multiple value.
    """
    if cmds.attributeQuery(attr, node=obj, nc=True) is None:
        return True
    else:
        return False


def resetController(controller, customAttrs=CUSTOM_ATTRS):
    """
    Resets to zero all the non-locked attributes from a controller
    """
    controllerAttrs = cmds.listAttr(controller, k=True)
    for attr in controllerAttrs:
        if(isSingleAttribute(attr, controller)):
            defaultValue = cmds.attributeQuery(attr, ld=True, node=controller)[0]
            fqAttr = controller + "." + attr
            try:
                cmds.setAttr(fqAttr, defaultValue)
            except RuntimeError:
                print("skipping %s" % fqAttr)
            else:
                print("set %s to %s" % (fqAttr, defaultValue))
        for fullAttr, value in customAttrs.iteritems():
            if attr == fullAttr.split(".")[1]:
                try:
                    cmds.setAttr(fullAttr, value)
                except RuntimeError:
                    print("skipping %s" % fullAttr)
                else:
                    print("set %s to %s" % (fullAttr, value))


def resetControllers(controllers=None):
    """
    Resets multiple controllers.
    """
    if controllers is None:
        controllers = cmds.ls(sl=True)
    if len(controllers):
        for controller in controllers:
            resetController(controller)
        print("%s controllers were reset" % len(controllers))
    else:
        print("No controllers selected for reset")


