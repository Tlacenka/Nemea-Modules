# ip_activity module - README

## Description
This module scans traffic and stores IP activity to the dedicated bitmap.

## Interfaces
- Input: 1, UniRec flow
- Output: 0, bitmap file.

## Parameters
### Module specific parameters
- `-t/--time_interval N`    Sets time unit (5 minutes by default).
- `-V/--ip_version N`       Sets scanned IP version (4 by default). (probably to be removed)
- `-p/--print`              Prints progress every interval.
- `-g/--granularity`        Sets network mask (granularity) (/32 for IPv4, /128 for IPv6 by default).
- `-r/--range`              Sets first,last considered IP address (the whole address space by default).
- `-f/--filename`           Sets name/prefix for bitmap files ("bitmap" by default).

### Common TRAP parameters
- `-h [trap,1]`      Print help message for this module / for libtrap specific parameters.
- `-i IFC_SPEC`      Specification of interface types and their parameters.
- `-v`               Be verbose.
- `-vv`              Be more verbose.
- `-vvv`             Be even more verbose.

## Usage
`./ip_activity -i "t:localhost:12345" -g 24 -r "169.0.0.0,169.1.0.0" -f my_bitmap`

This command will start IP activity scanner, will distinguish between /24 networks in 169.0.0.0-169.1.0.0 range and will store bitmap in files starting with "my_bitmap".
