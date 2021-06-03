#!/bin/bash
osascript -e 'on run argv' -e 'tell app "Terminal"
	set dir to (system attribute "HOME") & "/workspace/victor-animation/tools/other"
	do script "cd " & dir
	activate
	delay 0.5
	do script "./mac-client -f " & item 1 of argv in window 1
end tell' -e 'end run' $1