#!/bin/env bash
N=$1
HEADER_LINES=3
if [[ -z $N ]]; then
	N=${HEADER_LINES}
else
	N=$(command echo "${HEADER_LINES}+${N}" | bc)
fi

sqlite3 smarthome.db \
	"SELECT * FROM eventdata \
	ORDER BY EventdataTime DESC;"\
	| awk -F '|' 'BEGIN { count = 1; format="%5s | %-19s | %-2s | %-15s | %-8s | %-20s\n"; \
	print "--------------------------------------------------------------------------------";\
	printf format, "#", "Time", "ID", "Location", "Priority", "Info";\
	print "--------------------------------------------------------------------------------"};\
	{ printf "%5s | %-19s | %-2s | %-15s | %-8s | %-20s\n", count, $1, $2, $3, $4, $5; count+=1;}\
	END { print "--------------------------------------------------------------------------------" }'\
	| if [[ $N -gt $HEADER_LINES ]]; then\
		head -n ${N}
	else
		cat
	fi
