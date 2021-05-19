#!/bin/bash

set -e
set -u

# Go to directory of this script
SCRIPT_PATH=$(dirname $([ -L $0 ] && echo "$(dirname $0)/$(readlink -n $0)" || echo $0))

function usage()
{
    SCRIPT_NAME=`basename $0`
    echo "${SCRIPT_NAME} [OPTIONS] <ASSETS_BUILD_DIR>"
    echo "  -h          print this message"
    echo "  -f          force-push assets to device"
    echo "  -x          remove all assets bundles from device"
    echo "${SCRIPT_NAME} with no arguments lists the available local assets"
}

#
# defaults
#
REMOVE_ALL_ASSETS=0
: ${INSTALL_ROOT:="/anki"}

while getopts ":hfx" opt; do
  case ${opt} in
    h )
      usage
      exit 1
      ;;
    f )
      REMOVE_ALL_ASSETS=1
      ;;
    \? )
      usage
      exit 1
      ;;
  esac
done

cd "${SCRIPT_PATH}"
shift $((OPTIND -1))

# Set asset directories
ASSETSDIR="${@: -1}" # last argument

# Check that the assets directory exists
if [ ! -d "$ASSETSDIR" ]; then
  echo "Assets directory ${ASSETSDIR} does not exist!"
  exit 1
fi

RSYNC_BIN_DIR=${SCRIPT_PATH}
: ${DEVTOOLS_INSTALL_ROOT:="/anki-devtools"}
: ${DEVICE_RSYNC_BIN_DIR:="${DEVTOOLS_INSTALL_ROOT}/bin"}
: ${DEVICE_RSYNC_CONF_DIR:="/run/systemd/system"}
DEVICE_ASSET_ROOT_DIR="${INSTALL_ROOT}/data/assets/cozmo_resources/assets"

# source env & helper functions
source victor_env.sh

# delete all old bundles from asset folder if REMOVE_ALL_ASSETS=1
if [ $REMOVE_ALL_ASSETS -eq 1 ]; then
  robot_sh rm -rf ${DEVICE_ASSET_ROOT_DIR}/*
fi

# Make sure we have the directories we expect
robot_sh mkdir -p ${DEVICE_RSYNC_BIN_DIR}
robot_sh mkdir -p ${DEVICE_RSYNC_CONF_DIR}
robot_sh mkdir -p ${DEVICE_ASSET_ROOT_DIR}

# install rsync binary and config if needed
set +e
robot_sh [ -f "$DEVICE_RSYNC_BIN_DIR/rsync.bin" ]
if [ $? -ne 0 ]; then
  echo "loading rsync to device"
  robot_cp ${RSYNC_BIN_DIR}/rsync.bin ${DEVICE_RSYNC_BIN_DIR}/rsync.bin
fi

echo "loading rsync config to device"
robot_cp ${RSYNC_BIN_DIR}/rsyncd.conf ${DEVICE_RSYNC_CONF_DIR}/rsyncd.conf

robot_sh [ -f "$DEVICE_RSYNC_CONF_DIR/rsyncd.service" ]
if [ $? -ne 0 ]; then
  echo "loading rsyncd.service to device"
  robot_cp ${RSYNC_BIN_DIR}/rsyncd.service ${DEVICE_RSYNC_CONF_DIR}/rsyncd.service
  robot_sh "/bin/systemctl daemon-reload"
fi
set -e

echo "deploying assets: ${ASSETSDIR}"

# startup rsync daemon
robot_sh "/bin/systemctl is-active rsyncd.service > /dev/null 2>&1 || /bin/systemctl start rsyncd.service"

# Install new assets
pushd ${ASSETSDIR} > /dev/null 2>&1

# Use --inplace to avoid consuming temp space & minimize number of writes
# Use --delete to purge files that are no longer present in build tree
RSYNC_ARGS="-rlptD -zvP --inplace --delete"
#RSYNC_ARGS="-rlptD -zvP --inplace --delete --delete-before --force"

if ! [ -z ${ANIM_DIRS+x} ]; then
    if ! [ -z ${ANIM_DIRS} ]; then
        IFS=':' read -r -a anim_dirs_array <<< "${ANIM_DIRS}"
        for anim_dir in "${anim_dirs_array[@]}"; do
            if [[ $anim_dir = *"/"* ]]; then
                IFS='/' read -r -a anim_dir_array <<< "${anim_dir}"
                anim_dir="${anim_dir_array[0]}"
            fi
            rsync $RSYNC_ARGS ./${anim_dir}/ rsync://${ANKI_ROBOT_HOST}:1873/resource_assets/${anim_dir}
        done
    fi
fi

popd > /dev/null 2>&1
echo "assets installed to $DEVICE_ASSET_ROOT_DIR"

#echo "Restarting processes"
#robot_sh systemctl restart anki-robot.target

