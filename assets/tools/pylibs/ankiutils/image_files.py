#!/usr/bin/env python

import os
import sys
import copy
import subprocess
import tarfile
import tempfile


DEFAULT_IMAGE_TYPE = ".png"

TOOLS_DIR_ENV_VAR = "ANKI_TOOLS"

PNGQUANT = os.path.join("other", "pngquant")
NUMBER_COLORS = 16

OPTIPNG = os.path.join("other", "optipng")
OPTIPNG_QUALITY = "o7"

IMAGE_MAGICK_DIR = os.path.join("other", "ImageMagick-7.0.8")

SIPS = "/usr/bin/sips"


def _run_command(cmd, settings=None, shell=False, verbose=False):
    env_vars = copy.copy(os.environ)
    if settings:
        env_vars.update(settings)
    if verbose:
        print("Running: %s" % cmd)
    if not shell:
        cmd = cmd.split()
    try:
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=shell, env=env_vars)
    except OSError as err:
        print("WARNING: Failed to execute: %s" % cmd)
        raise
    (stdout, stderr) = p.communicate()
    status = p.poll()
    if verbose:
        print("status = %s" % status)
        print("stdout = %s" % stdout)
        print("stderr = %s" % stderr)
    return (status, stdout, stderr)


def optimize_image_file(png_file, number_of_colors=NUMBER_COLORS, quality=OPTIPNG_QUALITY):
    """
    This function uses 'pngquant' and 'optipng' to optimize a PNG image file.
    """
    st = os.stat(png_file)
    #print("Optimizing image file: %s (size = %s)" % (png_file, st.st_size))

    tools_dir = os.environ[TOOLS_DIR_ENV_VAR]
    pngquant = os.path.join(tools_dir, PNGQUANT)
    if not os.path.isfile(pngquant):
        raise ValueError("Missing file: %s" % pngquant)
    optipng = os.path.join(tools_dir, OPTIPNG)
    if not os.path.isfile(optipng):
        raise ValueError("Missing file: %s" % optipng)

    # quant this file and output to temp
    temp_file = tempfile.mktemp(suffix='.png', prefix='tmp_pngquant')
    if os.path.isfile(temp_file):
        os.remove(temp_file)
    cmd = pngquant + ' {0} {1} --output {2}'.format(number_of_colors, png_file, temp_file)
    status, stdout, stderr = _run_command(cmd)
    os.rename(temp_file, png_file)

    # optipng works in place on the file (replaces the orig)
    cmd = optipng + ' -{0} {1}'.format(quality, png_file)
    status, stdout, stderr = _run_command(cmd)

    #st = os.stat(png_file)
    #print("Optimized image file: %s (size = %s)" % (png_file, st.st_size))


def change_pixel_density(image_file, density):
    """
    This function uses https://imagemagick.org/script/convert.php to
    update the image's pixel density.
    """
    os.stat(image_file)

    tools_dir = os.environ[TOOLS_DIR_ENV_VAR]
    image_magick_dir = os.path.join(tools_dir, IMAGE_MAGICK_DIR)
    if not os.path.isdir(image_magick_dir):
        raise ValueError("Missing directory: %s" % image_magick_dir)
    lib_dir = os.path.join(image_magick_dir, "lib")
    convert_tool = os.path.join(image_magick_dir, "bin", "convert")
    settings = { "DYLD_LIBRARY_PATH" : lib_dir }
    cmd = convert_tool
    cmd += ' %s -units PixelsPerInch -density %s %s' % (image_file, density, image_file)
    status, stdout, stderr = _run_command(cmd, settings)


def _get_first_file_in_tarball(tar_file, file_type=DEFAULT_IMAGE_TYPE, dest_dir=None):
    try:
        tar = tarfile.open(tar_file)
    except tarfile.ReadError, e:
        raise RuntimeError("%s: %s" % (e, tar_file))
    members = tar.getmembers()
    members = [x.name for x in members]
    members = [x for x in members if x.endswith(file_type)]
    if not members:
        return None
    members.sort()
    first_image_name = members[0]
    if not dest_dir:
        dest_dir = tempfile.mkdtemp()
    tar.extract(first_image_name, path=dest_dir)
    tar.close()
    first_file = os.path.join(dest_dir, first_image_name)
    return first_file


def get_image_file_count(tar_file, image_file_type=DEFAULT_IMAGE_TYPE):
    """
    Given a tar file, this function will return the count
    of PNG image files that it contains.
    """
    os.stat(tar_file)

    if tar_file.endswith(image_file_type):
        return 1
    try:
        tar = tarfile.open(tar_file)
    except tarfile.ReadError, e:
        raise RuntimeError("%s: %s" % (e, tar_file))
    members = tar.getmembers()
    tar.close()
    members = [x.name for x in members]
    members = [x for x in members if x.endswith(image_file_type)]
    file_count = len(members)
    return file_count


def _get_sips_info(image_file, property, sips=SIPS):
    os.stat(image_file)

    if not os.path.isfile(sips):
        raise ValueError("Missing file: %s" % sips)
    if image_file.endswith('.tar'):
        tar_file = image_file
        image_file = _get_first_file_in_tarball(tar_file)
        if not image_file:
            raise ValueError("No image files found in: %s" % tar_file)
    cmd = sips + " -g %s %s | tail -1 | awk '{print $2}'" % (property, image_file)
    status, stdout, stderr = _run_command(cmd, shell=True)
    value = int(stdout.strip().split()[0])
    #print("%s of %s = %s" % (property, image_file, value))
    return value


def get_pixel_height(image_file):
    """
    Given an image file (or a tar file that contains image files),
    this function will return the height of the image (or the first
    image in the tar file) in pixels.
    """
    height = _get_sips_info(image_file, "pixelHeight")
    return height


def get_pixel_width(image_file):
    """
    Given an image file (or a tar file that contains image files),
    this function will return the width of the image (or the first 
    image in the tar file) in pixels.
    """
    width = _get_sips_info(image_file, "pixelWidth")
    return width


if __name__ == "__main__":
    image_files = sys.argv[1:]
    for image_file in image_files:
        optimize_image_file(image_file)


