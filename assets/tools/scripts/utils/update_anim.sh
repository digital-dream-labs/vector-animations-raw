#!/bin/bash

verion_num="486"

branch_name="wip/daria/update_animation_v"
branch_name=$branch_name$verion_num
commit_message="updated animation to v"
commit_message=$commit_message$verion_num

cd ~/workspace_git/cozmo-one
git checkout master
git fetch
git merge origin/master
git checkout -b $branch_name
~/scripts/update_anim.py $verion_num


git add --all
git commit -m "$commit_message"
git push origin $branch_name
