#
# This file is intended to be included in other scripts that require the ANDROID_SDK or ADB
#

#
# SSH/SCP support
#

: ${ANKI_ROBOT_USER:="root"}

robot_set_host ()
{
    if [ -z ${ANKI_ROBOT_HOST+x} ]; then
        GIT_PROJ_ROOT=`git rev-parse --show-toplevel`
        ROBOT_IP_FILE="${GIT_PROJ_ROOT}/tools/victor-ble-cli/robot_ip.txt"
        if [ ! -f $ROBOT_IP_FILE ]; then
            echo "ERROR: Missing file $ROBOT_IP_FILE"
            echo "You can create this file manually or run tools/victor-ble-cli/vic_set_robot_key.sh <robotName>"
            echo "The file just needs to contain the robot's IP address"
            exit
        fi
        ANKI_ROBOT_HOST=$(cat $ROBOT_IP_FILE)
    fi
}

robot_sh ()
{
    if [ -z ${ANKI_ROBOT_HOST} ]; then
        echo "ERROR: Unspecified robot host."
        return 1
    fi
    ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no ${ANKI_ROBOT_USER}@${ANKI_ROBOT_HOST} timeout -t 30 $*
}

robot_cp ()
{
    if [ -z ${ANKI_ROBOT_HOST} ]; then
        echo "ERROR: Unspecified robot host"
        return 1
    fi

    if [ $# -eq 3 ]; then
        ARGS="$1"
        shift
    else
        ARGS=""
    fi

    SRC="$1"
    DST=$ANKI_ROBOT_USER@$ANKI_ROBOT_HOST:"$2"

    scp -o ConnectTimeout=10 ${ARGS} ${SRC} ${DST}
}

robot_cp_from ()
{
    if [ -z ${ANKI_ROBOT_HOST} ]; then
        echo "ERROR: Unspecified robot host"
        return 1
    fi

    if [ $# -eq 3 ]; then
        ARGS="$1"
        shift
    else
        ARGS=""
    fi

    SRC=$ANKI_ROBOT_USER@$ANKI_ROBOT_HOST:"$1"
    DST="$2"

    scp -o ConnectTimeout=10 ${ARGS} ${SRC} ${DST}
}

ADB=adb                                                                                             
#echo "ADB: $ADB"

function adb_shell {
    CMD='$ADB'
    CMD+=" shell '"
    CMD+="$1; echo "
    CMD+='$?'
    CMD+=" | tr -d [:space:]"
    CMD+="'"

    # uncomment for debugging
    # set -x
    RC=$(eval $CMD)
    # set +x
    # echo "RC = $RC"

    [[ $RC == "0" ]]
}

