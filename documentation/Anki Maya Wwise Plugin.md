# Anki Maya Wwise Plugin

Created by Jordan Rivas  Aug 09, 2018

## Intro

The AnkiMayaWwisePlugin is used by Maya to perform audio events/tasks inserted in a Cozmo or Victor Animation. The plugin is loaded by Maya and uses Maya environment variables to setup the audio engine (Wwise). The plugin is maintained in the Animation repo so it can be easily loaded with the other animation tools and plugins.

## Building Plugin
## Maya 2018, Wwise 2016.2.1

Source code is in Anki-Audio git repo and is setup to build using CMake, similar to Victor. Due to linking complexities the easiest way to build the plugin is to build it alongside the victor project. By default the plug does NOT build, you must have Maya 2018 installed to build against. The simplest way to build the plugin is to use a script which properly configures and builds it. See <victor_repo_root>/project/victor/scripts/build_maya_wwise_plugin.sh

This script basically runs this command:

`project/victor/build-victor.sh -f -S -p mac -c Release -t anki_maya_wwise_plugin -a -DBUILD_MAYA_WWISE_PLUGIN=ON`