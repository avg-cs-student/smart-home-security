#!/bin/env sh

if [ ! -z ${SMARTHOMEPATH} ]; then
	sqlite3 ${SMARTHOMEPATH}/smarthome.db ".backup '${SMARTHOMEPATH}/smarthome.db.bak'"
fi
