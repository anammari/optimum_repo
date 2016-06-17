#!/bin/bash
#make-run.sh
#make sure a process is always running.

export DISPLAY=:0 #needed if you are running a simple gui app.

process='Stream_UK_accounts.py'
makerun="/usr/local/lib/python2.7.11/bin/python /home/optimum/optimum_uk_accounts/twitter_streaming/Stream_UK_accounts.py"


if ps ax | grep -v grep | grep $process > /dev/null
then
    echo 'exist'
    exit
else
    echo 'process is not running, starting it again' 
    $makerun &
fi

exit


if [ `flock -xn '/usr/local/lib/python2.7.11/bin/python Stream_UK_accounts.py' -c 'echo 1'` ]; then 
   echo 'its not running'
else
   echo -n 'its already running with PID '
   #cat /tmp/script.lock
fi
