# Splitting Maya Scenes

Created by Shmuel Segal Jun 09, 2017

## Overview

This is a quick guide on how to split Maya scenes with multiple AnimClips.

## When to split Maya scenes

* We should avoid having 2 animators working on the same Maya scene at the same time. In those cases we should split the Maya scenes.

* When there's a Maya file with so many animation clips the scene become too heavy to work on. In those cases we should split the Maya scenes.

Remember, if you have many animation clips in a scene, and exporting the animations to the robot takes too long, you don't necessarily have to split the Maya scene. You can always check and uncheck clips to determined for the exporter what clips to export in the Game Exporter as you're iterating on the animations.

## Splitting scenes in Maya

[Example video](images/SplitMayaScenes.mp4)


## Steps

1. Open the Maya scene you need to split.
2. Save the same scene again and replace the number at the end of the file name. The file names should end up being:
   1. anim_splitscene_demo_01.ma.
   1. anim_splitscene_demo_02.ma.
3. Delete the AnimClips that are going to stay in anim_splitscene_demo_01.ma and keep the anim_splitscene_demo_02.ma AnimClips.
4. Save anim_splitscene_demo_02.ma.
5. Open anim_splitscene_demo_01.ma
6. Delete the AnimClips meant for anim_splits_scene_demo_02.ma and keep the ones for anim_splitscene_demo_01.ma
7. Save anim_splitscene_demo_01.ma and commit anim_splitscene_demo_01.ma and anim_splitscene_demo_02.ma in Cornerstone.
8. Export the animations from all the Maya scenes.
9. Commit the Maya files in Cornerstone.
10 Commit the tar files in Cornerstone.

Make sure there aren't any duplicate AnimClips between the different Maya scenes. Each Maya scene should hold different AnimClips with unique file names for Shotgun to link the files properly.
