#!/bin/sh

mayapy=/Applications/Autodesk/maya2018/Maya.app/Contents/bin/mayapy

other_dir=`dirname $0`

export PYTHONPATH=$other_dir/../pylibs

exec $mayapy -c 'import ankimaya.rename_anim_data; ankimaya.rename_anim_data.main()' "$@"

