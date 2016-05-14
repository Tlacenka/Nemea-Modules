#!/bin/bash

# Subject: IP Activity - Tests
# Author:  Katerina Pilatova
# Date:    2016


./backend_tests.sh $1
printf "\n"
./server_tests.sh $1
printf "\n"
./bitmap_tests.sh $1

rm *.bmap
