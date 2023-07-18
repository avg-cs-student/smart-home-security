#!/bin/env bash

DATABASE_NAME='smarthome.db'
export SMARTHOMEPATH=$(pwd)

if [[ "$EUID" -ne 0 ]]; then
	echo "To enable backups, run this script as root OR ensure that"
	echo "'smarthome-db-backup.sh' is placed in '/etc/cron.daily/' prior"
	echo -e "to starting the server.\n"
elif [[ ! -f '/etc/cron.daily/smarthome-db-backup.sh' ]]; then
	cp -v "${SMARTHOMEPATH}/smarthome-db-backup.sh" "/etc/cron.daily"
fi

echo "Initializing database..."

if [[ -f "$DATABASE_NAME" ]]; then
	echo "A database with the name ${DATABASE_NAME} already exists"
else
	sqlite3 ${DATABASE_NAME} < initdb.sql
fi

echo "Starting server..."
if [[ "$EUID" -ne 0 ]]; then
	./main.py
else
	sudo -u $(logname) ./main.py
fi
