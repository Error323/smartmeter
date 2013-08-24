Smart meter logger
------------------

A smart meter logger for the dutch smart meters with a P1 (RJ11) port. In this
case a Landys+Gir E350, but it should work for other types with this port. The
device is connected via RJ11 -> USB to a Raspberry Pi.

### Usage ###

    usage: p1-reader.py [-h] [--input INPUT] [--output OUTPUT] [--verbose]
                        [--kwh1 KWH1] [--kwh2 KWH2] [--gas GAS] [--port PORT]
    
    Smart meter logger
    
    optional arguments:
      -h, --help       show this help message and exit
      --input INPUT    Read data from file, for testing
      --output OUTPUT  File to write output to
      --verbose        Print debug info to screen
      --kwh1 KWH1      Price of a kWh at night tariff
      --kwh2 KWH2      Price of a kWh at day tariff
      --gas GAS        Price of a cubic meter of gas (m3)
      --port PORT      Serial port to read from

### Program Output ###
The program writes averaged data from the device to file every 5 min consisting
of the following:

    A B C D

where `A` is the current kw usage, `B` the accumulated gas used thusfar in m^3, `C`
the cost of power per month and `D` the cost of the accumulated gas thusfar.
This file is interpreted by munin which creates the graphs every 5 min.
