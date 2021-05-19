# Auto-saving Maya Scenes
Created by Nishkar Grover Oct 05, 2016

Autodesk has a page with instructions for setting up the auto-save preferences in Maya.

We recommend:

* setting the save interval to approximately 5 or 10 minutes
* limiting the number of auto-saves to approximately 5
* setting the auto-save destination to a named folder, eg. $HOME/maya_auto_save

In that case Maya will automatically save Maya files to the specified folder at the interval that you specify and replace the oldest auto-save when it reaches the specified limit.

For example, if you are working on anim_freePlay_reactToFace_like_01.ma, Maya will save anim_freePlay_reactToFace_like_01.0001.ma, anim_freePlay_reactToFace_like_01.0002.ma, anim_freePlay_reactToFace_like_01.0003.ma, etc.  Those files will start to get replaced with newer versions when we exceed the auto-save limit that was set, eg. anim_freePlay_reactToFace_like_01.0001.ma will get removed when anim_freePlay_reactToFace_like_01.0006.ma is saved if we limit the number of auto-saves to 5.

If Maya crashes on you and you lose any work, you could simply copy the latest auto-saved file, eg. $HOME/maya_auto_save/anim_freePlay_reactToFace_like_01.0006.ma, on top of the original anim_freePlay_reactToFace_like_01.ma file that you created or opened in Maya (which probably lives under $HOME/workspace/cozmo-animation/scenes).

![](images/Screen%20Shot%202016-10-05%20at%202.45.23%20PM.png)
