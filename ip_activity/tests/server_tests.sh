#!/bin/bash

# Subject: IP Activity - Tests for web server
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

cd $DIR

# Parameters tests
# python 2.x
TEST201=("Testing parameter -p < 1" "python http_server.py -p -1" 1)
TEST202=("Testing parameter -p > 65535" "python http_server.py -p 100000" 1)
TEST203=("Testing parameter -d with non-existing filepath" "python http_server.py -d /whatever/somethingelse" 1)
TEST204=("Testing parameter -d with non-existing firpath" "python http_server.py -d /whatever/somethingelse.smth" 1)
TEST205=("Testing parameter -c with non-existing path" "python http_server.py -c /whatever/smthelse.yaml" 1)
TEST206=("Testing parameter -f beginning with a digit" "python http_server.py -f 12file" 1)
TEST207=("Testing parameter -f beginning with _" "python http_server.py -f _my_file" 1)
TEST208=("Testing parameter -f containing invalid char" "python http_server.py -f bitmap_file#name?" 1)


TESTS2=("${TEST201[@]}" "${TEST202[@]}" "${TEST203[@]}" "${TEST204[@]}" "${TEST205[@]}" "${TEST206[@]}")
TESTS2+=("${TEST207[@]}" "${TEST208[@]}")

TESTS2_NR=`expr ${#TESTS2[@]} / $ELEMENTS`

# Python 3.x
TEST301=("Testing parameter -p < 1" "python3 http_server.py -p -24" 1)
TEST302=("Testing parameter -p > 65535" "python3 http_server.py -p 121121" 1)
TEST303=("Testing parameter -d with non-existing filepath" "python3 http_server.py -d ./whatever/somethingelse" 1)
TEST304=("Testing parameter -d with non-existing dirpath" "python3 http_server.py -d ./whatever/somethingelse.smth" 1)
TEST305=("Testing parameter -c with non-existing path" "python3 http_server.py -c ./whatever/smthelse.yaml" 1)
TEST306=("Testing parameter -f beginning with a digit" "python3 http_server.py -f 42answer" 1)
TEST307=("Testing parameter -f beginning with _" "python3 http_server.py -f _-filename-" 1)
TEST308=("Testing parameter -f containing invalid char" "python3 http_server.py -f bitmap_file&name^" 1)

TESTS3=("${TEST301[@]}" "${TEST302[@]}" "${TEST303[@]}" "${TEST304[@]}" "${TEST305[@]}" "${TEST306[@]}")
TESTS3+=("${TEST307[@]}" "${TEST308[@]}")

TESTS3_NR=`expr ${#TESTS3[@]} / $ELEMENTS`

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
   fi
   
   # Print error if verbose
   if [ "$VERBOSE" = true ]
   then
      printf "${yellow}`cat $DIR/$ERR_FILE` ${normal}\n"
   fi

}

# Main

if [[ "$1" = "-v" ]]
then
   VERBOSE=true
fi

printf "${bold}${magenta}Running web server tests${normal}\n"
printf "${bold}${magenta}Testing python 2.x${normal}\n"
for T in $(seq 0 $((TESTS2_NR - 1 )))
do
   run_test "${TESTS2[@]:$(( T * ELEMENTS )):$ELEMENTS}"

done

printf "\n${bold}${magenta}Testing python 3.x${normal}\n"

for T in $(seq 0 $((TESTS3_NR - 1 )))
do
   run_test "${TESTS3[@]:$(( T * ELEMENTS )):$ELEMENTS}"

done

if [[ -e $DIR/$ERR_FILE ]] && [[ -e $DIR/$OUT_FILE ]]
then
   rm $DIR/$ERR_FILE
   rm $DIR/$OUT_FILE
fi

exit

# kill -9 `pidof lt-ip_activity`

