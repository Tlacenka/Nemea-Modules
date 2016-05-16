# IP Activity - backend module ip_activity

## Description
This module scans traffic and stores IP activity to the dedicated bitmap.

## Interfaces
- Input: 1, UniRec flow
- Output: 0, bitmap file.

## Parameters
### Module specific parameters
- `-c/--config_file <name>`     Sets name/prefix for configuration file ("config" by default).
- `-d/--directory <name>`       Sets directory for saving bitmaps and configuration (CWD by default)
- `-f/--filename <name>`        Sets name/prefix for bitmap files ("bitmap" by default).
- `-g/--granularity N`          Sets network mask (granularity) (/32 for IPv4 by default).
- `-r/--range <first>,<last>`   Sets first and last considered IP address as a string (the whole IPv4 address space by default).
- `-t/--time_interval N`        Sets time unit in seconds (300 seconds by default).
- `-w/--time_window N`          Sets time window of stored data (100 intervals by default).

### Common TRAP parameters
- `-h [trap,1]`      Print help message for this module / for libtrap specific parameters.
- `-i IFC_SPEC`      Specification of interface types and their parameters.
- `-v`               Be verbose.
- `-vv`              Be more verbose.
- `-vvv`             Be even more verbose.

## Usage
`./ip_activity -i "t:localhost:12345" -g 24 -r "169.0.0.0,169.1.0.0" -f my_bitmap`

This command will start IP activity scanner, will distinguish between /24 networks in 169.0.0.0-169.1.0.0 range and will store bitmap in files starting with "my_bitmap".

# IP Activity - Web server

## Description
This program implements a web server modifying and visualising stored IP activity.

## Parameters
### Server specific parameters
- `-c/--config_file <name>`  Sets name/prefix for configuration file ("config" by default).
- `-d/--directory <name>`    Sets directory for saving bitmaps and configuration (CWD by default)
- `-f/--filename <name>`     Sets name/prefix for bitmap files ("bitmap" by default).
- `-H/--hostname <hostname>` Sets hostname of the server (localhost by default).
- `-p/--port N`              Sets server port (8080 by default).

### Common parameters
- `-h/--help`              Print help message for the server created by argparse.

### Usage
`python[3] http_server.py -f my_bitmap -p 9999`
