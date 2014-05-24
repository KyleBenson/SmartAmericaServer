#!/bin/bash
DB_NAME=scale_db
dropdb $DB_NAME
createdb $DB_NAME
./setup_db.sh
