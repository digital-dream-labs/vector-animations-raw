# Setting up Head-Angle Specific Animations and populating Anim Groups

Created by Daria Jerjomina Aug 29, 2016

Pressing "Generate multiple head angle animations" button in Maya (courtesy of COZMO-2108) will take "anim_blah" animation clip and generate "anim_blah__head_angle_-20", "anim_blah__head_angle_20" and "anim_blah__head_angle_40" clips. Your timeline will expand to fit all the new animations. Animations are copied from the original one but "x:mech_head_ctrl" is changed in each new animation. The values at the end of head angle clips specify how is the rotateX curve of "x:mech_head_ctrl" being updated and how much it's values shift. Note that if the value at the end of the clip is positive, for example 40, the RotateX curve of the "x:mech_head_ctrl" will move down by the value of 40, so if your head's keyframe was at 10, in the copied clip it will be at -30.

If you are setting up an animation group with head-angle specific animations, you will typically have four of those animations. For each of those, you will need to specify the min and max head-angle values in the animation group editor:

1. for the "anim_blah_-20" animation, use -25 for the min value and -10 for the max value
2. for the "anim_blah" (or "anim_blah_0") animation, use -10 for the min value and 10 for the max value
3. for the "anim_blah_20" animation, use 10 for the min value and 30 for the max value
4. for the "anim_blah_40" animation, use 30 for the min value and 45 for the max value

Because values on the robot are reversed from the RotateX values of the "x:mech_head_ctrl" we have a separate attribute Real Head Angle on that controller for you to be able to tell the real value of the head rotation which min and max keys of the animation group correspond to.