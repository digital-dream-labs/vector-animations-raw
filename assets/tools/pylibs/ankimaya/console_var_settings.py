
# The doUpdateFace() function in preview_selector.py will read CONSOLE_FUNCTIONS
# list from here and execute those console functions on the robot. It will also
# read the CONSOLE_VAR_VALUES dictionary from here and set those console
# variable/values on the robot. See VIC-1445 for additional details.

CONSOLE_FUNCTIONS = [ "ProcFace_Saturation&args=1" ]

CONSOLE_VAR_VALUES = { "ProcFace_NoiseNumFrames" : "5",
					   "ProcFace_HotspotFalloff" : "0.5",
					   "ProcFace_NoiseMinLightness" : "0.96",
					   "ProcFace_NoiseMaxLightness" : "1.14",
					   "ProcFace_Hue" : "0.43",
					    }