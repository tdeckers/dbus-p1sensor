#!/usr/bin/env python3

"""
A class to put a simple service on the dbus, according to victron standards, with constantly updating
paths. See example usage below. It is used to generate dummy data for other processes that rely on the
dbus. See files in dbus_vebus_to_pvinverter/test and dbus_vrm/test for other usage examples.
To change a value while testing, without stopping your dummy script and changing its initial value, write
to the dummy data via the dbus. See example.
https://github.com/victronenergy/dbus_vebus_to_pvinverter/tree/master/test
"""
from gi.repository import GLib
import platform
from argparse import ArgumentParser
import logging
import sys
import os

# our own packages
sys.path.insert(1, os.path.join(os.path.dirname(__file__), './ext/velib_python'))
sys.path.insert(1, os.path.join(os.path.dirname(__file__), '/opt/victronenergy/dbus-systemcalc-py/ext/velib_python'))

from vedbus import VeDbusService
from bridge import MqttGObjectBridge

VERSION = '0.1'

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class DbusP1Service(object):
    def __init__(self, servicename, deviceinstance, productname='P1 Bridge', connection='P1 service'):
        self.service = service = VeDbusService(servicename)

        logger.debug("%s /DeviceInstance = %d" % (servicename, deviceinstance))

        # Create the management objects, as specified in the ccgx dbus-api document
        service.add_path('/Mgmt/ProcessName', __file__)
        service.add_path('/Mgmt/ProcessVersion', VERSION + ' ' + platform.python_version())
        # TODO: change connection to MQTT host
        service.add_path('/Mgmt/Connection', connection)

        # Create the mandatory objects
        service.add_path('/DeviceInstance', deviceinstance)
        service.add_path('/ProductId', 0)
        service.add_path('/ProductName', productname)
        service.add_path('/FirmwareVersion', 0)
        service.add_path('/HardwareVersion', 0)
        service.add_path('/Connected', 1)
        service.add_path('/DeviceType', 71) # or try 340? or 345?

        _kwh = lambda p, v: (str(v) + 'KWh')
        _a = lambda p, v: (str(v) + 'A')
        _w = lambda p, v: (str(v) + 'W')
        _v = lambda p, v: (str(v) + 'V')        

        service.add_path('/Ac/Energy/Forward', None, gettextcallback=_kwh)
        service.add_path('/Ac/Energy/Reverse', None, gettextcallback=_kwh)
        service.add_path('/Ac/Power', None, gettextcallback=_w)        
        service.add_path('/Ac/L1/Current', None, gettextcallback=_a)
        # service.add_path('/Ac/L1/Energy/Forward', None, gettextcallback=_kwh)
        # service.add_path('/Ac/L1/Energy/Reverse', None, gettextcallback=_kwh)
        service.add_path('/Ac/L1/Power', None, gettextcallback=_w)
        service.add_path('/Ac/L1/Voltage', None, gettextcallback=_v)
        service.add_path('/Ac/L2/Current', None, gettextcallback=_a)
        # service.add_path('/Ac/L2/Energy/Forward', None, gettextcallback=_kwh)
        # service.add_path('/Ac/L2/Energy/Reverse', None, gettextcallback=_kwh)
        service.add_path('/Ac/L2/Power', None, gettextcallback=_w)
        service.add_path('/Ac/L2/Voltage', None, gettextcallback=_v)
        service.add_path('/Ac/L3/Current', None, gettextcallback=_a)
        # service.add_path('/Ac/L3/Energy/Forward', None, gettextcallback=_kwh)
        # service.add_path('/Ac/L3/Energy/Reverse', None, gettextcallback=_kwh)
        service.add_path('/Ac/L3/Power', None, gettextcallback=_w)
        service.add_path('/Ac/L3/Voltage', None, gettextcallback=_v)        

        # GLib.timeout_add(1000, self._update)
    def set_path(self, path, value):
        if self.service[path] != value:
            self.service[path] = value

    # def _update(self):
    #     with self._dbusservice as s:
    #         for path, settings in self._paths.items():
    #             if 'update' in settings:
    #                 update = settings['update']
    #                 if callable(update):
    #                     s[path] = update(path, s[path])
    #                 else:
    #                     s[path] += update
    #                 logger.debug("%s: %s" % (path, s[path]))
    #     return True

    def _handlechangedvalue(self, path, value):
        logger.debug("someone else updated %s to %s" % (path, value))
        return True # accept the change

class Bridge(MqttGObjectBridge):
    def __init__(self, host, p1_service, *args, **kwargs):
        super(Bridge, self).__init__(host, *args, **kwargs)
        self.host = host
        self.p1_service = p1_service

    def _on_message(self, client, userdata, msg):
        if msg.topic == 'dsmr/reading/electricity_currently_delivered':
            power = float(msg.payload) * 1000 # kW to W
            logger.debug("Power received: {}".format(power))
            self.p1_service.set_path('/Ac/Power', power)
        elif msg.topic == 'dsmr/reading/electricity_currently_returned':
            power = float(msg.payload) * -1000 # kW to W
            logger.debug("Power Returned: {}".format(power))
            self.p1_service.set_path('/Ac/Power', power)
        elif msg.topic == 'dsmr/day-consumption/electricity_merged':
            energy = float(msg.payload)
            logger.debug("Energy received: {}".format(energy))
            self.p1_service.set_path('/Ac/Energy/Forward', energy)
        elif msg.topic == 'dsmr/day-consumption/electricity_returned_merged':
            energy = float(msg.payload)
            logger.debug("Energy returned: {}".format(energy))
            self.p1_service.set_path('/Ac/Energy/Reverse', energy)

        elif msg.topic == 'dsmr/reading/phase_currently_delivered_l1':
            power = float(msg.payload) * 1000
            logger.debug("L1 Power received: {}".format(power))
            self.p1_service.set_path('/Ac/L1/Power', power)            
        elif msg.topic == 'dsmr/reading/phase_currently_returned_l1':
            power = float(msg.payload) * -1000
            logger.debug("L1 Power returned: {}".format(power))
            self.p1_service.set_path('/Ac/L1/Power', power)
        elif msg.topic == 'dsmr/reading/phase_power_current_l1':
            current = float(msg.payload)
            logger.debug("L1 Current: {}".format(current))
            self.p1_service.set_path('/Ac/L1/Current', current)
        elif msg.topic == 'dsmr/reading/phase_voltage_l1':
            voltage = float(msg.payload)
            logger.debug("L1 Voltage: {}".format(voltage))
            self.p1_service.set_path('/Ac/L1/Voltage', voltage)

        elif msg.topic == 'dsmr/reading/phase_currently_delivered_l2':
            power = float(msg.payload) * 1000
            logger.debug("L2 Power received: {}".format(power))
            self.p1_service.set_path('/Ac/L2/Power', power)            
        elif msg.topic == 'dsmr/reading/phase_currently_returned_l2':
            power = float(msg.payload) * -1000
            logger.debug("L2 Power returned: {}".format(power))
            self.p1_service.set_path('/Ac/L2/Power', power)
        elif msg.topic == 'dsmr/reading/phase_power_current_l2':
            current = float(msg.payload)
            logger.debug("L2 Current: {}".format(current))
            self.p1_service.set_path('/Ac/L2/Current', current)
        elif msg.topic == 'dsmr/reading/phase_voltage_l2':
            voltage = float(msg.payload)
            logger.debug("L2 Voltage: {}".format(voltage))
            self.p1_service.set_path('/Ac/L2/Voltage', voltage)

        elif msg.topic == 'dsmr/reading/phase_currently_delivered_l3':
            power = float(msg.payload) * 1000
            logger.debug("L3 Power received: {}".format(power))
            self.p1_service.set_path('/Ac/L3/Power', power)            
        elif msg.topic == 'dsmr/reading/phase_currently_returned_l3':
            power = float(msg.payload) * -1000
            logger.debug("L3 Power returned: {}".format(power))
            self.p1_service.set_path('/Ac/L3/Power', power)
        elif msg.topic == 'dsmr/reading/phase_power_current_l3':
            current = float(msg.payload)
            logger.debug("L3 Current: {}".format(current))
            self.p1_service.set_path('/Ac/L3/Current', current)
        elif msg.topic == 'dsmr/reading/phase_voltage_l3':
            voltage = float(msg.payload)
            logger.debug("L3 Voltage: {}".format(voltage))
            self.p1_service.set_path('/Ac/L3/Voltage', voltage)            

    def _on_connect(self, client, userdata, di, rc):
        self._client.subscribe('dsmr/#', 0)
        # self._client.subscribe('servicelocation/+/channelConfig', 0)

def main():
    parser = ArgumentParser(description=sys.argv[0])
    parser.add_argument('host', help='MQTT Host')
    args = parser.parse_args()

    from dbus.mainloop.glib import DBusGMainLoop
    # Have a mainloop, so we can send/receive asynchronous calls to and from dbus
    DBusGMainLoop(set_as_default=True)

    p1_service = DbusP1Service(
        servicename='com.victronenergy.grid.dsmr',
        deviceinstance=0
        )    

    # MQTT connection
    bridge = Bridge(args.host, p1_service)

    logger.info('Connected to dbus, and switching over to GLib.MainLoop() (= event based)')
    mainloop = GLib.MainLoop()
    mainloop.run()    

if __name__ == "__main__":
    main()