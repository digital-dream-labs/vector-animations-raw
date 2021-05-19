#!/bin/bash

set -e
set -u

# Go to directory of this script
SCRIPT_PATH=$(dirname $([ -L $0 ] && echo "$(dirname $0)/$(readlink -n $0)" || echo $0))
SCRIPT_NAME=$(basename ${0})

source ${SCRIPT_PATH}/android_env.sh
export -f adb_shell

# Settings can be overridden through environment
: ${VERBOSE:=0}
: ${ANKI_BUILD_TYPE:="Debug"}
: ${INSTALL_ROOT:="/anki"}

: ${DEVICE_RSYNC_BIN_DIR:="/tmp"}
: ${DEVICE_RSYNC_CONF_DIR:="/data/rsync"}

# increment the following value if the contents of rsyncd.conf change
RSYNCD_CONF_VERSION=2

function usage() {
  echo "$SCRIPT_NAME [OPTIONS]"
  echo "  -h                      print this message"
  echo "  -v                      print verbose output"
  echo "  -c [CONFIGURATION]      build configuration {Debug,Release}"
}

while getopts "hvc:" opt; do
  case $opt in
    h)
      usage && exit 0
      ;;
    v)
      VERBOSE=1
      ;;
    c)
      ANKI_BUILD_TYPE="${OPTARG}"
      ;;
    *)
      usage && exit 1
      ;;
  esac
done

# echo "VERBOSE: ${VERBOSE}"
# echo "ANKI_BUILD_TYPE: ${ANKI_BUILD_TYPE}"
echo "INSTALL_ROOT: ${INSTALL_ROOT}"

: ${LIB_INSTALL_PATH:="${INSTALL_ROOT}/lib"}
: ${BIN_INSTALL_PATH:="${INSTALL_ROOT}/bin"}
: ${RSYNC_BIN_DIR="${BASH_SCRIPTS_DIR}"}

$ADB shell mkdir -p "${INSTALL_ROOT}"
$ADB shell mkdir -p "${INSTALL_ROOT}/etc"
$ADB shell mkdir -p "${LIB_INSTALL_PATH}"
$ADB shell mkdir -p "${BIN_INSTALL_PATH}"

# get device IP Address
DEVICE_IP_ADDRESS=`$ADB shell ip addr show wlan0 | grep "inet\s" | awk '{print $2}' | awk -F'/' '{print $1}'`
if [ -z $DEVICE_IP_ADDRESS ]; then
  DEVICE_IP_ADDRESS=`$ADB shell ip addr show lo | grep "inet\s" | awk '{print $2}' | awk -F'/' '{print $1}'`
  if [ -z $DEVICE_IP_ADDRESS ]; then
    echo "no valid android device found"
    exit 1
  fi

  DEVICE_IP_ADDRESS="$DEVICE_IP_ADDRESS:6010"
  $ADB forward tcp:6010 tcp:1873
else
  DEVICE_IP_ADDRESS="$DEVICE_IP_ADDRESS:1873"
fi

# install rsync binary and config if needed
set +e
adb_shell "[ -f "$DEVICE_RSYNC_BIN_DIR/rsync.bin" ]"
if [ $? -ne 0 ]; then
  echo "loading rsync to device"
  $ADB push ${RSYNC_BIN_DIR}/rsync.bin ${DEVICE_RSYNC_BIN_DIR}/rsync.bin
fi

RSYNCD_CONF="rsyncd-v${RSYNCD_CONF_VERSION}.conf"

adb_shell "[ -f "$DEVICE_RSYNC_CONF_DIR/$RSYNCD_CONF" ]"
if [ $? -ne 0 ]; then
  echo "loading rsync config to device"
  $ADB push ${RSYNC_BIN_DIR}/rsyncd.conf ${DEVICE_RSYNC_CONF_DIR}/$RSYNCD_CONF
fi
set -e

# startup rsync daemon
$ADB shell "${DEVICE_RSYNC_BIN_DIR}/rsync.bin --daemon --config=${DEVICE_RSYNC_CONF_DIR}/${RSYNCD_CONF}"

rsync -rv --include="*.so" --exclude="*" --delete ${BUILD_ROOT}/lib/ rsync://${DEVICE_IP_ADDRESS}/anki_root/lib/
rsync -rv --exclude="*.full" --delete ${BUILD_ROOT}/bin/ rsync://${DEVICE_IP_ADDRESS}/anki_root/bin/
rsync -rv --delete ${BASH_SCRIPTS_DIR}/runtime/ rsync://${DEVICE_IP_ADDRESS}/anki_root/etc/

# all executable binaries need to have executable file permissions
$ADB shell chmod a+x ${BIN_INSTALL_PATH}/*

#
# Put a link in /data/appinit.sh for automatic startup
#
$ADB shell ln -sf ${INSTALL_ROOT}/etc/appinit.sh /data/appinit.sh

#####################################################
#
# The following is the new way of rsync'ing... create a list of files and then rsync all of those in one shot.
#
#pushd ${BUILD_ROOT} > /dev/null 2>&1

# Since invoking rsync multiple times is expensive.
# build an include file list so that we can run a single rsync command
#RSYNC_LIST="${BUILD_ROOT}/rsync.$$.lst"
#touch ${RSYNC_LIST}

#find lib -type f -name '*.so' >> ${RSYNC_LIST}
#find bin -type f -not -name '*.full' >> ${RSYNC_LIST}
#find etc >> ${RSYNC_LIST}
#find data >> ${RSYNC_LIST}

#rsync -rlptD -uzvP --delete --files-from=${RSYNC_LIST} ./ rsync://${DEVICE_IP_ADDRESS}/anki_root/

#rm -f ${BUILD_ROOT}/rsync.*.lst

#popd > /dev/null 2>&1

