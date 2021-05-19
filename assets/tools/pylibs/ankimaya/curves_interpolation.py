# Copies the base layer, turns all animation curves to have linear interpolation for export and
# later deletes it. This way we can have interpolation that animators would expect to see on the
# robot

# Original purpose of this class is to fix curve interpolation problem when exporting animation.

# daria.jerjomina@anki.com
# August 16, 2016: start
# August 20, 2016: fixed where the error is being shown, added overriding

# Copying ctrs gives unpredicted

import maya.cmds as mc
from ankimaya import ctrs_manager

CURVE_ADJUSTMENT_LAYER = "curveAdjustmentLayer"

class CurvesInterpolation(object):
    def __init__(self):
        self.is_export = True
        self.root_layer = mc.animLayer(query=True, root=True)

    def create_exporter_layer(self, ctrs):
        mc.animLayer(CURVE_ADJUSTMENT_LAYER)
        mc.select(ctrs)
        mc.animLayer(CURVE_ADJUSTMENT_LAYER, edit=True, addSelectedObjects=True)
        self.root_layer = mc.animLayer(query=True, root=True)

    def clean_layers(self):
        mc.animLayer(self.root_layer, edit=True, selected=True, preferred=True,
                     lock=False, override=True)
        if CURVE_ADJUSTMENT_LAYER in mc.ls(type='animLayer'):
            mc.delete(CURVE_ADJUSTMENT_LAYER)

    def switch_to_new_layer(self):
        mc.animLayer(self.root_layer, edit=True, selected=False, preferred=False, lock=True,
                     override=False)
        if CURVE_ADJUSTMENT_LAYER in mc.ls(type='animLayer'):
            mc.animLayer(CURVE_ADJUSTMENT_LAYER, edit=True, selected=True, preferred=True,
                         lock=False, override=True)

    def switch_to_root_layer(self):
        if CURVE_ADJUSTMENT_LAYER in mc.ls(type='animLayer'):
            mc.animLayer(CURVE_ADJUSTMENT_LAYER, edit=True, selected=False, preferred=False,
                         lock=True, override=False)
        mc.animLayer(self.root_layer, edit=True, selected=True, preferred=True, lock=False,
                     override=True)

    def copy_ctrs_animation(self, ctrs):
        for ctr in ctrs:
            self.switch_to_root_layer()
            mc.copyKey(ctr)
            self.switch_to_new_layer()
            try:
                mc.pasteKey(ctr)
            except RuntimeError:  # If there are no keys on a ctr
                pass
            mc.keyTangent(ctr, inTangentType='linear', outTangentType='linear')

    def before_export(self):
        keyed_ctrs = ctrs_manager.get_keyed_ctrs(skip_muted=False)
        keyed_attrs = ctrs_manager.get_keyed_attrs()
        layers = mc.ls(type='animLayer')
        if len(layers) > 1:
            mc.warning("There should not be more than one animation layer prior to export. Curve "
                     "interpolation will not be accounted for")
            self.is_export = False
            return
        self.create_exporter_layer(keyed_ctrs)
        self.copy_ctrs_animation(keyed_attrs)
        self.switch_to_new_layer()

    def after_export(self):
        """
        Should be triggered when export finished or when export cannot be completed
        """
        if self.is_export:
            self.clean_layers()
        #else:
        #    print("did not use curve interpolation")


