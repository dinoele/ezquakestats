#!/bin/bash

helpFunction()
{
   echo ""
   echo "Usage: $0 [-s] [-c]"
   echo -e "\t-s Server is started"
   echo -e "\t-c Network copy is enabled"
   exit 1 # Exit script after printing help
}

isServer=false
isNetCopy=false
while getopts "sc" opt
do
   case "$opt" in
      s ) isServer=true ;;
      c ) isNetCopy=true ;;
      ? ) helpFunction ;; # Print helpFunction in case parameter is non-existent
   esac
done

if [ "$isServer" = true ] ; then
    cd /cygdrive/c/nQuakesv   # <---- TOCHANGE
    ./mvdsv.exe -game ktx +logrcon +logplayers +fraglogfile 1 +map messy +exec port2.cfg
fi

cd /cygdrive/d/tmp/qstats   # <---- TOCHANGE

if [ "$isNetCopy" = false ] ; then
    python getstats_launch.py
fi
if [ "$isNetCopy" = true ] ; then
    python getstats_launch.py --net-copy
fi