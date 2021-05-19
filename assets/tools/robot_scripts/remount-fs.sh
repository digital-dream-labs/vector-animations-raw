#!/bin/bash

set -e
set -u

# Go to directory of this script                                                                    
SCRIPT_PATH=$(dirname $([ -L $0 ] && echo "$(dirname $0)/$(readlink -n $0)" || echo $0))            
cd "${SCRIPT_PATH}"

# source env & helper functions
source victor_env.sh

robot_sh /bin/mount -o remount,rw /

