
export BASH_SCRIPTS_DIR=${ANKI_TOOLS}/robot_scripts

# The following environment variables were borrowed from the ~/.bash_profile
# recommendation in the "ADB setup" section of
# https://github.com/anki/victor/blob/master/README.md (from mid-February,
# shortly BEFORE we switched to DVT2/LE robots)

ANKI_ANDROID_ROOT=~/.anki/android
ANDROID_SDK_REPOSITORY=${ANKI_ANDROID_ROOT}/sdk-repository
export ANDROID_HOME=${ANDROID_SDK_REPOSITORY}/`/bin/ls $ANDROID_SDK_REPOSITORY/ | tail -1`
export ANDROID_ROOT=$ANDROID_HOME
export ANDROID_NDK_REPOSITORY=${ANKI_ANDROID_ROOT}/ndk-repository
export ANDROID_NDK_ROOT=${ANDROID_NDK_REPOSITORY}/`/bin/ls $ANDROID_NDK_REPOSITORY/ | tail -1`
export ANDROID_NDK_HOME=$ANDROID_NDK_ROOT
export ANDROID_NDK=$ANDROID_NDK_ROOT
export NDK_ROOT=$ANDROID_NDK_ROOT
export PATH=${PATH}:${ANDROID_HOME}/platform-tools  # for adb

# The following environment variables were setup to match some of the aliases from
# https://github.com/anki/victor/blob/master/project/victor/scripts/usefulALiases.sh
# (from mid-February, shortly BEFORE we switched to DVT2/LE robots)

export VICTOR_RESTART='${BASH_SCRIPTS_DIR}/systemctl.sh restart anki-robot.target'

export VICTOR_START='${BASH_SCRIPTS_DIR}/systemctl.sh start anki-robot.target'

export VICTOR_STOP='${BASH_SCRIPTS_DIR}/systemctl.sh stop anki-robot.target'

export VICTOR_DEPLOY='${BASH_SCRIPTS_DIR}/deploy.sh -c Release'

export VICTOR_ASSETS='${BASH_SCRIPTS_DIR}/deploy-assets.sh ${ASSETS_DIR}'

export VICTOR_ASSETS_FORCE='${BASH_SCRIPTS_DIR}/deploy-assets.sh -f ${ASSETS_DIR}'

