#!/bin/bash
#   WRW 24-May-2025 - presently incomplete, 
#       do_*.py requires command-line options for confdir and userdatadir.

export PYTHONPATH=../../src
for x in *
do
    if [[ -d $x ]]
    then
    (
        echo $x
        cd $x
        do_*.py
    )
    fi
done
