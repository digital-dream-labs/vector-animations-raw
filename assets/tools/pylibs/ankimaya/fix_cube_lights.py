import pymel.core as pm

import random

# get all remaphsvs

# for all light controls, add a saturation with a default of 1
#     change all color attrs to 0 360
DEFAULT_BRIGHTNESS = 0.4
GREY = 128

def go():
    pm.openFile("/Users/chris.rogers/workspace/victor-animation/assets/models/Cozmo/3cubes_rig.ma", f=True)
    ctrls = pm.ls('light*ctrl*', type='transform')
    for c in ctrls:
        print c
        if 'grp' not in str(c):
            s, d = pm.listConnections(c, c=1, s=1, d=1, p=1)[0]
            d = d.split('.')[0]
            print d
            s2, d2 = pm.listConnections(d, c=1, s=1, d=1, p=1)[0]
            d2 = d2.split('.')[0]
            print d2
            remap = d2
            material = pm.ls(d2)[0]
            print material
            # print pm.listConnections(pm.listRelatives(c), c=1,  d=1, p=1)
            pm.addAttr(c, longName='Saturation', attributeType='float', minValue=0, maxValue=1, defaultValue=0,
                       keyable=True)
            pm.addAttr(c, longName='Hue', minValue=0, maxValue=360, keyable=True, type='float', defaultValue=0)
            pm.setAttr(c + '.Brightness', DEFAULT_BRIGHTNESS)
            pm.deleteAttr(c + '.Color')
            # this is just to test that it works animated
            for i in range(10):
                pm.setAttr(c + '.Hue', random.random() * 360)
                pm.setKeyframe(c + '.Hue', t=i * 10)

            hsv = pm.createNode("hsvToRgb", name="rgbToHsv_" + str(c))
            c.Saturation >> hsv.inHsvG
            c.Hue >> hsv.inHsvR
            c.Brightness >> hsv.inHsvB
            hsv.outRgbR >> material.incandescenceR
            hsv.outRgbG >> material.incandescenceG
            hsv.outRgbB >> material.incandescenceB
            pm.setAttr(material + '.colorR', GREY)
            pm.setAttr(material + '.colorG', GREY)
            pm.setAttr(material + '.colorB', GREY)


pm.delete(pm.ls('remapH*'))
