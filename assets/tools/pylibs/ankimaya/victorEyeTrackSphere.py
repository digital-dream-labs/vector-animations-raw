import maya.cmds as cmds

MESH_NAME = 'x:eye_R_geo'
VERTEX_INDEX = 19
SCALE = 0.05
TRACKED_OBJECT = 'victorEyeTrackSphere'

def attachSphere():
    if cmds.objExists(TRACKED_OBJECT):
        cmds.warning("tracked object {0} already exists.  delete it before you make a new one.".format(TRACKED_OBJECT))
        return
    if not cmds.objExists(MESH_NAME):
        cmds.warning("Could not find Victor's eye control {0}.".format(MESH_NAME))
        return
    vertex = '{0}.vtx[{1}]'.format(MESH_NAME, VERTEX_INDEX)
    sphere = cmds.polySphere(name='victorEyeTrackSphere')[0]
    cmds.scale(SCALE, SCALE, SCALE)
    try:
        cmds.select(vertex, sphere)
    except:
        cmds.error("Could not select {0}.".format(vertex))
        return
    else:
        cmds.pointOnPolyConstraint()