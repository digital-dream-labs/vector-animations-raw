

TIME_CHANGED_EVENT_NAME = "timeChanged"
RANGE_CHANGED_EVENT_NAME = "playbackRangeChanged"

PLAYING_BACK_EVENT_NAME = "playingBack"


from maya import cmds
from maya import OpenMaya


_timeChangeCallback = []
_rangeChangeCallback = []
_timeChangeCallbackToScriptJobMapping = {}


def _addCallback(func, eventName, trackingList):
    id = OpenMaya.MEventMessage.addEventCallback(eventName, func)
    trackingList.append(id)
    try:
        funcName = func.im_func.func_name
    except AttributeError:
        funcName = func.func_name
    #print("Registered '%s' event callback for %s()" % (eventName, funcName))
    return id


def _addScriptJobConditionFalse(func, eventName):
    id  = cmds.scriptJob(cf=[eventName, func], protected=True)
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


def _removeScriptJob(id):
    if cmds.scriptJob(exists=id):
        cmds.scriptJob(kill=id, force=True)
        #print("Removed script job for: %s" % id)
    else:
        #print("No existing script job in place for: %s" % id)
        pass


def addTimeChangeCallback(func, callbackEvent=TIME_CHANGED_EVENT_NAME,
                          scriptJobEvent=PLAYING_BACK_EVENT_NAME):
    """
    Given a function/method, this function will setup the callback so
    that function/method is called whenever the selected/active frame
    changes. This function will return the ID for that callback so it
    can be later removed when needed.

    If the callback function does nothing during playback, which can
    be detected in that callback function using:
        currentlyPlayingBack = cmds.play(q=True,state=True)
    then that function should be called once at the end of playback.

    By default, this function will register a script job to execute
    the callback function once at the end of playback. To disable
    that behavior, simply pass in None for 'scriptJobEvent' when
    calling this function.
    """
    callbackId = _addCallback(func, callbackEvent, _timeChangeCallback)
    if scriptJobEvent:
        scriptJobId = _addScriptJobConditionFalse(func, scriptJobEvent)
    else:
        scriptJobId = None
    _timeChangeCallbackToScriptJobMapping[callbackId] = scriptJobId
    return callbackId


def removeTimeChangeCallback(callbackId):
    _removeCallback(callbackId, _timeChangeCallback)
    try:
        scriptJobId = _timeChangeCallbackToScriptJobMapping[callbackId]
    except KeyError:
        scriptJobId = None
    if scriptJobId is not None:
        _removeScriptJob(scriptJobId)


def addRangeChangeCallback(func, eventName=RANGE_CHANGED_EVENT_NAME):
    return _addCallback(func, eventName, _rangeChangeCallback)


def removeRangeChangeCallback(id):
    return _removeCallback(id, _rangeChangeCallback)


def showCurrentTime(arg=None):
    currentTime = cmds.currentTime(query=True)
    print("Current time = %s and input argument = %s" % (currentTime, arg))


def test():
    addTimeChangeCallback(showCurrentTime)


