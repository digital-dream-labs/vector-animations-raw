"""
This module provides some convenience functionality for rendering
images from Maya to be displayed on the robot's face.
"""

import os
import time
import copy
import subprocess
import shutil
import math
from maya import cmds
import maya.app.renderSetup.model.renderSetup as renderSetup
import maya.app.renderSetup.model.renderLayer as renderLayer
from ankiutils.image_files import change_pixel_density


IMAGE_RESOLUTION = (184, 96)

PIXELS_PER_INCH = 202

RESOLUTION_NODE_CONNECTION = "defaultRenderGlobals.resolution"

# The following render settings help set the filename format of rendered
# images to be "name_####.ext" and the format of those images to PNG
RENDER_SETTINGS = { "defaultRenderGlobals.animationRange" : 0,       # use frame range from renderGlobals rather than time slider
                    "defaultRenderGlobals.imageFilePrefix" : None,   # this attribute should be set dynamically for each render
                    "defaultRenderGlobals.animation" : True,         # this usually renders more than just the current frame, so animation = True
                    "defaultRenderGlobals.extensionPadding" : 4,     # the number of digits to use in the frame number
                    "defaultRenderGlobals.periodInExt" : 2,          # to insert underscore between name and frame number, this should be 2
                    "defaultRenderGlobals.imageFormat" : 32,         # format for PNG = 32
                    "defaultRenderGlobals.putFrameBeforeExt" : True,
                    "defaultRenderGlobals.outFormatControl" : 0 }

TOOLS_DIR_ENV_VAR = "ANKI_TOOLS"


def _get_settings(attrs):
    settings = {}
    for attr in attrs:
        val = cmds.getAttr(attr)
        settings[attr] = val
    return settings


def _update_settings(settings):
    for attr, val in settings.items():
        if val is None:
            continue
        try:
            cmds.setAttr(attr, val)
        except RuntimeError:
            # if attribute is not numeric or boolean and we get RuntimeError, then assume
            # it is a string (since "defaultRenderGlobals.imageFilePrefix" is a string)
            cmds.setAttr(attr, val, type="string")


def _get_render_dpi(resolution_node_connection=RESOLUTION_NODE_CONNECTION):
    resolution_node = cmds.listConnections(resolution_node_connection)[0]
    dpi = cmds.getAttr("%s.dotsPerInch" % resolution_node)
    print("DPI = %s" % dpi)
    return dpi


def _set_render_dpi(dpi, resolution_node_connection=RESOLUTION_NODE_CONNECTION):
    resolution_node = cmds.listConnections(resolution_node_connection)[0]
    cmds.setAttr("%s.dotsPerInch" % resolution_node, dpi)


def _run_command(cmd, settings=None, verbose=False):
    env_vars = copy.copy(os.environ)
    if settings:
        env_vars.update(settings)
    if verbose:
        print("Running: %s" % cmd)
    try:
        p = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             shell=False, env=env_vars)
    except OSError as err:
        cmds.warning("Failed to execute: %s" % cmd)
        raise
    (stdout, stderr) = p.communicate()
    status = p.poll()
    if verbose:
        print("status = %s" % status)
        print("stdout = %s" % stdout)
        print("stderr = %s" % stderr)
    return (status, stdout, stderr)


def _convert_to_int(number, round_func=round):
    if isinstance(number, int):
        return number
    not_number_msg = "The provided frame numbers must be integers or floats"
    try:
        number = float(number)
    except (TypeError, ValueError):
        raise TypeError(not_number_msg)
    number = round_func(number)
    return int(number)


def _validate_frame_range(start, end):
    end_before_start_msg = "The end frame must be greater than or equal to the start frame"
    start = _convert_to_int(start, math.floor)
    end = _convert_to_int(end, math.ceil)
    #print("Frame range: %s to %s (inclusive)" % (start, end))
    if end < start:
        raise ValueError(end_before_start_msg)
    return (start, end)


def render(camera, name, start, end, render_layer=None, settings=RENDER_SETTINGS,
           resolution=IMAGE_RESOLUTION, density=PIXELS_PER_INCH,
           timestamp_output_dir=False, open_folder=False, start_numbering_from_zero=False):
    """
    Given a camera name, the name that should be used for the
    rendered output images, a start frame and an end frame, this
    function can be used to render out images in a new directory
    with the image format required for full-screen images on the
    robot's face (184 x 96 pixels in PNG format) and with our
    standard naming convention ("name_####.png")
    """
    image_files = []
    try:
        start, end = _validate_frame_range(start, end)
    except (ValueError, TypeError), e:
        cmds.warning(str(e))
        return (image_files, None)
    current_frame = cmds.currentTime(query=True)
    orig_render_settings = _get_settings(settings.keys())
    workspace_root = cmds.workspace(q=True, rd=True)
    file_rules = cmds.workspace(q=True, fileRule=True)
    orig_images_dir = file_rules[file_rules.index('images')+1]
    if timestamp_output_dir:
        # images should go into a unique "<name>_<timestamp>" subdirectory
        this_image_dir = name + '_' + str(int(time.time()))
    else:
        # images should go into a "<name>" subdirectory, where any existing
        # files in that subdirectory may get overwritten
        this_image_dir = name
    this_image_dir = os.path.join(orig_images_dir, this_image_dir)
    images_dir = os.path.join(workspace_root, this_image_dir)
    if not os.path.isdir(images_dir):
        os.makedirs(images_dir)
    try:
        # update output directory for rendered images to be "<current_image_dir>/<name>",
        # where <name> may or may not include a timestamp suffix
        cmds.workspace(fileRule=['images', this_image_dir])
        _update_settings(settings)
        cmds.setAttr("defaultRenderGlobals.imageFilePrefix", name, type="string")

        if start_numbering_from_zero:
            # from maya's documentation on modifyExtension of defaultRenderGlobals:
            # false-> use the current frame value as the filename extension,
            # true->use startExtension + ((currentFrame-startFrame)/byFrame) * byExtension value
            # as the filename extension
            cmds.setAttr("defaultRenderGlobals.modifyExtension",True)
            cmds.setAttr("defaultRenderGlobals.startExtension", 0.0)
            cmds.setAttr("defaultRenderGlobals.startFrame", start)
        else:
            cmds.setAttr("defaultRenderGlobals.modifyExtension", False)

        for frame in range(start, end+1):
            cmds.currentTime(frame, edit=True)
            if render_layer:
                # Can also use render_setup.switchToLayer(render_layer) and then render
                image_file = cmds.render(camera, x=resolution[0], y=resolution[1],
                                         layer=render_layer)
            else:
                image_file = cmds.render(camera, x=resolution[0], y=resolution[1])
            #print("Rendered: %s" % image_file)
            image_files.append(image_file)
    finally:
        # restore the output directory for images, the render settings and the frame
        # that was selected back to their original settings from before the render
        cmds.workspace(fileRule=['images', orig_images_dir])
        _update_settings(orig_render_settings)
        cmds.currentTime(current_frame, edit=True)
    if density:
        # Updating the resolution node's "dotsPerInch" attribute in Maya
        # does NOT successfully change the pixel density from 72 DPI to the
        # specified value, so we have to change it after the fact; see
        # https://knowledge.autodesk.com/support/maya/troubleshooting/caas/sfdcarticles/sfdcarticles/Images-rendered-at-300-DPI-in-Maya-appear-at-72-DPI-when-opened-in-Adobe-Photoshop-s.html
        for image_file in image_files:
            change_pixel_density(image_file, density)
    new_image_files = _remove_tmp_dir(images_dir, image_files)
    if open_folder:
        os.system("open %s" % images_dir)
    return (new_image_files, images_dir)


def _remove_tmp_dir(images_dir, image_files):
    # If tmp dir gets created, move rendered files into the top dir and remove the tmp dir
    # to avoid unnecessary directory nesting
    new_image_files = []
    old_dirs = []
    for image_file in image_files:
        image_file = os.path.normpath(os.path.abspath(image_file))
        new_image_file = os.path.join(images_dir, os.path.basename(image_file))
        new_image_file = os.path.normpath(os.path.abspath(new_image_file))
        if image_file != new_image_file:
            shutil.move(image_file, new_image_file)
        new_image_files.append(new_image_file)
        old_dir = os.path.dirname(image_file)
        if old_dir not in old_dirs:
            old_dirs.append(old_dir)
    #print("Empty directories to remove: %s" % old_dirs)
    for old_dir in old_dirs:
        if os.path.isdir(old_dir):
            try:
                os.rmdir(old_dir)
            except OSError:
                print("Unable to remove directory: %s" % old_dir)
            else:
                parent_dir = os.path.dirname(old_dir)
                if os.path.basename(parent_dir) == "tmp":
                    try:
                        os.rmdir(parent_dir)
                    except OSError:
                        pass
    return new_image_files


def create_render_layer(selection, name, overwrite_selection=True):
    """
    Creates render layer of a specified name with specified selection.
    """
    render_setup = renderSetup.instance()
    # Check if the layer with the same name already exists, in that case don't create new one
    try:
        render_layer = render_setup.getRenderLayer(name)
    except:
        # If can't get render layer, means it doesn't exist (so creating new one)
        render_layer = render_setup.createRenderLayer(name)
    # First remove existing collections, so that objects don't get rendered together with previous
    # selections (in case the render layer is the same as the one before).
    if overwrite_selection:
        remove_collections(render_layer)
        if selection:
            collection = render_layer.createCollection("selection_collection")
            collection.getSelector().staticSelection.set(selection)
    return render_layer


def remove_collections(render_layer):
    """
    Remove collections from a render layer.
    Can run if changing selection of existing layer.
    """
    collections = render_layer.getCollections()
    for collection in collections:
        render_layer.detachCollection(collection)


def show_default_render_layer():
    """
    Switches layer to the default one. Can do at the end of rendering,
    so that the last rendered layer doesn't stay visible.
    """
    render_setup = renderSetup.instance()
    default_render_layer = renderLayer.DefaultRenderLayer()
    render_setup.switchToLayer(default_render_layer)


def get_render_layers_info():
    """
    @return: All render layers and their selection
             objects {render_layer_name : [selection]}
    """
    render_layer_info = {}
    render_setup = renderSetup.instance()
    render_layers = render_setup.getRenderLayers()
    for render_layer in render_layers:
        selections = []
        collections = render_layer.getCollections()
        for collection in collections:
            selection = collection.getSelector().getStaticSelection()
            selections.append(selection)
        selections = filter(None, selections)
        render_layer_info[render_layer.name()] = selections
    return render_layer_info


