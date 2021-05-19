# Copy Animation Clip

Created by Daria Jerjomina


This is a tool to copy animation from existing clip to a new one within the same timeline, or to a new file.

![](images/copy_anim_clip_tool.png)


It can be opened from the animation shelf, by pressing the following icon:

![](images/Screen%20Shot%202018-09-10%20at%2011.31.02%20AM.png)


## Animation Clip To Copy

As soon as the tool is open, Animation Clip To Copy drop down selection is being populated with the names of animation clips from that file. If the animation clips are changed, please reopen the tool so that it gets repopulated with the updated clips.

You can chose the clip from the menu. That will be the clip that's going to be copied.

![](images/Screen%20Shot%202018-09-10%20at%2010.58.02%20AM.png)


__The following example is from anim_loco_driving_happy.ma__

## Copied Clip Name

This is where the name of the clip that needs to be copied is being inserted. If no clip name is specified it will default to the name of your original clip with _copy at the end.

![](images/Screen%20Shot%202018-09-10%20at%2011.06.02%20AM.png)


## Starting Frame # For Copied Clip

You can specify the frame at which the animation from the chosen clip is going to be pasted. If no frame number is inserted it will be pasted after the last frame of your last clip.

![](images/Screen%20Shot%202018-09-10%20at%2011.09.01%20AM.png)


## Create new maya file

By default your clip will be copied inside of the same scene, however you can chose to copy it to the new scene by checking the Create new maya file checkbox.

That will show the line for inserting the name of the file that will be opened after you press Copy.

![](images/Screen%20Shot%202018-09-10%20at%2011.26.04%20AM.png)


## Overwriting existing animation

In case there already are keyframes after the frame that you have specified in the copy tool the tool will ask you for the permission to overwrite them.

![](images/Screen%20Shot%202018-09-10%20at%2011.21.56%20AM.png)


## Unsaved changes before copying to the new file

![](images/Screen%20Shot%202018-09-10%20at%2011.27.11%20AM.png)


If you have unsaved changes in your current scene and you want to copy animation to the new scene, you will be warned about closing the current scene and opening the new one. The copy animation clip tool doesn't save any changes, incase you might want them to be overwritten.