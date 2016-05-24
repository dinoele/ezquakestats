#!/bin/bash
let num=1
if [ $# -eq 1 ]
  then
    num=$1
fi

if [ $num -gt 0 ]
    then
        let flag=1
        while [ $flag -eq 1 ]
        do
            echo "num="$num
            wget <link_to_team_ezquake_log> -O - | tac | grep begun -m $num -A 1 -B 10000 | tac | python getstats.py --net-log
            if [[ $? -eq 0 || $? -eq 2 || $num -gt 100 ]]
                then
                    let flag=0
            fi
            let num=$num+1
        done
fi