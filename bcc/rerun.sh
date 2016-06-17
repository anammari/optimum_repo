#!/bin/bash
#make-run.sh
#make sure a process is always running.

export DISPLAY=:0 #needed if you are running a simple gui app.

process='test.py'
makerun="/usr/local/Cellar/python/2.7.11/bin/python /Users/ahmadammari/Dropbox/Work/Optimum/bcc/test.py"


if ps ax | grep -v grep | grep $process > /dev/null
then
    echo 'exist'
    exit
else
    echo 'process is not running, starting it again' 
    $makerun &
fi

exit


if [ `flock -xn '/usr/local/Cellar/python/2.7.11/bin/python test.py' -c 'echo 1'` ]; then 
   echo 'its not running'
else
   echo -n 'its already running with PID '
   #cat /tmp/script.lock
fi
