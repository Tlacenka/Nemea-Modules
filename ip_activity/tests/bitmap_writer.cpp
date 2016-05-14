
#include <getopt.h>
#include <inttypes.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#include <ctime>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>
#include <utility>

#include "yaml-cpp/yaml.h"
#include "../ip_activity.hpp"

void test3()
{
   // Truncate existing file
   std::fstream file;
   file.open("test3.bmap", std::ios_base::out | std::ios_base::trunc);

   std::ios_base::openmode mode = std::ios_base::binary | std::ios_base::out |
                                  std::ios_base::in;
   // Create vector
   std::vector<bool> bits(9);
   for (int i = 0; i < 9; i++) {
      bits[i] = 1;
   }
   
   // Write to file
   for (int i = 0; i < 5; i++) {
      binary_write("test3.bmap", bits, mode, i);
   }
   return;
}

/* Write 10 rows of 95x"1" + 1x"0" as padding*/
void test2()
{
   // Truncate existing file
   std::fstream file;
   file.open("test2.bmap", std::ios_base::out | std::ios_base::trunc);

   std::ios_base::openmode mode = std::ios_base::binary | std::ios_base::out |
                                  std::ios_base::in;
   // Create vector
   std::vector<bool> bits(95);
   for (int i = 0; i < 95; i++) {
      bits[i] = 1;
   }
   
   // Write to file
   for (int i = 0; i < 10; i++) {
      binary_write("test2.bmap", bits, mode, i);
   }
   return;
}

/* Writes 10 rows of 16x"1" */
void test1 ()
{
   // Truncate existing file
   std::fstream file;
   file.open("test1.bmap", std::ios_base::out | std::ios_base::trunc);

   std::ios_base::openmode mode = std::ios_base::binary | std::ios_base::out |
                                  std::ios_base::in;
   // Create vector
   std::vector<bool> bits(16);
   for (int i = 0; i < 16; i++) {
      bits[i] = 1;
   }

   // Write to file
   for (int i = 0; i < 10; i++) {
      binary_write("test1.bmap", bits, mode, i);
   }
   return;
}

int main(int argc, char** argv) {

   int test_nr = 0;

   // Parse arguments
   char opt;
   
   while ((opt = getopt(argc, argv, "t:")) != -1) {
      switch (opt) {
         case 't':
            test_nr = atoi(optarg);
            break;
         default:
            fprintf(stderr, "Error: Unknown parameter -%c.\n", opt);
            return 1;
      }
   }

   // Perform tests
   switch (test_nr) {
      case 1:
         test1();
         break;
      case 2:
         test2();
         break;
      case 3:
         test3();
         break;
      default:
         test1();
         test2();
         test3();
         break;
   }

   return 0;
}
