#!/bin/sh

mayapy=/Applications/Autodesk/maya2018/Maya.app/Contents/bin/mayapy

other_dir=`dirname $0`

export PYTHONPATH=$other_dir/../pylibs

exec $mayapy -c 'import ankimaya.set_exporter_version; ankimaya.set_exporter_version.main()' "$@"

