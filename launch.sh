#!/bin/bash
if [ $# -eq 0 ]
  then
    wget <link_to_ezquake_log> -O - | tac | grep begun -m 1 -A 1 -B 10000 | tac | python getstats_deathmatch.py
  else
    wget <link_to_ezquake_log> -O - | tac | grep begun -m $1 -A 1 -B 10000 | tac | python getstats_deathmatch.py
fi
