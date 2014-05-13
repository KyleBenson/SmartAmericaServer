#!/bin/bash
# Don't forget to `cf login` first!
# Also don't forget to do setup_db.sh the first time you push the app!

APP_NAME=testenvsmartamerica
BUILDPACK=https://github.com/joshuamckenty/heroku-buildpack-python
RUN_CMD=./run.sh

cf push -b $BUILDPACK -c "$RUN_CMD" $APP_NAME