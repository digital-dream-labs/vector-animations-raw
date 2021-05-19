
export BASH_SCRIPTS_DIR=${ANKI_TOOLS}/robot_scripts

# The following environment variables were setup to match some of the aliases from
# https://github.com/anki/victor/blob/master/project/victor/scripts/usefulALiases.sh
# (from mid-February, shortly BEFORE we switched to DVT2/LE robots)

export VICTOR_RESTART='${BASH_SCRIPTS_DIR}/systemctl.sh restart anki-robot.target'

export VICTOR_START='${BASH_SCRIPTS_DIR}/systemctl.sh start anki-robot.target'

export VICTOR_STOP='${BASH_SCRIPTS_DIR}/systemctl.sh stop anki-robot.target'

export VICTOR_DEPLOY='${BASH_SCRIPTS_DIR}/deploy.sh -c Release'

export VICTOR_ASSETS='${BASH_SCRIPTS_DIR}/deploy-assets.sh ${ASSETS_DIR}'

export VICTOR_ASSETS_FORCE='${BASH_SCRIPTS_DIR}/deploy-assets.sh -f ${ASSETS_DIR}'

export VICTOR_REMOUNT_FS='${BASH_SCRIPTS_DIR}/remount-fs.sh'

