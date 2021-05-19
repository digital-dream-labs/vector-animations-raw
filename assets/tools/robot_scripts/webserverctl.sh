#!/bin/bash

set -e
set -u

: ${INSTALL_ROOT:="/data/data/com.anki.cozmoengine"}

# Go to directory of this script                                                                    
SCRIPT_PATH=$(dirname $([ -L $0 ] && echo "$(dirname $0)/$(readlink -n $0)" || echo $0))

source ${SCRIPT_PATH}/android_env.sh

$ADB shell "${INSTALL_ROOT}/webserverctl.sh $*"
