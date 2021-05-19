
SCENE_OPENED_EVENT_NAME = "SceneOpened"


from maya import cmds
from maya import OpenMaya


BEFORE_SCENE_OPENED_EVENT = OpenMaya.MSceneMessage.kBeforeOpen


_sceneOpenedJobs = []


def _addCallback(func, eventName, trackingList):
    id = OpenMaya.MEventMessage.addEventCallback(eventName, func)
    trackingList.append(id)
    try:
        funcName = func.im_func.func_name
    except AttributeError:
        funcName = func.func_name
    #print("Registered '%s' event callback for %s()" % (eventName, funcName))
    return id


def _addScriptJob(func, eventName, trackingList):
    id  = cmds.scriptJob(event=[eventName, func], protected=True)
    trackingList.append(id)
    try:
        funcName = func.im_func.func_name
    except AttributeError:
        funcName = func.func_name
    #print("Registered script job to execute %s() when '%s' becomes false" % (funcName, eventName))
    return id


def _removeCallback(id, trackingList):
    try:
        trackingList.remove(id)
    except ValueError:
        #print("No existing callback in place for: %s" % id)
        pass
    else:
        OpenMaya.MMessage.removeCallback(id)
        #print("Removed event callback for: %s" % id)


def _removeScriptJob(id, trackingList):
    unknownMsg = "No existing script job in place for: %s" % id
    try:
        trackingList.remove(id)
    except ValueError:
        #print(unknownMsg)
        pass
    if cmds.scriptJob(exists=id):
        cmds.scriptJob(kill=id, force=True)
        #print("Removed script job for: %s" % id)
    else:
        #print(unknownMsg)
        pass


def addBeforeSceneOpenedCallback(func, callbackEvent=BEFORE_SCENE_OPENED_EVENT):
    #callbackId = _addCallback(func, callbackEvent, _sceneOpenedJobs)
    callbackId = OpenMaya.MSceneMessage.addCallback(callbackEvent, func)
    return callbackId


def addSceneOpenedScriptJob(func, scriptJobEvent=SCENE_OPENED_EVENT_NAME):
    """
    Given a function/method, this function will setup the callback so
    that function/method is called whenever the scene is changed (a
    new scene or an existing scene opened). This function will return
    the ID for that callback so it can be later removed when needed.
    """
    scriptJobId = _addScriptJob(func, scriptJobEvent, _sceneOpenedJobs)
    return scriptJobId


def removeSceneOpenedScriptJob(scriptJobId):
    if scriptJobId is not None:
        _removeScriptJob(scriptJobId, _sceneOpenedJobs)


def showSceneFile(arg=None):
    currentTime = cmds.currentTime(query=True)
    print("Current time = %s and input argument = %s" % (currentTime, arg))
    sceneFile = cmds.file(query=True, sceneName=True)
    print("Current scene file = %s and input argument = %s" % (sceneFile, arg))


def test():
    addSceneOpenedScriptJob(showSceneFile)


