# dbus-p1sensor

This is a driver for VenusOS devices.  The goal is to receive data from the Belgian (and other
european) P1 DSMR Smart grid meters.  The driver doesn't integrate directly with the P1 port, but
instead relies on the [DSMR reader](https://github.com/dsmrreader/dsmr-reader) project.

DSMR Reader receives data from the P1 port and forwards this data to an MQTT server.  This is where
the dbus-p1sensor listens for updates.

Context: this has been tested with a belgian smart meter and a Multiplus II GX.

## Installation

This is a typical driver for VenusOS.  A `scripts/deploy.sh` has been provided to copy the driver onto
the VenusOS.  For this to work:
* enable SSH on VenusOS
* Update MQTT_SERVER in `start-p1sensor.sh`.  This should point to the MQTT server used by DSMR Reader.  
  (Note: this might be different than the MQTT server on VenusOS)
* run `rc.local`

Once installed, make sure to configure AC input 1 as Grid in VenusOS System setup.

# TODO

[ ] Move MQTT_SERVER into VenusOS Settings
