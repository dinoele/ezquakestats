#!/bin/bash

helpFunction()
{
   echo ""
   echo "Usage: $0 [-s] [-c]"
   echo -e "\t-s Server is started"
   echo -e "\t-c Network copy is enabled"
   exit 1 # Exit script after printing help
}

CONFIG_FILE="stat.conf"

if test -f ./$CONFIG_FILE; then
  . ./$CONFIG_FILE
else
  echo "ERROR: Config file is missing. Copy stat.conf.sample to stat.conf and set parameters."
  exit 1
fi

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
    cd $nquakesv_root  # TODO SERVER PATH
    ./mvdsv.exe -game ktx +logrcon +logplayers +fraglogfile 1 +map warfare2 +exec port22.cfg
fi

cd $scripts_root  # TODO QSTATS ROOT PATH

if [ "$isNetCopy" = false ] ; then
    python launch_getstats_team_XML.py
fi
if [ "$isNetCopy" = true ] ; then
    python launch_getstats_team_XML.py --net-copy
fi
