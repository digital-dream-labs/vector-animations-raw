import maya.cmds as mc
import copy
import json_exporter as je
import os

# from sprite_box_material import create_sprite_box_material # This will be used for visualization
# of aniamtion on Vector's face. (Not working yet)

LEVEL_CM = 0.1  # How many centimeteres to move the sprite plane in maya depending on the layer
# before L5 will move by eye_z_pos-LEVEL_CM/2-(5-layer_num)*LEVEL_CM)
# after L5 will move by eye_z_pos+LEVEL_CM/2+(layer_num-6)*LEVEL_CM

SPRITE_BOX_HOLDER = "x:sprite_boxes_grp"

RENDER_METHOD_ATTR = "SpriteRenderMethod"
LOOP_CONFIG_ATTR = "SpriteLoopConfig"
ASSET_NAME_ATTR = "SpriteAssetEnum"

DEFAULT_ASSET_NAME = "clear_sprite_box"

TRANSPARENCY_ATTR = "SpriteTransparency"
ALPHA_JSON_ATTR = "alpha"
# LAYER_ATTR = "SpriteLayer"
LAYER_JSON_ATTR = "layer"

# RENDER_METHOD_ATTR is not part of this dict, because it's choices can change depending on
ENUMS_DICT = {RENDER_METHOD_ATTR: ["RGBA", "Eye Color"],
              LOOP_CONFIG_ATTR: ["Clear", "Loop", "Hold"],
              ASSET_NAME_ATTR: []}

ENUM_2_JSON_NAME = {RENDER_METHOD_ATTR: "renderMethod", LOOP_CONFIG_ATTR: "spriteSeqEndType",
                    ASSET_NAME_ATTR: "assetName"}
TRANSLATION_ATTR_2_JSON_NAME = {"translateX": "xPos", "translateY": "yPos"}
SCALE_ATTR_2_JSON_NAME = {"scaleX": "width", "scaleY": "height"}

JSON_KEYFRAME = {
    "Name": "SpriteBoxKeyFrame",
    "spriteBoxName": "SpriteBox_1",
    "assetName": "clear_sprite_box",
    "triggerTime_ms": 2640,
    "layer": "Layer_2",
    "renderMethod": "RGBA",
    "alpha": 100,
    "spriteSeqEndType": "Clear",
    "xPos": 0,
    "yPos": 0,
    "width": 184,  # value needs to correspond to 1 in scaleX (used when getting json)
    "height": 96  # value needs to correspond to 1 in scaleY (used when getting json)
}

ENUM_STR = "enum"

PX_IN_CM = 80.0  # Value based on VIC-1294
DEFAULT_LAYER_NUM = 6

AXIS = ["x", "y", "z"]
RGB = ["R", "G", "b"]


# Sprite box creation, and setting of values
#
def create_sprite_box_polygon(srite_box_holder=SPRITE_BOX_HOLDER, layer_num=DEFAULT_LAYER_NUM,
                              pos_x="0",
                              pos_y="0", width="184", height="96", sprite_box_name="SpriteBox_1",
                              render_method="RGBA", loop_config="Loop",
                              asset_name=DEFAULT_ASSET_NAME, asset_enum_list=[],
                              alpha_value="100", verbose=False):
    """
    Create polygon in the origin, then parent under a sprite
    holder and zero out the values to position at the
    left top corner of the eyes
    """

    if verbose:
        print "Creating sprite box plane, with the following parameters:"
        print "srite_box_holder ", srite_box_holder
        print "layer_num ", layer_num
        print "pos_x ", pos_x
        print "pos_y ", pos_y
        print "width ", width
        print "height ", height
        print "render_method ", render_method
        print "loop_config ", loop_config
        print "asset_name ", asset_name,
        print "alpha_value ", alpha_value

    # Translate values to maya's attributes units
    if str_2_float(JSON_KEYFRAME["width"]) and str_2_float(JSON_KEYFRAME["height"]):
        original_width_cm = px_2_cm(float(JSON_KEYFRAME["width"]))
        original_height_cm = px_2_cm(float(JSON_KEYFRAME["height"]))
    else:
        return

    # Most enums are pre-populated, and can have only specific values. Asset names are an exception
    # since they are being populated from the names of image files. Clear asset needs to be added.
    enums_dict = copy.deepcopy(ENUMS_DICT)
    asset_enum_list.append(DEFAULT_ASSET_NAME)
    enums_dict[ASSET_NAME_ATTR] = asset_enum_list

    if not mc.objExists(srite_box_holder):
        mc.error("Can not find %s. Please make sure correct rig is referenced") % (srite_box_holder)
        return

    sprite_box_name = generate_sprite_box_name(sprite_box_name)
    # Create Sprite box in the top right corner, so that translation attrs represent
    # position (and not vertexes)
    sprite_box = mc.polyCreateFacet(p=[(0, 0, 0),
                                       (original_width_cm, 0, 0),
                                       (original_width_cm, -original_height_cm, 0),
                                       (0, -original_height_cm, 0)],
                                    name=sprite_box_name)[0]
    # By default normals are facing the wrong direction, so need to reverse them back
    mc.polyNormal(sprite_box, normalMode=0)

    # Parenting will change the transformation of the object to be in relation to the parent
    mc.parent(sprite_box, srite_box_holder)

    # Make attributes that can't be animated un-keyable
    for axi in AXIS:
        mc.setAttr(sprite_box + ".r" + axi, keyable=False)
    mc.setAttr(sprite_box + ".sz", keyable=False)
    mc.setAttr(sprite_box + ".visibility", keyable=False)

    # Add enum attributes to sprite box
    for attr, enum_list in enums_dict.iteritems():
        add_enum_attr(sprite_box, attr, enum_list)
    mc.addAttr(sprite_box, longName=TRANSPARENCY_ATTR, attributeType='float',
               minValue=0, maxValue=1, defaultValue=0, keyable=True)

    # This is going to be used to display textures on the sprite box
    # create_sprite_box_material(sprite_box, True, TRANSPARENCY_ATTR)

    # Setting keyframe at the end of creation (in case of a modified sprite box)
    set_sprite_box_keyframe(sprite_box=sprite_box, render_method=render_method,
                            loop_config=loop_config,
                            asset_name=asset_name,
                            layer=layer_num, width=width, height=height, pos_x=pos_x, pos_y=pos_y,
                            alpha_value=alpha_value, verbose=False)


def set_sprite_box_keyframe(sprite_box=None, render_method="RGBA", loop_config="Loop",
                            asset_name="face_nowifi_icon",
                            layer=DEFAULT_LAYER_NUM, width=184, height=96, pos_x=0, pos_y=0,
                            alpha_value=100, verbose=True):
    """
    Sets a keyframe with specified parameters on the sprite box.
    """
    if sprite_box is None:
        mc.error("Sprite box is not specified")
        return

    if verbose:
        print "Setting keyframe on %s with the following parameters" % (sprite_box)
        print "pos_x ", pos_x
        print "pos_y ", pos_y
        print "width ", width
        print "height ", height
        print "render_method ", render_method
        print "loop_config ", loop_config
        print "asset_name ", asset_name,
        print "alpha_value ", alpha_value

    scale_x = float(width) / float(JSON_KEYFRAME["width"])
    scale_y = float(height) / float(JSON_KEYFRAME["height"])
    pos_x = px_2_cm(float(pos_x))
    pos_y = px_2_cm(float(pos_y))
    alpha_value = int(alpha_value)
    # Alpha (0 to 100) needs to be converted to transparency (1 to 0) to then connect it to material
    transparency_value = alpha_2_transparency(alpha_value)

    set_enum_by_string(sprite_box, ASSET_NAME_ATTR, asset_name)
    set_enum_by_string(sprite_box, LOOP_CONFIG_ATTR, loop_config)
    set_enum_by_string(sprite_box, RENDER_METHOD_ATTR, render_method)
    mc.setAttr(sprite_box + "." + TRANSPARENCY_ATTR, transparency_value)
    # If we decide to add a layer attr:
    # mc.setAttr(sprite_box + "." + LAYER_ATTR, layer)

    # Changing translation will place the plane at the specified position in relation to the parent
    pos_z = layer_num_2_z_pos(layer)
    mc.setAttr(sprite_box + ".tx", pos_x)
    mc.setAttr(sprite_box + ".ty", -pos_y)
    mc.setAttr(sprite_box + ".tz", pos_z)
    mc.setAttr(sprite_box + ".sx", scale_x)
    mc.setAttr(sprite_box + ".sy", scale_y)
    for ax in AXIS:
        mc.setAttr(sprite_box + ".r" + ax, 0)

    mc.setKeyframe(sprite_box)


def generate_sprite_box_name(sprite_box_name):
    """
    Get a name of a sprite box, which is a specified name with a unique number at the end.
    This is done to avoid name repetition.
    """
    if mc.objExists(sprite_box_name):
        try:
            sprite_num = int(sprite_box_name.split("_")[-1])
        except ValueError:
            sprite_num = 0
        if sprite_num > 0:
            sprite_num += 1
            sprite_box_name = sprite_box_name.split("_")[0]
        return generate_sprite_box_name("%s_%s" % (sprite_box_name, sprite_num))
    return sprite_box_name


# Enum attributes functionality
#
def add_enum_attr(obj, attr_name, enum_list):
    enum_str = ":".join(enum_list)
    mc.addAttr(obj, longName=attr_name,
               attributeType=ENUM_STR, keyable=True, enumName=enum_str)
    return enum_str + "." + attr_name


def set_enum_by_string(node, attribute, enum_name):
    enum_string = mc.attributeQuery(attribute, node=node, listEnum=True)[0]
    enum_list = enum_string.split(":")
    if enum_name in enum_list:
        enum_idx = enum_list.index(enum_name)
        mc.setAttr("%s.%s" % (node, attribute), enum_idx)


# Conversion
#
def alpha_2_transparency(alpha_value):
    return 1 - (float(alpha_value) / 100.0)


def transparency_2_alpha(transparency_value):
    return int(100 - (transparency_value * 100))


def layer_num_2_z_pos(layer_num=DEFAULT_LAYER_NUM):
    """
    Find z position of the polygon based on the number of it's layer
    """
    layer_num = float(layer_num)
    if 0.0 <= layer_num <= 5.0:
        pos_z = -(LEVEL_CM / 2.0) - ((5.0 - layer_num) * LEVEL_CM)
    elif 6.0 <= layer_num <= 10.0:
        pos_z = LEVEL_CM / 2.0 + (layer_num - 6.0) * LEVEL_CM
    else:
        mc.error("Need to specify level betweeb 1 and 10")
        pos_z = 0.0
    return pos_z


def z_pos_2_layer_num(z_value):
    layer_num = int(((z_value - (LEVEL_CM / 2.0)) + 6.0 * LEVEL_CM) / LEVEL_CM)
    # elif z_value < 0:
    #     layer_num = int((z_value - (LEVEL_CM / 2.0)) + 5)

    if layer_num < 1:
        layer_num = 1
    elif layer_num > 10:
        layer_num = 10
    return layer_num

    return layer_num


def px_2_cm(px_value):
    """
    Since all maya calculations are done in cm and
    eye screen calculations in px, need to convert from one to another
    """
    return px_value / PX_IN_CM


def cm_2_px(cm_value):
    """
    Since all maya calculations are done in cm and
    eye screen calculations in px, need to convert from one to another
    """
    return cm_value * PX_IN_CM


def str_2_float(input_str):
    try:
        float(input_str)
    except Exception:
        print "Can't convert %s to float" % (input_str)
    else:
        return float(input_str)


# For json export
#
def get_sprite_box_attrs(sprite_box):
    """
    Get all values of the current keyframe.
    Used when opening ui when sprite box is selected.
    """
    json_keyframe = get_json_keyframe(sprite_box, mc.currentTime(q=True))
    pos_x = json_keyframe["xPos"]
    pos_y = json_keyframe["yPos"]
    width = json_keyframe["width"]
    height = json_keyframe["height"]
    asset_name = json_keyframe["assetName"]
    render_method = json_keyframe["renderMethod"]
    loop_config = json_keyframe["spriteSeqEndType"]
    alpha = json_keyframe["alpha"]
    layer = json_keyframe["layer"].split("_")[-1]

    return pos_x, pos_y, width, height, asset_name, render_method, loop_config, alpha, layer


def get_json_keyframe(sprite_box, frame_num):
    """
    Returns json keyframe for the specified sprite box, excluding trigger time.
    """
    json_keyframe = copy.deepcopy(JSON_KEYFRAME)

    # Enum attrs
    for attr, json_attr in ENUM_2_JSON_NAME.iteritems():
        if mc.objExists(sprite_box + "." + attr):
            attr_value = mc.getAttr(sprite_box + "." + attr, asString=True, time=frame_num)
            json_keyframe[json_attr] = attr_value.replace(" ", "")

    # Translation attrs
    for attr, json_attr in TRANSLATION_ATTR_2_JSON_NAME.iteritems():
        if mc.objExists(sprite_box + "." + attr):
            attr_value = mc.getAttr(sprite_box + "." + attr, time=frame_num)
            px_value = int(cm_2_px(attr_value))
        if "Y" in attr:
            px_value *= -1
        json_keyframe[json_attr] = px_value

    # Scale attrs
    for attr, json_attr in SCALE_ATTR_2_JSON_NAME.iteritems():
        if mc.objExists(sprite_box + "." + attr):
            attr_value = mc.getAttr(sprite_box + "." + attr, time=frame_num)
            largest_value = JSON_KEYFRAME[json_attr]  # The value when scale is 1
        # Since we are converting from flaots to integers and back, there might be discrepencies
        # between the px values and attribute values, but they are very minor and thus are not taken into concidiration
        px_value = int(
            round(largest_value * attr_value))  # Scale attr in maya is a multiplier for json attr
        json_keyframe[json_attr] = px_value

    # Transparency, alpha and layers
    if mc.objExists(sprite_box + "." + TRANSPARENCY_ATTR):
        transparency_value = mc.getAttr(sprite_box + "." + TRANSPARENCY_ATTR, time=frame_num)
        alpha_value = int(transparency_2_alpha(transparency_value))
        json_keyframe[ALPHA_JSON_ATTR] = alpha_value

    if mc.objExists(sprite_box + ".tz"):
        pos_z = mc.getAttr(sprite_box + ".tz", time=frame_num)
        layer_num = z_pos_2_layer_num(pos_z)
    json_keyframe[LAYER_JSON_ATTR] = "Layer_%s" % (layer_num)
    json_keyframe["spriteBoxName"] = sprite_box

    return json_keyframe
