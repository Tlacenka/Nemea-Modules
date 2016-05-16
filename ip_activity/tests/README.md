# Tests - README

## Description
The test suite consists of test checking parameters for both backend and
the web server, writing/reading the configuration file and writing/reading
the bitmap file.

## Test Files
- `./backend_tests.sh` Runs tests checking validity of backend parameters.
- `./server_tests.sh`  Runs tests checking validity of server parameters.
- `./config_tests.sh`  Runs tests checking writing and reading confuration files.
- `./bitmap_tests.sh`  Runs tests checking writing and reading bitmap files.

## Running Tests
In order to run all tests, execute `./run_tests.sh`
To run only one type of tests, execute dedicated test file:
   - `./backend_tests.sh`
   - `./server_tests.sh`
   - `./config_tests.sh`
   - `./bitmap_tests.sh`
   

## Parameters
- `-v`  Runs tests in verbose mode, prints stdout/stderr of tested programs.
