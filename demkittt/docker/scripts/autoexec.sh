#!/bin/sh
file="/apps/workspace/autoexec.sh"
if [ -f "$file" ]
then
	sh /apps/workspace/autoexec.sh
else
	cd /app/demkit
	# First run commands
	# sh scripts/update.sh
	# sh scripts/obtainexample.sh
	
	# sh scripts/setupalpg.sh
	
	#optionally update the code first
	# git pull
	
	python3 demkit.py -f ${DEMKIT_FOLDER} -m ${DEMKIT_MODEL} 
fi
