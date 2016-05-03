#!/bin/bash

# Subject: IP Activity - Tests for backend
# Author:  Katerina Pilatova
# Date:    2016

# Colours
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

# Tests
TEST1=("Omitting -i parameter" "$DIR/ip_activity -w whatever" 1)
TEST2=("Using wrong parameters" "$DIR/ip_activity -i t:12345 -z whatever" 1)
TEST3=("Testing parameter -w < 0" "$DIR/ip_activity -i t:12345 -w -1" 1)
TEST4=("Testing parameter -w > 1000" "$DIR/ip_activity -i t:12345 -w 5000" 1)
TEST5=("Testing parameter -t < 0" "$DIR/ip_activity -i t:12345 -t -12" 1)
TEST6=("Testing parameter -t > 1000" "$DIR/ip_activity -i t:12345 -t 120000" 1)

TESTS=("${TEST1[@]}" "${TEST2[@]}" "${TEST3[@]}" "${TEST4[@]}" "${TEST5[@]}" "${TEST6[@]}")
ELEMENTS=3

TESTS_NR=`expr ${#TESTS[@]} / $ELEMENTS`

# Run tests
function run_test() {

   # Run command
   ${2} 2> $DIR/$ERR_FILE > $DIR/$OUT_FILE
   RETURN="$?"

   # Print output
   printf "${bold}%-30s${normal}" "${1}:"
   if [ "$RETURN" = "${3}" ]
   then
       printf "${green} PASS${normal}\n"
   else
      printf "${red} FAIL (expected ${3}) ${normal}\n"

      # Print error if verbose
      if [ "$VERBOSE" = true ]
      then
         printf "${yellow}`cat $DIR/$ERR_FILE` ${normal}\n"
      fi
   fi

}

# Main

if [[ "$1" = "-v" ]]
then
   VERBOSE=true
fi

for T in $(seq 0 $((TESTS_NR - 1 )))
do
   run_test "${TESTS[@]:$(( T * ELEMENTS )):$ELEMENTS}"

done

if [[ -e $DIR/$ERR_FILE ]] && [[ -e $DIR/$OUT_FILE ]]
then
   rm $DIR/$ERR_FILE
   rm $DIR/$OUT_FILE
fi

exit

# Missing -i option

