#!/usr/bin/bash
# --------------------------------------------------------------------------------------------------
#   WRW 29-Mar-2025 - too much to remember, encpsulte in shell script
#   Rebuild resources as safety measure if I forget to do so before building a bundle
#   Only update version on build.linux.onedir.sh

(
    cd src
    pyside6-rcc bl_resources.qrc -o bl_resources_rc.py
)

time pyinstaller pyi.linux.onefile.spec \
        --clean \
        --noconfirm \
        --distpath ~/Uploads/onefile/ \
        --workpath ~/Uploads/onefile/build

# --------------------------------------------------------------------------------------------------
