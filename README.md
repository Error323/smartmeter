Smart meter logger
------------------

A smart meter logger for the dutch smart meters with a P1 (RJ11) port. In this
case a Landys+Gir E350, but it should work for other types with this port. The
device is connected via RJ11 -> USB to a Raspberry Pi.

### Usage ###

    usage: p1-reader.py [-h] [--input INPUT] [--output OUTPUT] [--kwh1 KWH1]
                        [--kwh2 KWH2] [--gas GAS] [--port PORT]
                        [--logfile LOGFILE] [--loglvl LOGLVL]

    optional arguments:
      -h, --help         show this help message and exit
      --input INPUT      Read data from file, for testing
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

    A B C D

where `A` is the current power usage in Watt, `B` the current gas usage in m3,
`C` the cost of power per month and `D` the cost of gas per month.  This file
is interpreted by munin, see `munin/` for the plugins.
