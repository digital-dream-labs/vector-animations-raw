# Troubleshooting Cozmo's movement visualization

Created by Daria Jerjomina  Apr 26, 2019

Cozmo does not move in maya as expected.

For example: I am animating Cozmo move back, but instead he is moving forward.


1) Which movement setup are you using?

* I am using separate wheel controllers: x:wheel_R_ctrl and x:wheel_L_ctrl. (go to Step 2)
* I am using x:mech_all_ctrl and moac controller. (go to Step 6)
* I am using both separate wheel setup and the mech_all controller. (go to Step 7)
* I am using a different wheel setup - We currently only support animation using either x:mech_all_ctrl or using x:wheel_R_ctrl and x:wheel_L_ctrl. Please convert your animation to use either mech_all or separate wheel ctrs. If you need help with that please talk to Daria.


(2) Are the keys on x:wheel_R_ctrl and x:wheel_L_ctrl in sync?

Yes: go to Step 3

No/I don't know: Please run Missing Frames script. That will place keyframes on the wheel that has frames missing. For more information  please see Animate Movement using separate wheel controls the Shortcut Tools section.

Did that fix your issue?: Yes (Hurray!) No (Go to Step 3)

Explanation: Evaluation of Cozmo's movement is based on the two wheels. It calculates where Cozmo needs to be based on the keyframes and values between them. If at a certain frame there is a keyframe on one wheel but no keyframe on the other prediction of Cozmo's position will not be accurate.



(3) Is the interpolation between wheels keyframes linear?

Yes: go to Step 4

No/I don't know: Select all the wheels keyframes in the graph editor and click linear interpolation.

Did that fix your issue?: Yes (Hurray!) No (Go to Step 4)



(4) Are all the values on the moac controller 0ed out?

Yes: got to Step 5

No/I don't know: Select all the attributes of the moac controller and set them to 0.

Did that fix your issue?: Yes (Hurray!) No (Go to Step 5)

Explanation: The movement group that wheels control is parented under a moac controller. If it has values, cozmo won't be moving as expected.



(5) Refresh movement expression.

1) Open expression editor (Windows→Animation Editors→Expression Editor)

2) Click Edit button

3) Close Expression Editor

Did that fix your issue?: Yes (Hurray!) No (Talk to Daria)

Explanation: It seems like sometimes expression needs to be refreshed, clicking edit does the trick.

