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

# Additional variables
DIR=.
RETURN=
VERBOSE=false
ERR_FILE=tmp.err
OUT_FILE=tmp.out
CONFIG_FILE=config_test.yaml

# Tests
ELEMENTS=5
TESTS=()

# Trap tests
TEST01=("Writing a simple node" "$DIR/config_writer -t 1" 0 "$DIR/config_reader.py -t 1" 1)
TEST02=("Writing a node containing current time" "$DIR/config_writer -t 2" 0 "$DIR/config_reader.py -t 2" 1)
TEST03=("Writing a nested node" "$DIR/config_writer -t 3" 0 "$DIR/config_reader.py -t 3" 1)
TEST04=("Writing a valid configuration (offline)" "$DIR/config_writer -t 4" 0 "$DIR/config_reader.py -t 4" 0)
TEST05=("Writing a valid configuration (online)" "$DIR/config_writer -t 5" 0 "$DIR/config_reader.py -t 5" 0)
TEST06=("Writing an invalid configuration" "$DIR/config_writer -t 6" 0 "$DIR/config_reader.py -t 6" 1)


TESTS=("${TEST01[@]}" "${TEST02[@]}" "${TEST03[@]}" "${TEST04[@]}" "${TEST05[@]}" "${TEST06[@]}")
TESTS_NR=`expr ${#TESTS[@]} / $ELEMENTS`

# Run tests
function run_test() {

   # Run writer
   ${2} 2> $DIR/$ERR_FILE > $DIR/$OUT_FILE
   RETURN="$?"

   # Print output
   printf "${bold}%-50s${normal}" "${1} - writer:"
   if [ "$RETURN" = "${3}" ]
   then
       printf "${green} PASS${normal}\n"
      if [ "$VERBOSE" = true ]
      then
         printf "${yellow}`cat $DIR/$CONFIG_FILE` ${normal}\n"
      fi
   else
      printf "${red} FAIL (expected ${3}) ${normal}\n"
      # Print error if verbose
      if [ "$VERBOSE" = true ]
      then
         printf "${yellow}`cat $DIR/$ERR_FILE` ${normal}\n"
      fi
   fi

   # Run reader
   ${4} 2> $DIR/$ERR_FILE > $DIR/$OUT_FILE
   RETURN="$?"

   # Print output
   printf "${bold}%-50s${normal}" "${1} - reader:"
   if [ "$RETURN" = "${5}" ]
   then
       printf "${green} PASS${normal}\n"
   else
      printf "${red} FAIL (expected ${5}) ${normal}\n"
      # Print error if verbose
      if [ "$VERBOSE" = true ]
      then
         printf "${yellow}`cat $DIR/$ERR_FILE` ${normal}\n"
      fi
   fi

   if [[ -e config_test.yaml ]]
   then
      rm config_test.yaml
   fi

}

# Main
if [[ "$1" = "-v" ]]
then
   VERBOSE=true
fi

g++ -std=c++0x config_writer.cpp ../ip_activity.hpp ../backend_functions.cpp \
               -o config_writer -lyaml-cpp

printf "${bold}${magenta}Running configuration tests${normal}\n"

for T in $(seq 0 $((TESTS_NR - 1 )))
do
   run_test "${TESTS[@]:$(( T * ELEMENTS )):$ELEMENTS}"

done

if [[ -e $DIR/$ERR_FILE ]] && [[ -e $DIR/$OUT_FILE ]]
then
   rm $DIR/$ERR_FILE
   rm $DIR/$OUT_FILE
fi

if [[ -e config_test.yaml ]]
then
   rm config_test.yaml
fi

exit
