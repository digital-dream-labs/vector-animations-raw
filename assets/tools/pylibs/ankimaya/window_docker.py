"""
https://gist.github.com/mottosso/c853b6fd9fb963e6f3e7c7a4f53b649d
this came from Marcus Ottoson
"""

DOCKING_WINDOW = ['MacBlast', 'PreviewSettings', 'ChannelBoxLayerEditor', 'AttributeEditor']


from maya import OpenMayaUI as omui
from maya import cmds

# Maya 2016 uses PySide and Maya 2017+ uses PySide2, so try PySide2 first before resorting to PySide
try:
    from PySide2.QtCore import *
    from PySide2.QtGui import *
    from PySide2.QtWidgets import *
    from PySide2.QtUiTools import *
    from shiboken2 import wrapInstance
except ImportError:
    from PySide.QtCore import *
    from PySide.QtGui import *
    from PySide.QtUiTools import *
    from shiboken import wrapInstance


def Dock(Widget, width=300, show=True, winTitle='DockableWindow', **kwargs):
    """
    Dock `Widget` into Maya

    Arguments:
        Widget (QWidget): Class
        show (bool, optional): Whether to show the resulting dock once created
    """
    tabControl = "AttributeEditor"
    name = Widget.__name__
    label = getattr(Widget, "label", name)

    try:
        cmds.deleteUI(name)
    except RuntimeError:
        pass

    for dw in DOCKING_WINDOW:
        if cmds.workspaceControl(dw, exists=True) and cmds.workspaceControl(dw, q=True, visible=True):
            tabControl = dw
            break

    dockControl = cmds.workspaceControl(
        name,
        tabToControl=[tabControl, -1],
        initialWidth=320,
        minimumWidth=False,
        widthProperty="free",
        label=winTitle
    )

    dockPtr = omui.MQtUtil.findControl(dockControl)
    dockWidget = wrapInstance(long(dockPtr), QDockWidget)
    dockWidget.setAttribute(Qt.WA_DeleteOnClose)
    child = Widget(dockWidget, **kwargs)
    dockWidget.layout().addWidget(child)

    if show:
        cmds.evalDeferred(
            lambda *args: cmds.workspaceControl(
                dockControl,
                edit=True,
                restore=True
            )
        )

    return child, dockWidget, dockControl


