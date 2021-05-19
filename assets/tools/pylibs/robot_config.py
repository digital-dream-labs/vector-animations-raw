
# Many of these constants were taken from robot/include/anki/cozmo/shared/cozmoConfig.h
# TODO: Is there any good way to read/parse that file so we don't have to redefine constants here?

LIFT_HEIGHT_MIN_ROBOT_MM = 32.0  # aka "LIFT_HEIGHT_LOWDOCK"
LIFT_HEIGHT_MAX_ROBOT_MM = 92.0  # aka "LIFT_HEIGHT_CARRY"

MAX_WHEEL_SPEED_MMPS = 220
MAX_BODY_ROTATION_SPEED_DEG_PER_SEC = 300

WHEEL_DIAMETER_MM = 29.0
WHEEL_DIST_MM = 46.0  # approx distance b/w the center of the front treads

# As described in COZMO-10889, BodyMotionKeyFrame's radius and speed parameters are internally read
# as float and then cast to int16, so those values should fall in the range between -32768 and 32767.
# We could get these min/max values from numpy.iinfo(numpy.int16).min and numpy.iinfo(numpy.int16).max
# respectively, but that would introduce a dependency on numpy.
MIN_RADIUS_MM = -32768
MAX_RADIUS_MM =  32767

BATTERY_VOLTAGE_LABEL = "Robot battery voltage:"
BATTERY_VOLTAGE_LOW_THRESHOLD = 3.50

def check_robot_battery(voltage, threshold=BATTERY_VOLTAGE_LOW_THRESHOLD,
                        label=BATTERY_VOLTAGE_LABEL):
    if voltage < threshold:
        print(label + str(voltage))

