import maya.cmds as mc

MECH_EYE = "mech_eye"

OUTPUT_INPUT_ATTR_ALL_DRV_DICT = {"mech_eyes_all_drv_loc_scaleX.output": "mech_eyes_all_drv_loc.scaleX",
                                   "mech_eyes_all_drv_loc_rotateZ.output": "mech_eyes_all_drv_loc.rotateZ",
                                   "mech_eyes_all_drv_loc_translateX.output": "mech_eyes_all_drv_loc.translateX",
                                   "mech_eyes_all_drv_loc_translateY.output": "mech_eyes_all_drv_loc.translateY",
                                  "mech_eyes_all_drv_loc_scaleY.output": "mech_eyes_all_drv_loc.scaleY",

                                  "mech_eye_R_drv_loc_rotateZ.output": "mech_eye_R_drv_loc.rotateZ",
                                  "mech_eye_R_drv_loc_translateX.output": "mech_eye_R_drv_loc.translateX",
                                  "mech_eye_R_drv_loc_scaleY.output": "mech_eye_R_drv_loc.scaleY",
                                  "mech_eye_R_drv_loc_scaleX.output": "mech_eye_R_drv_loc.scaleX",
                                  "mech_eye_R_drv_loc_translateY.output": "mech_eye_R_drv_loc.translateY",

                                  "mech_eye_L_drv_loc_rotateZ.output": "mech_eye_L_drv_loc.rotateZ",
                                  "mech_eye_L_drv_loc_translateX.output": "mech_eye_L_drv_loc.translateX",
                                  "mech_eye_L_drv_loc_scaleY.output": "mech_eye_L_drv_loc.scaleY",
                                  "mech_eye_L_drv_loc_scaleX.output": "mech_eye_L_drv_loc.scaleX",
                                  "mech_eye_L_drv_loc_translateY.output": "mech_eye_L_drv_loc.translateY"
                                  }

OUTPUT_INPUT_ATTR_JNTS_DICT = {
                                  "mech_eye_R_drv_loc.scale":"eyeLid_R_bttm_jnt_grp.scale",
                                  "mech_eye_R_drv_loc.scale":"eye_R_jnt_grp.scale",

                                  "mech_eye_L_drv_loc.scale": "eyeLid_L_bttm_jnt_grp.scale",
                                  "mech_eye_L_drv_loc.scale": "eye_L_jnt_grp.scale",

                                  "mech_eyes_all_drv_loc.translate":"eyes_jnt_grp.translate",
                                  "mech_eyes_all_drv_loc.rotate":"eyes_jnt_grp.rotate",
                                  "mech_eyes_all_drv_loc.scale":"eyes_jnt_grp.scale"
                               }

JNT_CONSTRAINTS = {"eye_L_jnt_grp_parentConstraint1":["parentConstraint","mech_eye_L_drv_loc","eye_L_jnt_grp"],
                   "eye_R_jnt_grp_parentConstraint1":["parentConstraint","mech_eye_R_drv_loc","eye_R_jnt_grp"]
                   }

JNTS_PARENTING_INFO = {"eyeLid_R_top_jnt_grp":"mech_eye_R_drv_loc",
                    "eyeLid_R_bttm_jnt_grp":"mech_eye_R_drv_loc",
                    "eyeLid_L_top_jnt_grp":"mech_eye_L_drv_loc",
                    "eyeLid_L_bttm_jnt_grp":"mech_eye_L_drv_loc"}

EYES_DRV_GRP = "eyes_drv_grp"
JNT_GRP = "jnt_grp"

class AdjustEyeRig(object):

    def populate_eye_data(self, side="_L_"):

        self.eye_jnt_grp = "eye" + side + "jnt_grp"
        self.loc = "|actor_grp|drv_grp|eyes_drv_grp|mech_eyes_all_drv_loc|mech_eye" + side + "drv_loc"
        self.eye_shape = "eye" + side + "geoShape"

        self.bttm_lid = "eyeLid" + side + "bttm_geoShape"
        self.top_lid = "eyeLid" + side + "top_geoShape"

        self.output_input_attr_dict = {MECH_EYE + side + "drv_loc_scaleX.output": self.loc + "." +"scaleX",
                                        MECH_EYE + side + "drv_loc_rotateZ.output": self.loc + "." +"rotateZ",
                                        MECH_EYE + side + "drv_loc_translateX.output": self.loc + "." +"translateX",
                                        MECH_EYE + side + "drv_loc_translateY.output": self.loc + "." +"translateY",
                                        MECH_EYE + side + "drv_loc_scaleY.output": self.loc + "." +"scaleY",
                                       "eyeLid"+ side +"top_bend_jnt_scaleY.output": "eyeLid"+ side +"top_bend_jnt.scaleY",
                                       "eyeLid" + side + "btm_bend_jnt_scaleY.output": "eyeLid" + side + "bttm_bend_jnt.scaleY"
                                       }

        # todo: change the names of lid joints
        self.geo_jnts_dict = {
            self.bttm_lid: ["eyeLid" + side + "bttm_bend_jnt",
                            "eyeLid" + side + "bttm_base_jnt"],
            self.top_lid: ["eyeLid" + side + "top_bend_jnt",
                           "eyeLid" + side + "top_base_jnt"],
            self.eye_shape:["eye" + side + "innerTop_jnt", "eye" + side + "outerTop_jnt",
                            "eye" + side + "outerBtm_jnt", "eye" + side + "innerBtm_jnt"],
            "eye_L_glow_geoShape": ["eye_L_innerTop_jnt", "eye_L_outerTop_jnt",
                                    "eye_L_outerBtm_jnt", "eye_L_innerBtm_jnt"],
            "eye_R_glow_geoShape": ["eye_R_innerTop_jnt", "eye_R_outerTop_jnt",
                                    "eye_R_outerBtm_jnt", "eye_R_innerBtm_jnt"]
            }

    def disconnect_mesh(self):
        mc.setAttr(EYES_DRV_GRP + ".visibility", True)
        mc.setAttr(JNT_GRP + ".visibility", True)



        self.disconnect_mesh_side(side="_L_")
        self.disconnect_mesh_side(side="_R_")



    def connect_mesh(self):
        self.connect_mesh_side(side="_L_")
        self.connect_mesh_side(side="_R_")

    def disconnect_jnts(self):

        for output, input in OUTPUT_INPUT_ATTR_JNTS_DICT.iteritems():
            try:
                mc.disconnectAttr(output, input)
            except Exception:
                print ("skiped %s" %(input))
        # mc.disconnectAttr("mech_eye_R_drv_loc.scale", "eyeLid_R_bttm_jnt_grp.scale")

        for constr, constr_info in JNT_CONSTRAINTS.iteritems():
            try:
                mc.delete(constr)
            except Exception:
                print "skipping %s constraint deletion" %(constr)

        for jnt_child, jnt_parent in JNTS_PARENTING_INFO.iteritems():
            try:
                mc.parent(jnt_child, world=True)
            except Exception:
                print ("skipping unparenting %s" % (jnt_child))

    def disconnect_main_loc(self):
        for output, input in OUTPUT_INPUT_ATTR_ALL_DRV_DICT.iteritems():
            try:
                mc.disconnectAttr(output, input)
            except Exception:
                print ("skipping %s, %s" %(output, input))

    def connect_main_loc(self):
        for output, input in OUTPUT_INPUT_ATTR_ALL_DRV_DICT.iteritems():
            mc.connectAttr(output, input)

    def connect_jnts(self):
        for jnt_child, jnt_parent in JNTS_PARENTING_INFO.iteritems():
            try:
                mc.parent(jnt_child, jnt_parent)
            except Exception:
                print ("skipping parenting %s to %s" % (jnt_child, jnt_parent))

        for constr, constr_info in JNT_CONSTRAINTS.iteritems():
            if constr_info[0] == "parentConstraint":
                try:
                    mc.parentConstraint(constr_info[1], constr_info[2], mo=True)
                except Exception:
                    print ("skipping parenting %s to %s" % (constr_info[1], constr_info[2]))


        for output, input in OUTPUT_INPUT_ATTR_JNTS_DICT.iteritems():
            try:
                mc.connectAttr(output, input)
            except Exception:
                print ("skiped %s" % (input))


    def disconnect_mesh_side(self, side="_L_"):
        self.populate_eye_data(side=side)

        # unbind eye and lids
        mc.skinCluster(self.eye_shape, e=True, unbindKeepHistory=True)
        mc.skinCluster(self.bttm_lid, e=True, unbindKeepHistory=True)
        mc.skinCluster(self.top_lid, e=True, unbindKeepHistory=True)
        for output, input in self.output_input_attr_dict.iteritems():
            try:
                mc.disconnectAttr(output, input)
            except Exception:
                print ("skipping %s, %s" %(output, input))

        mc.setAttr("eyeLid"+side+"top_bend_jnt.scaleY", 1)
        mc.setAttr("eyeLid" + side + "bttm_bend_jnt.scaleY", 1)


    def connect_mesh_side(self, side="_L_"):
        self.populate_eye_data(side=side)

        # reskin
        for geo, jnts in self.geo_jnts_dict.iteritems():
            try:
                mc.skinCluster(jnts, geo, tsb=True)
            except Exception:
                print ("skipping %s, %s " %(geo, jnts))

        mc.setAttr("eyeLid"+side+"top_bend_jnt.scaleY", 0)
        mc.setAttr("eyeLid" + side + "bttm_bend_jnt.scaleY", 0)

        #restore connections
        for output, input in self.output_input_attr_dict.iteritems():
            try:
                mc.connectAttr(output, input)
            except Exception:
                print ("skiped %s" % (input))


def lockUnlockEyeAttrs(lock=True):
    keyable_state = False
    lock_state = True
    axis = ["Z"]

    if not lock:
        keyable_state = True
        lock_state = False
        axis = ["X", "Y", "Z"]

    for ax in axis:
        mc.setAttr("mech_eyes_all_ctrl.translate" + ax, k=keyable_state, lock=lock_state)
        mc.setAttr("mech_eye_L_ctrl.translate" + ax, k=keyable_state, lock=lock_state)
        mc.setAttr("mech_eye_R_ctrl.translate" + ax, k=keyable_state, lock=lock_state)

        mc.setAttr("mech_upperLid_R_ctrl.translate" + ax, k=keyable_state, lock=lock_state)
        mc.setAttr("mech_upperLid_L_ctrl.translate" + ax, k=keyable_state, lock=lock_state)
        mc.setAttr("eyeCorner_L_innerTop_ctrl.translate" + ax, k=keyable_state, lock=lock_state)
        mc.setAttr("eyeCorner_L_OuterTop_ctrl.translate" + ax, k=keyable_state, lock=lock_state)

        mc.setAttr("eyeCorner_L_OuterBtm_ctrl.translate" + ax, k=keyable_state, lock=lock_state)
        mc.setAttr("eyeCorner_L_innerBtm_ctrl.translate" + ax, k=keyable_state, lock=lock_state)

        mc.setAttr("mech_L_pupil_ctrl.translate" + ax, k=keyable_state, lock=lock_state)

        mc.setAttr("eyeCorner_R_innerTop_ctrl.translate" + ax, k=keyable_state, lock=lock_state)
        mc.setAttr("eyeCorner_R_OuterTop_ctrl.translate" + ax, k=keyable_state, lock=lock_state)

        mc.setAttr("eyeCorner_R_OuterBtm_ctrl.translate" + ax, k=keyable_state, lock=lock_state)
        mc.setAttr("eyeCorner_R_innerBtm_ctrl.translate" + ax, k=keyable_state, lock=lock_state)

        mc.setAttr("mech_R_pupil_ctrl.translate" + ax, k=keyable_state, lock=lock_state)
        mc.setAttr("mech_lwrLid_L_ctrl.translate" + ax, k=keyable_state, lock=lock_state)
        mc.setAttr("mech_lwrLid_R_ctrl.translate" + ax, k=keyable_state, lock=lock_state)

        mc.setAttr("eyeCorner_R_OuterTop_ctrl.scale" + ax, k=keyable_state, lock=lock_state)
        mc.setAttr("eyeCorner_L_OuterTop_ctrl.scale" + ax, k=keyable_state, lock=lock_state)
        mc.setAttr("eyeCorner_R_innerTop_ctrl.scale" + ax, k=keyable_state, lock=lock_state)
        mc.setAttr("eyeCorner_L_innerTop_ctrl.scale" + ax, k=keyable_state, lock=lock_state)

        mc.setAttr("eyeCorner_R_OuterBtm_ctrl.scale" + ax, k=keyable_state, lock=lock_state)
        mc.setAttr("eyeCorner_L_OuterBtm_ctrl.scale" + ax, k=keyable_state, lock=lock_state)
        mc.setAttr("eyeCorner_R_innerBtm_ctrl.scale" + ax, k=keyable_state, lock=lock_state)
        mc.setAttr("eyeCorner_L_innerBtm_ctrl.scale" + ax, k=keyable_state, lock=lock_state)

    # need to lock eye corners translation
    if lock:
        axis = ["X", "Y", "Z"]
        for ax in axis:
            mc.setAttr("eyeCorner_R_OuterTop_ctrl.translate" + ax, k=keyable_state, lock=lock_state)
            mc.setAttr("eyeCorner_L_OuterTop_ctrl.translate" + ax, k=keyable_state, lock=lock_state)
            mc.setAttr("eyeCorner_R_innerTop_ctrl.translate" + ax, k=keyable_state, lock=lock_state)
            mc.setAttr("eyeCorner_L_innerTop_ctrl.translate" + ax, k=keyable_state, lock=lock_state)

            mc.setAttr("eyeCorner_R_OuterBtm_ctrl.translate" + ax, k=keyable_state, lock=lock_state)
            mc.setAttr("eyeCorner_L_OuterBtm_ctrl.translate" + ax, k=keyable_state, lock=lock_state)
            mc.setAttr("eyeCorner_R_innerBtm_ctrl.translate" + ax, k=keyable_state, lock=lock_state)
            mc.setAttr("eyeCorner_L_innerBtm_ctrl.translate" + ax, k=keyable_state, lock=lock_state)