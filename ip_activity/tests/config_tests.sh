#!/bin/bash

# Subject: IP Activity - Testing configuration file writing and reading
# Author:  Katerina Pilatova
# Date:    2016

green=$(tput setaf 2)
yellow=$(tput setaf 3)
red=$(tput setaf 1)
magenta=$(tput setaf 5)
bold=`tput bold`
normal=$(tput sgr0)

g++ -std=c++0x config_writer.cpp ../ip_activity.hpp ../backend_functions.cpp \
               -o config_writer -lyaml-cpp

printf "${bold}${magenta}Testing config_write${normal}\n"

printf "${bold}Test 1: writing a simple node:${normal}\n"
./config_writer -t 1

cat config_test.yaml
printf "\n"
rm config_test.yaml

printf "${bold}Test 2: writing a node containing current time:${normal}\n"
./config_writer -t 2

cat config_test.yaml
printf "\n"
rm config_test.yaml

printf "${bold}Test 3: writing nested node:${normal}\n"
./config_writer -t 3

cat config_test.yaml
printf "\n"
rm config_test.yaml

printf "${bold}Test 4: writing valid configuration (offline)${normal}\n"
./config_writer -t 4

cat config_test.yaml
printf "\n"

printf "${bold}Test 5: writing valid configuration (online)${normal}\n"
./config_writer -t 5

cat config_test.yaml
printf "\n"

printf "${bold}Test 6: writing invalid configuration${normal}\n"
./config_writer -t 6

cat config_test.yaml
printf "\n"

rm config_test.yaml
