#!/usr/bin/bash
# -------------------------------------------------------------------------------
#   pack.linux.sh - Package a Linux onedir bundle for distribution.

#   Reminder: '-C $Dir' changes directory to $Dir before building
# -------------------------------------------------------------------------------

. src/fb_version.sh

Dir=~/Uploads/onedir

tar -C $Dir -czvf $Dir/birdland_qt-Linux-${AppVersionFull}.gz birdland_qt

cd $Dir
zip -r $Dir/birdland_qt-Linux-${AppVersionFull}.zip birdland_qt
