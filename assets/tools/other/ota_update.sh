#!/bin/bash
osascript -e 'on run argv' -e 'tell app "Terminal"
	set dir to (system attribute "HOME") & "/workspace/victor-animation/tools/other"
	do script "cd " & dir
	activate
	delay 0.5
	do script "./mac-client -f " & item 1 of argv & " -p 2 --ota-update http://ota.global.anki-dev-services.com/vic/master-dev/lo8awreh23498sf/full/lkg.ota" in window 1
end tell' -e 'end run' $1