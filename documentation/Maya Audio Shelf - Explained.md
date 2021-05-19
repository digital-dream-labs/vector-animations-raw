# Maya Audio Shelf: Explained

Created by Andrew Bertolini 

The vast majority of the work we do in Maya utilizes a custom set of proprietary tools called the Audio Shelf.

Each of these tools has a specific function, there are some that we use more than others but most of them are used at some point. See below for what the shelf looks like and for further information on each of the tools.


![](images/Screen%20Shot%202019-03-04%20at%202.20.56%20PM.png)


## 1. Select AudioNode: ![](images/Screen%20Shot%202019-02-22%20at%201.26.34%20PM.png)

This will enable the display of Audio Keyframes in your timeline window. If there are any audio keyframes present on the timeline they will appear as red lines.

![](images/Screen%20Shot%202019-02-22%20at%2011.18.04%20AM.png)


From time to time the keyframes will disappear, simply press this button again to toggle their display back on.

2. Refresh Audio Data: ![](images/Screen%20Shot%202019-02-22%20at%201.26.43%20PM.png)

This is used to update the audio data that Maya is referencing. You would use this after changing which the soundbank directory Maya is referencing. Once you've changed the directory this button will load the correct audio data and the audio events from said soundbank will be present in Maya.


3. Magic Update Audio Ghosts: ![](images/Screen%20Shot%202019-02-22%20at%201.36.16%20PM.png)

This will refresh any/all audio keyframes in the animation clip. If you add or delete an audio keyframe, by default you'll have to let the animation play through one entire cycle before the newly added/deleted keyframes are played appropriately. This button will force a refresh so what you hear on first playback is accurate.

4. Preview on Device: ![](images/Screen%20Shot%202019-02-22%20at%201.26.49%20PM.png)

This is a quick playback tool that will play the last exported animation on your robot. This is more useful when working in a Maya project that only has one animation clip. For anything more complex than that it would be more efficient to use the Preview Selection Tool. 

5. Get Audio Soundbanks: ![](images/Screen%20Shot%202019-02-22%20at%201.26.52%20PM.png)

This is mostly used by the animators. This will pull the latest committed SoundBanks that are sitting at the Head of Audio Repo. This is used when an animator needs to pull in the latest audio work that has been committed but might not be in Master yet.

6. Preview Selection Tool: ![](images/6.png)

This is an advanced animation playback tool that will allow you to force play an animation on your robot. It also includes tools to manage your robot, such as: Rebooting, loading assets, and OTA'ing your robot.

7. Audio Settings: ![](images/Screen%20Shot%202019-02-22%20at%201.38.33%20PM.png)

This is one of the main tools you will use when working with audio in Maya. This button will show you any audio keyframe in the active animation clip that you are working in. It will also show you the frame timestamp for each audio keyframe. The window looks like this:

![](images/Screen%20Shot%202019-03-21%20at%2012.00.12%20PM.png)

By clicking on any of the keyframes above, your timeline will snap to that keyframe's position and will give you access to the properties of the keyframe in the Audio Tool(see #12 for more details).

8. Load Vic Rig: ![](images/Screen%20Shot%202019-02-22%20at%201.40.48%20PM.png)

This is mostly used by the animators when creating a brand new animation. This will load the default Victor rig into the Maya project.

9. Low-Res Mesh:  ![](images/Screen%20Shot%202019-02-22%20at%201.27.13%20PM.png)

This will load a lower resolution mesh model for the robot. This can be used to improve playback FPS if your computer is having issues with performance.

10. Mid-Res Mesh:  ![](images/Screen%20Shot%202019-02-22%20at%201.27.20%20PM.png)

This will load a slightly higher resolution mesh model for the robot. This can have negative effects on computer performance though.

11. Export Animation and Audio:  ![](images/Screen%20Shot%202019-02-22%20at%201.27.40%20PM.png)

This is used to export animation and audio data into a readable format for the robot(.tar) This tools has been wrapped into the Publisher but we still use it for certain workflows. If for example you wanted to test local audio changes on robot you could: Modify the needed audio keyframes, export animation and audio data, and then send your local version of that .tar file directly to your robot to test before committing. See "Preview Selection Tool" section above for how to do this.

12. Audio Tool:  ![](images/Screen%20Shot%202019-02-22%20at%201.27.46%20PM.png)

This is the main tool we use to add/delete/modify audio keyframes in Maya. The window looks like this:

![](images/Screen%20Shot%202019-03-21%20at%201.06.06%20PM.png)

### Wwise ID Enum:

We name our audio events using a very particular naming convention that is then used to sort our events by Wwise ID Enum. Looking at the event above *Play__Robot_Vic_Sfx__Lift_High_Down_Long_Sad* the enum would be *Robot_Vic_Sfx*. Changing the ID Enum is a quick way to toggle between different sets of audio events used across the robot.

### Event Name:

This is simply the full audio event name. If you want to search for a specific audio event you can input keywords in the empty text field to the right of the Event Name drop down menu.

### Probability:

This value controls the overall likelihood that an audio keyframe will be played when being called upon. 100% will result in a successful playback every time the keyframe is called, with lesser values resulting in few successful plays.

### Volume:

This controls the overall volume that a keyframe will be played coming off the robot. This is independent of Wwise volumes but works additively with Wwise's gain structure.

### Set Keyframe:

This is how you "save" your changes to an audio keyframe. If you do not press this button your changes will not be written to that keyframe and will be lost. This is independent of saving your project, you will need to do both.

### 13. Publisher: !()[Screen Shot 2019-03-04 at 2.34.37 PM.png]

This is an all-in-one tool for committing modified Maya files and updated .tar files to the animation repositories. It runs a series of tests to verify that your changes are in-fact ready for commit and will prompt you if any conditions are not met. It looks like:

!()[Screen%20Shot%202019-03-21%20at%203.52.57%20PM.png]


14. Temp Function: !()[Screen%20Shot%202019-02-22%20at%201.45.42%20PM.png]

This is a tool that we don't actively use, and I'm unsure if it currently works properly. It was originally intended to query the Maya project for any audio keyframe under or behind the playhead.
