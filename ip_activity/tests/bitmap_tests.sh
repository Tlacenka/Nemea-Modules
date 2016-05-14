#!/bin/bash

# Subject: IP Activity - Testing bitmap writing and reading
# Author:  Katerina Pilatova
# Date:    2016

green=$(tput setaf 2)
yellow=$(tput setaf 3)
red=$(tput setaf 1)
magenta=$(tput setaf 5)
bold=`tput bold`
normal=$(tput sgr0)

g++ -std=c++0x bitmap_writer.cpp ../ip_activity.hpp ../backend_functions.cpp \
               -o bitmap_writer -lyaml-cpp

printf "${bold}${magenta}Testing bitmap_write${normal}\n"

printf "${bold}Test 1: writing 10 rows of 16x'1':${normal}\n"
./bitmap_writer -t 1

xxd -b -c 2 test1.bmap 

printf "${bold}Test 2: writing 10 rows of 95x'1' + padding 1x'0':${normal}\n"
./bitmap_writer -t 2

xxd -b -c 6 test2.bmap 

printf "${bold}Test 3: writing 5 rows of 9x'1' + padding 7x'0':${normal}\n"
./bitmap_writer -t 3

xxd -b -c 2 test3.bmap 

rm *.bmap
