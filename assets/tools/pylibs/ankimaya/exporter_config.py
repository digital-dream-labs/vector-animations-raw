
# TODO: Add brief explanation to the version strings that are displayed to animators in the UI.
#       Those explanations should be:
#           v1 = inaccurate lift & straight mvmts
#           v2 = whl mvmt turns wrong way
#           v3 = round turn under 0.5 check


from maya import cmds


EXPORTER_STRUCT_NAME = "ExporterStruct"
EXPORTER_STREAM_NAME = "ExporterStream"
EXPORTER_VERSION_MEMBER_NAME = "exporterVersion"
EXPORTER_VERSION_CHANNEL_NAME = "version"

CLAMP_BODY_MOTION = "clamp_body_motion"
ADJUST_LIFT_HEIGHT = "adjust_lift_height"
TURN_WRONG_DIRECTION = "turn_wrong_direction"
ROUND_TURN_UNDER_POINT_FIVE = "round_turn_under_point_five"
USE_DISTANCE_FOR_SPEED = "use_distance_for_speed"

LATEST_VERSION = 0
LATEST_VERSION_DISP_STRING = "latest"
DEFAULT_VERSION = LATEST_VERSION

# This dictionary maps the internal exporter version number to the setting that should be used for
# that version. Version 0 will always be the latest and the default version. When that version needs
# to be frozen/locked so a backwards-incompatible change can be made to the latest/default version,
# we should:
#  (1) copy the version 0 settings to the next version, eg. copy the version 0 settings to a new
#      version 3 if we already have versions 1 and 2 in place
#  (2) tag all existing Maya scenes that aren't already locked on a non-zero version with this new
#      version number, eg. tag all Maya scenes that are not tagged with any particular version (or
#      tagged as version 0) as version 3, ignoring all Maya scenes that are tagged as version 1 or 2

EXPORTER_CONFIG = { LATEST_VERSION : { CLAMP_BODY_MOTION : True,
                                       ADJUST_LIFT_HEIGHT : False,
                                       TURN_WRONG_DIRECTION : False,
                                       ROUND_TURN_UNDER_POINT_FIVE: False,
                                       USE_DISTANCE_FOR_SPEED : False } ,
                    3: {CLAMP_BODY_MOTION: True,
                        ADJUST_LIFT_HEIGHT: False,
                        TURN_WRONG_DIRECTION: False,
                        ROUND_TURN_UNDER_POINT_FIVE: True,
                        USE_DISTANCE_FOR_SPEED: False},
                    2 : { CLAMP_BODY_MOTION : True,
                          ADJUST_LIFT_HEIGHT : False,
                          TURN_WRONG_DIRECTION : True,
                          ROUND_TURN_UNDER_POINT_FIVE: True,
                          USE_DISTANCE_FOR_SPEED : False } ,
                    1 : { CLAMP_BODY_MOTION : False,
                          ADJUST_LIFT_HEIGHT : True,
                          TURN_WRONG_DIRECTION : True,
                          ROUND_TURN_UNDER_POINT_FIVE: True,
                          USE_DISTANCE_FOR_SPEED : True } }

VERSION_DISPLAY_PREFIX = 'v'


def get_clamp_body_motion():
    """
    Should body motion be clamped to not exceed physical
    limitations of the robot?  (default is True)
    """
    try:
        return _check_bool_setting(CLAMP_BODY_MOTION)
    except KeyError:
        return True

def get_adjust_lift_height():
    """
    Should the lift height be adjusted for backwards
    compatibility?  (default is False)
    """
    try:
        return _check_bool_setting(ADJUST_LIFT_HEIGHT)
    except KeyError:
        return False

def get_turn_wrong_direction():
    """
    Should the robot turn in the wrong direction when using
    wheel movements?  (default is False)
    """
    try:
        return _check_bool_setting(TURN_WRONG_DIRECTION)
    except KeyError:
        return False

def get_use_distance_for_speed():
    """
    Should the distance be stored for the speed attribute
    for backwards compatibility?  (default is False)
    """
    try:
        return _check_bool_setting(USE_DISTANCE_FOR_SPEED)
    except KeyError:
        return False

def get_round_turn_under_point_five():
    """
    Should the radius of less than 0.5 be rounded to turn in place?  (default is False)
    """
    try:
        return _check_bool_setting(ROUND_TURN_UNDER_POINT_FIVE)
    except KeyError:
        return False

def _check_bool_setting(setting, exporter_config=None):
    if exporter_config is None:
        exporter_config = EXPORTER_CONFIG
    else:
        exporter_config = exporter_config
    try:
        exporter_version = getExporterVersion()
        this_config = exporter_config[exporter_version]
    except (KeyError, RuntimeError):
        this_config = exporter_config[DEFAULT_VERSION]
    return this_config[setting]


def getExporterVersion(structName=EXPORTER_STRUCT_NAME):
    """
    Get the current setting for the exporter version that should be used.
    """
    exporterVersion = None
    dataStructs = cmds.dataStructure(query=True)
    if structName in dataStructs:
        exporterVersion = cmds.getMetadata(index=0, streamName=EXPORTER_STREAM_NAME,
                                         memberName=EXPORTER_VERSION_MEMBER_NAME,
                                         channelName=EXPORTER_VERSION_CHANNEL_NAME, scene=True)
        if isinstance(exporterVersion, list):
            exporterVersion = exporterVersion[0]
        exporterVersion = int(exporterVersion)
    return exporterVersion


def setExporterVersion(value, structName=EXPORTER_STRUCT_NAME):
    structDesc = "name=%s:int32=%s" % (structName, EXPORTER_VERSION_MEMBER_NAME)
    dataStructs = cmds.dataStructure(query=True)
    if structName in dataStructs:
        existingStruct = cmds.dataStructure(name=structName, format="raw", query=True, asString=True)
        if structDesc != existingStruct:
            cmds.warning("Removing data structure for '%s' since the existing structure does not "
                         "match the expected format" % structName)
            cmds.dataStructure(remove=True, name=structName)
            dataStructs = cmds.dataStructure(query=True)
    if structName not in dataStructs:
        print("Creating data structure to store the exporter version to use")
        cmds.dataStructure(format="raw", asString=structDesc)
        cmds.addMetadata(streamName=EXPORTER_STREAM_NAME, structure=structName,
                         channelName=EXPORTER_VERSION_CHANNEL_NAME, scene=True)
    print("Setting exporter version to be %s" % value)
    cmds.editMetadata(index=0, streamName=EXPORTER_STREAM_NAME, memberName=EXPORTER_VERSION_MEMBER_NAME,
                      value=value, scene=True)


class ExporterConfig(object):

    no_specific_version = [None, "None"]

    def __init__(self, exporter_config=None, default_version=DEFAULT_VERSION,
                 version_display_prefix=VERSION_DISPLAY_PREFIX):
        if exporter_config is None:
            self.exporter_config = EXPORTER_CONFIG
        else:
            self.exporter_config = exporter_config
        self.default_version = default_version
        self.version_display_prefix = version_display_prefix

    def get_display_string(self, version_num):
        try:
            version_num = int(version_num)
        except (TypeError, ValueError):
            version_num = self.default_version
        if version_num == LATEST_VERSION:
            disp_string = LATEST_VERSION_DISP_STRING
        else:
            disp_string = "%s%s" % (self.version_display_prefix, version_num)
        return disp_string

    def get_all_display_strings(self):
        display_strings = []
        version_num_options = self.exporter_config.keys()
        version_num_options.sort()
        for version_num in version_num_options:
            display_strings.append(self.get_display_string(version_num))
        return display_strings

    def get_version_num_from_display(self, disp_string):
        if disp_string == LATEST_VERSION_DISP_STRING:
            return LATEST_VERSION
        elif disp_string in self.no_specific_version:
            return self.default_version
        version_str = disp_string.lstrip(self.version_display_prefix)
        try:
            version_num = int(version_str)
        except (TypeError, ValueError):
            version_num = self.default_version
        return version_num

    def get_info_from_display(self, disp_string):
        version_num = self.get_version_num_from_display(disp_string)
        return self.exporter_config[version_num]


