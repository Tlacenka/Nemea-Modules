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
ELEMENTS=3
TESTS=()

cd $DIR

# Parameters tests
# python 2.x
TEST01=("Testing parameter -p < 1" "python http_server.py -p -1" 1)
TEST02=("Testing parameter -p > 65535" "python http_server.py -p 100000" 1)
TEST03=("Testing parameter -d with non-existing filepath" "python http_server.py -d /whatever/somethingelse" 1)
TEST04=("Testing parameter -d with non-existing firpath" "python http_server.py -d /whatever/somethingelse.smth" 1)
TEST05=("Testing parameter -c with non-existing path" "python http_server.py -c /whatever/smthelse.yaml" 1)
TEST06=("Testing parameter -H with non-existing hostname" "python http_server.py -H mynonexistinghostnamepython2123456" 1)
TEST07=("Testing parameter -f beginning with a digit" "python http_server.py -f 12file" 1)
TEST08=("Testing parameter -f beginning with _" "python http_server.py -f _my_file" 1)
TEST09=("Testing parameter -f containing invalid char" "python http_server.py -f bitmap_file#name?" 1)


TESTS2=("${TEST01[@]}" "${TEST02[@]}" "${TEST03[@]}" "${TEST04[@]}" "${TEST05[@]}" "${TEST06[@]}")
TESTS2+=("${TEST07[@]}" "${TEST08[@]}" "${TEST09[@]}")

TESTS2_NR=`expr ${#TESTS2[@]} / $ELEMENTS`

# Python 3.x
TEST01=("Testing parameter -p < 1" "python3 http_server.py -p -24" 1)
TEST02=("Testing parameter -p > 65535" "python3 http_server.py -p 121121" 1)
TEST03=("Testing parameter -d with non-existing filepath" "python3 http_server.py -d ./whatever/somethingelse" 1)
TEST04=("Testing parameter -d with non-existing dirpath" "python3 http_server.py -d ./whatever/somethingelse.smth" 1)
TEST05=("Testing parameter -c with non-existing path" "python3 http_server.py -c ./whatever/smthelse.yaml" 1)
TEST06=("Testing parameter -H with non-existing hostname" "python3 http_server.py -H mynonexistinghostnamepython3123456" 1)
TEST07=("Testing parameter -f beginning with a digit" "python3 http_server.py -f 42answer" 1)
TEST08=("Testing parameter -f beginning with _" "python3 http_server.py -f _-filename-" 1)
TEST09=("Testing parameter -f containing invalid char" "python3 http_server.py -f bitmap_file&name^" 1)

TESTS3=("${TEST01[@]}" "${TEST02[@]}" "${TEST03[@]}" "${TEST04[@]}" "${TEST05[@]}" "${TEST06[@]}")
TESTS3+=("${TEST07[@]}" "${TEST08[@]}" "${TEST09[@]}")

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

printf "Testing python 2.x\n"
for T in $(seq 0 $((TESTS2_NR - 1 )))
do
   run_test "${TESTS2[@]:$(( T * ELEMENTS )):$ELEMENTS}"

done

printf "\nTesting python 3.x\n"

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

