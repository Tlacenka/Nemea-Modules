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
DIR=..
RETURN=
VERBOSE=false
ERR_FILE=tmp.err
OUT_FILE=tmp.out

# Tests
ELEMENTS=3
TESTS=()

# Trap tests
TEST01=("Omitting -i parameter" "$DIR/ip_activity -w whatever" 1)
TEST02=("Testing wrong IFC_SPEC" "$DIR/ip_activity -i tt:12345" 1)
TEST03=("Using wrong parameters" "$DIR/ip_activity -i t:12345 -z whatever" 1)

# Parameters tests
TEST04=("Testing parameter -t < 0" "$DIR/ip_activity -i t:12345 -t -12" 1)
TEST05=("Testing parameter -t > 1000" "$DIR/ip_activity -i t:12345 -t 120000" 1)
TEST06=("Testing parameter -w < 0" "$DIR/ip_activity -i t:12345 -w -1" 1)
TEST07=("Testing parameter -w > 1000" "$DIR/ip_activity -i t:12345 -w 5000" 1)
TEST08=("Testing parameter -c with non-existing path" "$DIR/ip_activity -i t:12345 -c /whatever/smthelse.yaml" 1)
TEST09=("Testing parameter -g < 0" "$DIR/ip_activity -i t:12345 -g -42" 1)
TEST10=("Testing parameter -g > 32 with IPv4" "$DIR/ip_activity -i t:12345 -g 56" 1)
TEST11=("Testing parameter -g > 128 with IPv6" "$DIR/ip_activity -i t:12345 -r ff::,ffee:: -g 130" 1)
TEST12=("Testing parameter -r with random string" "$DIR/ip_activity -i t:12345 -r hello,goodbye" 1)
TEST13=("Testing parameter -r with one IPv4" "$DIR/ip_activity -i t:12345 -r 123.0.4.9" 1)
TEST14=("Testing parameter -r with one IPv6" "$DIR/ip_activity -i t:12345 -r faff:dfd2:2320::" 1)
TEST15=("Testing parameter -r with one IP + comma" "$DIR/ip_activity -i t:12345 -r ,123.0.4.9" 1)
TEST16=("Testing parameter -r with invalid IPv4" "$DIR/ip_activity -i t:12345 -r g.0.0.0,258.0.4.9" 1)
TEST17=("Testing parameter -r with invalid IPv6" "$DIR/ip_activity -i t:12345 -r ffaa::,haha::" 1)

TESTS=("${TEST01[@]}" "${TEST02[@]}" "${TEST03[@]}" "${TEST04[@]}" "${TEST05[@]}" "${TEST06[@]}")
TESTS+=("${TEST07[@]}" "${TEST08[@]}" "${TEST09[@]}" "${TEST10[@]}" "${TEST11[@]}" "${TEST12[@]}")
TESTS+=("${TEST13[@]}" "${TEST14[@]}" "${TEST15[@]}" "${TEST16[@]}" "${TEST17[@]}")

TESTS_NR=`expr ${#TESTS[@]} / $ELEMENTS`

# Run tests
function run_test() {

   # Run command
   ${2} 2> $DIR/$ERR_FILE > $DIR/$OUT_FILE
   RETURN="$?"

   # Print output
   printf "${bold}%-50s${normal}" "${1}:"
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

printf "${bold}${magenta}Running backend tests${normal}\n"

for T in $(seq 0 $((TESTS_NR - 1 )))
do
   run_test "${TESTS[@]:$(( T * ELEMENTS )):$ELEMENTS}"

done

if [[ -e $DIR/$ERR_FILE ]] && [[ -e $DIR/$OUT_FILE ]]
then
   rm $DIR/$ERR_FILE
   rm $DIR/$OUT_FILE
fi

if [[ -e config.yaml ]]
then
   rm config.yaml
fi

rm *.bmap

exit

# kill -9 `pidof lt-ip_activity`

