# Conversions to FBX, DAE, OBJ and other 3D formats

These assets has been exported from Maya (.ma) without modifing the source asset files, and contained warnings and errors for features that are not compatible with Maya.
Mainly there were warnings for usupported maps/textures, animation curves, skin definitions, and hierarchy issues...

## Goals

### To create two new separated rig assets files (mid_res & low_res), allowing full both-directionally compatible import and export (from and to fbx)

Here are concept suggestions and optimization ideas of how to proceed with the new rig files:

#### **1. Victor_rig_mid_res.fbx**
 - a) preserve same avatar hierarchy (rig skeleton root bone) for this asset and anim assets, which will reference this rigged model 
 - b) remove `low_res_grp` from `actor_grp`>`geo_grp`
 - c) remove the `screenEdge_geo` from `actor_grp`>`geo_grp`>`Eye_rig_geo_grp` as it is duplicate of `originalScreenEdge_geo`, but is not linked, contstained, and only causes disturbance in animations
 - d) remove the `overscan_0_geo` from `actor_grp`>`geo_grp`>`Eye_rig_geo_grp` as overscan lines are not valid for Vector and are artifacts of Cozmo
 - e) fix the trasform hierarchy for the forks (arms) joints
    - a new transform (joint group node) named `arms_jnt` should be created under `actor_grp`>`jnt_grp`>`body_jnt`
    - `fork_jntGRP` to be placed under this new `arms_jnt` instead of `root_jnt`
    - `lowArm_jnt` to be placed under this new `arms_jnt` instead of `body_jnt`
    - `upperArm_jnt` to be placed under this new `arms_jnt` instead of `body_jnt`
    This will similarily to `asd` make the `arms_jnt` the only transform to ajust the fork angle from one place/rotationX property
    
... 

TBA: more will be added ...
