#!/usr/bin/env bash

output_dir=~/string_diffs_$$
temp_folder=~/workspace_live/
remote_path=https://daria@svn.ankicore.com/svn/victor-animation

rm -rf $temp_folder
mkdir $temp_folder;
cd $temp_folder;
svn checkout https://daria@svn.ankicore.com/svn/victor-animation/trunk;
mv -f ~/workspace_live/trunk ~/workspace_live/victor-animation
