#!/bin/sh

docker run -it --rm --net=host --privileged \
    -v /var/run/dbus:/var/run/dbus \
    -e DBUS_SYSTEM_BUS_ADDRESS=unix:path=/var/run/dbus/system_bus_socket \
    ble-tui
