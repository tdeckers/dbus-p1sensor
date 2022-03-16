#!/bin/bash
#
# Start script for dbus-p1sensor
#   First parameter: ip address for MQTT server
#
# Keep this script running with daemon tools. If it exits because the
# connection crashes, or whatever, daemon tools will start a new one.
#

MQTT_SERVER=192.168.2.37
/usr/bin/python /opt/victronenergy/dbus-p1sensor/dbus-p1sensor.py ${MQTT_SERVER}