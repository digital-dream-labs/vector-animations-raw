#!/bin/bash

set -e
set -u

: ${INSTALL_ROOT:="/anki"}

# Go to directory of this script                                                                    
SCRIPT_PATH=$(dirname $([ -L $0 ] && echo "$(dirname $0)/$(readlink -n $0)" || echo $0))

source ${SCRIPT_PATH}/victor_env.sh

robot_sh "systemctl $*"
