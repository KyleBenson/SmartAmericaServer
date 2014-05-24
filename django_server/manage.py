#!/usr/bin/env python
import os
import sys

dime_running = False
if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "scale.settings")

    # subscribe to sensed data and events
    #TODO: ensure this only runs once and maybe remove the --noreload option from run.sh
    if not dime_running:
        dime_running = True
        from scale import DimeDriver
        DimeDriver.subscribe("iot-1/d/+/evt/+/json")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
