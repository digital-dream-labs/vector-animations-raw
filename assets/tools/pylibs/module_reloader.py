"""
This script will search for all loaded modules from a set of
packages defined in ANKI_PACKAGES. Those loaded modules will
then be removed from sys.modules and reloaded.

This allows you to:

    reload(top_level_module)

and it will reload the modules that top_level_module.py
depends on.

(c) 2018 Anki, Inc.

Chris Rogers 9/2018
"""

import sys
import importlib
from maya import cmds


VERBOSE = True

ANKI_PLUGINS = ['AnkiMenu.py']

ANKI_PACKAGES = ['ankimaya', 'ankiutils', 'ankisdk']


def get_loaded_modules(packages, ignore_this=True):
    """
    By looking in sys.modules, this function will return a
    list of all the modules that are currently loaded from
    the list of packages that was provided.
    """
    loaded_modules = []
    for name, mod in sys.modules.items():
        if mod is None:
            # this appears in sys.modules but is not a loaded object
            continue
        if ignore_this and name == __name__:
            # ignore this module
            continue
        for package in packages:
            if name.startswith(package):
                loaded_modules.append(name)
                if VERBOSE:
                    print("Before reloading: {0} -> {1}".format(name, mod))
                break
    return loaded_modules


def reload_plugins(plugins=ANKI_PLUGINS):
    for plugin in plugins:
        if cmds.pluginInfo(plugin, query=True, loaded=True):
            cmds.unloadPlugin(plugin)
        try:
            cmds.loadPlugin(plugin)
        except RuntimeError:
            cmds.warning("Failed to load plugin: {0}".format(plugin))
        else:
            print("Reloaded {0}".format(plugin))


def reload_modules(packages=ANKI_PACKAGES):
    loaded_modules = get_loaded_modules(packages)
    for name in loaded_modules:
        del sys.modules[name]
    for name in loaded_modules:
        importlib.import_module(name)
        if VERBOSE:
            print("After reloading: {0} -> {1}".format(name, sys.modules[name]))


