Smart meter logger
------------------
A smart meter logger for the dutch smart meters with a P1 (RJ11) port. In this
case a Landys+Gir E350, but it should work for other types with this port. The
device is connected via RJ11 -> USB to a Raspberry Pi.

### Usage ###

    usage: smartmeter.py [-h] [--data DATA] [--output OUTPUT] [--kwh1 KWH1]
                         [--kwh2 KWH2] [--gas GAS] [--port PORT]
                         [--logfile LOGFILE] [--loglvl LOGLVL]
    
    optional arguments:
      -h, --help         show this help message and exit
      --data DATA        Read data from file, for testing
      --output OUTPUT    File to write output to
      --kwh1 KWH1        Price of a kWh at low tariff
      --kwh2 KWH2        Price of a kWh at high tariff
      --gas GAS          Price of a cubic meter of gas (m3)
      --port PORT        Serial port to read from
      --logfile LOGFILE  File to log output to
      --loglvl LOGLVL    Set the loglevel in {DEBUG, INFO, WARNING, ERROR,
                         CRITICAL}

### Program Output ###
The program writes averaged data from the device to file `/tmp/energy.dat`
every 5 min consisting of the following:

    A B C D E

where `A` is the current power usage in Watt, `B` is the current power returned
in Watt, `C` the current gas usage in m3, `D` the cost of power per month and
`E` the cost of gas per month.  This file is interpreted by munin, see `munin/`
for the plugins.

### Hardware ###
As stated, the smart meters uses a RJ11 port (P1) which needs to be connected
to the serial input (Sub-D) of a serial-to-usb converter. This requires some
soldering of the datacables, the schema is shown in the following table:

| RJ11 | Sub-D | Signal |
|------|-------|--------|
| 1    | -     | -      |
| 2    | 4     | RTS    |
| 3    | 5     | GND    |
| 4    | -     | -      |
| 5    | 2     | RxD    |
| 6    | -     | -      |

Where the pin numbers of both RJ11 and Sub-D are counted from left to right
when facing the front of the connector.
