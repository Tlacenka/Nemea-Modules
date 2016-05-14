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

# Additional variables
DIR=.
RETURN=
VERBOSE=false
ERR_FILE=tmp.err
OUT_FILE=tmp.out
CONFIG_FILE=config_test.yaml

# Tests
ELEMENTS=7
TESTS=()

# Trap tests
TEST01=("Writing 10 rows of 16x'1'" "$DIR/bitmap_writer -t 1" 0 2 "test1.bmap" "$DIR/bitmap_reader.py -t 1" 0)
TEST02=("Writing 10 rows of 95x'1' + padding 1x'0'" "$DIR/bitmap_writer -t 2" 0 6 "test2.bmap" "$DIR/bitmap_reader.py -t 2" 0)
TEST03=("Writing 5 rows of 9x'1' + padding 7x'0'" "$DIR/bitmap_writer -t 3" 0 2 "test3.bmap" "$DIR/bitmap_reader.py -t 3" 0)
TEST04=("Writing 8 rows of 6x'01' + padding 4x'0'" "$DIR/bitmap_writer -t 4" 0 2 "test4.bmap" "$DIR/bitmap_reader.py -t 4" 0)
TEST04=("Writing 10 rows of 8x'1' + 8x'0'" "$DIR/bitmap_writer -t 5" 0 2 "test5.bmap" "$DIR/bitmap_reader.py -t 5" 0)

TESTS=("${TEST01[@]}" "${TEST02[@]}" "${TEST03[@]}" "${TEST04[@]}")
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
        # Print error if verbose
      if [ "$VERBOSE" = true ]
      then
         printf "${yellow}`xxd -b -c ${4} $DIR/${5}` ${normal}\n"
      fi
   else
      printf "${red} FAIL (expected ${3}) ${normal}\n"
      if [ "$VERBOSE" = true ]
      then
         printf "${yellow}`cat $DIR/$ERR_FILE` ${normal}\n"
      fi
   fi

   # Run reader
   ${6} 2> $DIR/$ERR_FILE > $DIR/$OUT_FILE
   RETURN="$?"

   # Print output
   printf "${bold}%-50s${normal}" "${1} shifted by 3 - reader:"
   if [ "$RETURN" = "${7}" ]
   then
       printf "${green} PASS${normal}\n"
       # Print stdout if verbose
       if [ "$VERBOSE" = true ]
       then
          printf "${yellow}`cat $DIR/$OUT_FILE | tr -d bittarray\(\' | tr -d \)\'` ${normal}\n"
       fi
   else
      printf "${red} FAIL (expected ${7}) ${normal}\n"
      # Print error if verbose
      if [ "$VERBOSE" = true ]
      then
         printf "${yellow}`cat $DIR/$ERR_FILE` ${normal}\n"
      fi
   fi

   if [[ -e "${5}" ]]
   then
      rm "${5}"
   fi

}

# Main
if [[ "$1" = "-v" ]]
then
   VERBOSE=true
fi

g++ -std=c++0x bitmap_writer.cpp ../ip_activity.hpp ../backend_functions.cpp \
               -o bitmap_writer -lyaml-cpp

printf "${bold}${magenta}Running bitmap tests${normal}\n"

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
