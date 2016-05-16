# IP Activity System Requirements
In order to be able to use the system, the following packages have to be installed.

## Backend Packages (C++)
- `yaml-cpp-0.5.3`        C++ Library for manipulating with YAML files. The package version has to be **0.5.3**.
- `Boost`                 C++ Boost libraries are used by the **yaml-cpp** package.

If `yaml-cpp` package is not available, you can build it yourself [here](https://github.com/jbeder/yaml-cpp/releases/tag/release-0.5.3)

## Server Packages (Python 2.x and/or 3.x)
- `[beautifulsoup4](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)` Used for HTML file modification.
- `bitarray`       Uses bit arrays for manipulating binary data from the storage.
- `ipaddress`      Used for wodking with IP addresses in a convenient way.
- `pyyaml`         Package for manipulation with YAML files, such as the system's configuration file.
- `Pillow`         Fork of `PIL`, used for creating images from bitmaps.

You can install these packages automatically by executing the `install_dependencies.sh` script.

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
- `-r/--range <first>,<last>`   Sets first and last considered IP address (the whole IPv4 address space by default).
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
